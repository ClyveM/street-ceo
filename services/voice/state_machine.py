"""Foreground Apo/Napo interaction state machine.

This module deliberately knows neither an audio provider nor an HTTP client.
Callers supply an interpreter, catalog resolver, and sale gateway implementing
the small protocols below.  The only mutating action is a confirmed sale
submitted through the documented API request shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Mapping, Optional, Protocol, Sequence
from uuid import UUID, uuid4


class SessionState(str, Enum):
    READY = "ready"
    APO = "apo"
    ITEM_CAPTURE = "item_capture"
    NAPO = "napo"
    QUOTE = "quote"
    PAYMENT = "payment"
    VALIDATING = "validating"
    COMMITTED = "committed"
    FAILURE = "failure"


class InputMode(str, Enum):
    FOREGROUND = "foreground"
    PUSH_TO_TALK = "push_to_talk"
    TEXT = "text"


class SaleMode(str, Enum):
    """How a validated voice basket is finalized."""

    REVIEW = "review"
    QUICK = "quick"


@dataclass(frozen=True)
class CatalogItem:
    product_id: UUID
    name: str
    unit_price_minor: int
    stock_qty: int


@dataclass(frozen=True)
class BasketLine:
    item: CatalogItem
    quantity: int

    @property
    def total_minor(self) -> int:
        return self.item.unit_price_minor * self.quantity


@dataclass(frozen=True)
class CommandIntent:
    """Provider-independent interpretation supplied by a speech/text adapter."""

    action: str
    item: Optional[str] = None
    quantity: Optional[int] = None
    tender: Optional[str] = None


@dataclass(frozen=True)
class VoiceEvent:
    state: SessionState
    message: str
    basket: tuple[BasketLine, ...] = ()
    sale_id: Optional[UUID] = None
    retryable: bool = False
    receipt: Optional[Mapping[str, object]] = None
    spoken: Optional[str] = None


class Interpreter(Protocol):
    def interpret(self, text: str) -> CommandIntent: ...


class CatalogResolver(Protocol):
    def resolve(self, item: str) -> Sequence[CatalogItem]: ...


class SaleGateway(Protocol):
    def create_sale(
        self,
        shop_id: UUID,
        lines: Sequence[Mapping[str, object]],
        tender: str,
        idempotency_key: str,
        *,
        amount_received_cents: Optional[int] = None,
    ) -> Mapping[str, object]: ...


class UndoSaleGateway(Protocol):
    def undo_sale(self, shop_id: UUID, sale_id: UUID, idempotency_key: str) -> Mapping[str, object]: ...


class VoiceInputError(ValueError):
    pass


class VoiceSession:
    """A foreground session. One instance represents one vendor interaction."""

    def __init__(
        self,
        shop_id: UUID,
        interpreter: Interpreter,
        catalog: CatalogResolver,
        sales: SaleGateway,
        mode: SaleMode = SaleMode.REVIEW,
        default_tender: Optional[str] = None,
    ) -> None:
        self.shop_id = shop_id
        self.interpreter = interpreter
        self.catalog = catalog
        self.sales = sales
        self.mode = SaleMode(mode)
        self.default_tender = self._normalize_tender(default_tender) if default_tender else None
        self.state = SessionState.READY
        self.basket: list[BasketLine] = []
        self.tender: Optional[str] = None
        self._pending_intent: Optional[CommandIntent] = None
        self._retry_key: Optional[str] = None
        self._last_failure: Optional[str] = None
        self._last_sale_id: Optional[UUID] = None
        self._last_receipt: Optional[Mapping[str, object]] = None
        self._cash_received: Optional[int] = None

    def _event(self, message: str, retryable: bool = False) -> VoiceEvent:
        return VoiceEvent(
            self.state, message, tuple(self.basket), self._last_sale_id, retryable,
            self._last_receipt, message,
        )

    def _clear_cycle(self) -> None:
        self.state = SessionState.READY
        self.basket.clear()
        self.tender = None
        self._pending_intent = None
        self._retry_key = None
        self._last_failure = None
        self._last_sale_id = None
        self._last_receipt = None
        self._cash_received = None

    def wake(self, word: str = "Apo") -> VoiceEvent:
        if self._spoken_word(word) != "apo" or self.state not in (SessionState.READY, SessionState.COMMITTED, SessionState.FAILURE):
            return self._fail("Say Apo to start a new sale.")
        self._clear_cycle()
        self.state = SessionState.APO
        self.basket.clear()
        self.tender = None
        self._pending_intent = None
        self._retry_key = None
        self._last_failure = None
        self._last_sale_id = None
        return self._event("Apo heard. Tell me the item and quantity.")

    def capture(self, text: str) -> VoiceEvent:
        allowed_states = (SessionState.APO, SessionState.ITEM_CAPTURE)
        if self.mode == SaleMode.QUICK:
            allowed_states = (SessionState.APO, SessionState.ITEM_CAPTURE, SessionState.NAPO)
        if self.state not in allowed_states:
            return self._fail("I am not listening for an item.")
        if not text.strip():
            return self._fail("I did not hear an item. Repeat or cancel.")
        self.state = SessionState.ITEM_CAPTURE
        try:
            intent = self.interpreter.interpret(text)
        except Exception:
            return self._fail("I could not understand that. Repeat or cancel.")
        if intent.action == "cancel":
            return self.cancel()
        if intent.action != "record_sale" or not intent.item or isinstance(intent.quantity, bool) or not isinstance(intent.quantity, int) or intent.quantity <= 0:
            return self._fail("I need one item and a positive quantity. Repeat or cancel.")
        matches = tuple(self.catalog.resolve(intent.item))
        if len(matches) != 1:
            self._pending_intent = intent
            return self._fail("That item is ambiguous or unavailable. Clarify the item or cancel.")
        item = matches[0]
        if item.stock_qty < intent.quantity:
            self._pending_intent = intent
            return self._fail("There is not enough stock. Change the quantity or cancel.")
        if any(line.item.product_id == item.product_id for line in self.basket):
            return self._fail("That item was already added. Repeat with a different item or cancel.")
        self.basket.append(BasketLine(item, intent.quantity))
        self._pending_intent = None
        self.state = SessionState.NAPO
        return self._event("Item added. Say Apo when you are finished, or add another item.")

    def end(self, word: str = "Napo") -> VoiceEvent:
        spoken_word = self._spoken_word(word)
        if spoken_word not in {"apo", "napo"} or self.state != SessionState.NAPO:
            return self._fail("Finish the item with Apo.")
        if self.mode == SaleMode.QUICK and spoken_word == "apo":
            if self.default_tender:
                self.state = SessionState.PAYMENT
                self.tender = self.default_tender
                return self.payment(self.default_tender)
            self.state = SessionState.PAYMENT
            return self._event(self._tender_question())
        self.state = SessionState.QUOTE
        return self._event(self.quote())

    def quote(self) -> str:
        total = sum(line.total_minor for line in self.basket)
        if not self.basket:
            return "The basket is empty."
        names = ", ".join(f"{line.quantity} x {line.item.name}" for line in self.basket)
        return f"{names}; total {total} minor units. Confirm and say cash or bank."

    def confirm(self, confirmed: bool) -> VoiceEvent:
        if self.state != SessionState.QUOTE:
            return self._fail("There is no quote to confirm.")
        if not confirmed:
            return self.cancel()
        self.state = SessionState.PAYMENT
        return self._event("Which tender: cash or bank?")

    def payment(self, tender: str, amount_minor: Optional[int] = None) -> VoiceEvent:
        if self.state != SessionState.PAYMENT:
            return self._fail("Confirm the quote before choosing tender.")
        normalized, spoken_amount = self._parse_tender(tender)
        if amount_minor is None:
            amount_minor = spoken_amount
        if normalized not in {"cash", "bank"}:
            return self._ask_tender("I did not catch that. Please say cash or bank.")
        if amount_minor is not None and (isinstance(amount_minor, bool) or not isinstance(amount_minor, int) or amount_minor < 0):
            return self._ask_tender("Please say a whole cash amount, or say bank.")
        total = sum(line.total_minor for line in self.basket)
        if normalized == "cash" and amount_minor is None:
            self.tender = "cash"
            return self._ask_tender(f"How much cash did you receive? The total is {total} minor units.")
        if normalized == "bank" and amount_minor not in (None, total):
            return self._ask_tender("Bank payment must equal the sale total.")
        if normalized == "cash" and amount_minor is not None and amount_minor < total:
            return self._ask_tender(f"Your total is {total}. I need at least {total} cash, or say bank.")
        self.tender = normalized
        self._cash_received = amount_minor if normalized == "cash" else None
        return self.commit()

    def commit(self) -> VoiceEvent:
        if self.state != SessionState.PAYMENT or not self.basket or not self.tender:
            return self._fail("The sale is not ready to submit.")
        self.state = SessionState.VALIDATING
        if self._retry_key is None:
            self._retry_key = f"voice-{uuid4()}"
        lines = [{"product_id": line.item.product_id, "quantity": line.quantity} for line in self.basket]
        try:
            amount_args = {"amount_received_cents": self._cash_received} if self.tender == "cash" else {}
            response = self.sales.create_sale(self.shop_id, lines, self.tender, self._retry_key, **amount_args)
            if response.get("status") == "needs_tender":
                return self._ask_tender(str(response.get("question") or self._tender_question()))
            raw_id = response.get("id")
            if not raw_id or response.get("status") not in (None, "committed"):
                raise VoiceInputError("Gateway did not return a committed sale receipt")
            self._last_sale_id = UUID(str(raw_id))
            self._last_receipt = self._receipt(response)
        except Exception as exc:
            self._last_failure = type(exc).__name__
            self.state = SessionState.FAILURE
            return self._event("The sale was not posted. Your basket is preserved; retry or cancel.", True)
        self.state = SessionState.COMMITTED
        return self._event("Sale posted and confirmed.")

    def undo_last_sale(self) -> VoiceEvent:
        """Request a reversal through an explicitly supported gateway only."""

        if self.state != SessionState.COMMITTED or self._last_sale_id is None:
            return self._fail("There is no recent voice sale available to undo.")
        undo = getattr(self.sales, "undo_sale", None)
        if not callable(undo):
            return self._fail("Undo is not available until the reversal service is connected.")
        try:
            response = undo(self.shop_id, self._last_sale_id, f"undo-{self._last_sale_id}")
            if response.get("status") != "reversed":
                raise VoiceInputError("Reversal was not acknowledged")
        except Exception:
            return self._event("Undo is unconfirmed. Check sale history or retry undo with the same key.", retryable=True)
        sale_id = self._last_sale_id
        self._clear_cycle()
        return self._event(f"Sale {sale_id} was undone.")

    @staticmethod
    def _normalize_tender(tender: Optional[str]) -> str:
        normalized = (tender or "").strip().lower()
        if normalized not in {"cash", "bank"}:
            raise VoiceInputError("default tender must be cash or bank")
        return normalized

    @staticmethod
    def _parse_tender(value: str) -> tuple[str, Optional[int]]:
        match = re.fullmatch(r"(cash|bank)(?:[\s,]+(\d+))?", value.strip().lower().strip(".!?;:"))
        if not match:
            return value.strip().lower(), None
        return match.group(1), int(match.group(2)) if match.group(2) else None

    @staticmethod
    def _spoken_word(value: str) -> str:
        """Ignore terminal ASR punctuation around Apo/Napo wake words."""

        return value.strip().lower().strip(".!?;:")

    def _tender_question(self) -> str:
        total = sum(line.total_minor for line in self.basket)
        return f"Your total is {total}. Cash or Bank?"

    def _ask_tender(self, message: str) -> VoiceEvent:
        self.state = SessionState.PAYMENT
        return self._event(message, retryable=True)

    def _receipt(self, response: Mapping[str, object]) -> Mapping[str, object]:
        """Expose only bounded sale facts returned by the sale gateway."""

        return {
            "sale_id": str(self._last_sale_id) if self._last_sale_id else None,
            "tender": self.tender,
            "total_minor": response.get("total_minor", response.get("total_cents", sum(line.total_minor for line in self.basket))),
            "cash_received": response.get("amount_received_cents", self._cash_received) if self.tender == "cash" else None,
            "change_minor": response.get("change_cents", (
                self._cash_received - sum(line.total_minor for line in self.basket)
                if self.tender == "cash" and self._cash_received is not None
                else 0
            )),
            "lines": tuple(
                {"product_id": str(line.item.product_id), "name": line.item.name, "quantity": line.quantity}
                for line in self.basket
            ),
            "stock_after": response.get("stock_after"),
        }

    def retry(self) -> VoiceEvent:
        if self.state != SessionState.FAILURE or not self.basket or not self.tender:
            return self._fail("There is no safe sale retry available.")
        self.state = SessionState.PAYMENT
        return self.commit()

    def cancel(self) -> VoiceEvent:
        self._clear_cycle()
        return self._event("Cancelled. Nothing was posted.")

    def _fail(self, message: str) -> VoiceEvent:
        self.state = SessionState.FAILURE
        self._last_failure = message
        return self._event(message, False)

    def accept(self, mode: InputMode, event: str, text: str = "") -> VoiceEvent:
        """Map foreground, push-to-talk, and text fallback to the same flow."""
        if mode == InputMode.FOREGROUND:
            if event == "wake":
                return self.wake(text or "Apo")
            if event == "capture":
                return self.capture(text)
            if event == "end":
                return self.end(text or "Napo")
        elif mode == InputMode.PUSH_TO_TALK:
            if event == "press":
                return self.wake("Apo")
            if event == "release":
                if self.state == SessionState.APO:
                    return self.capture(text)
                return self.end("Napo")
        elif mode == InputMode.TEXT and event == "submit":
            started = self.wake("Apo") if self.state == SessionState.READY else self._event("Text command received.")
            if started.state == SessionState.APO:
                captured = self.capture(text)
                if captured.state == SessionState.NAPO:
                    return self.end("Napo")
                return captured
            return started
        return self._fail("Unsupported voice input event.")
