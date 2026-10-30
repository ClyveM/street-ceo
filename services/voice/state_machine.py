"""Foreground Apo/Napo interaction state machine.

This module deliberately knows neither an audio provider nor an HTTP client.
Callers supply an interpreter, catalog resolver, and sale gateway implementing
the small protocols below.  The only mutating action is a confirmed sale
submitted through the documented API request shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
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


@dataclass(frozen=True)
class VoiceEvent:
    state: SessionState
    message: str
    basket: tuple[BasketLine, ...] = ()
    sale_id: Optional[UUID] = None
    retryable: bool = False


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
    ) -> Mapping[str, object]: ...


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
    ) -> None:
        self.shop_id = shop_id
        self.interpreter = interpreter
        self.catalog = catalog
        self.sales = sales
        self.state = SessionState.READY
        self.basket: list[BasketLine] = []
        self.tender: Optional[str] = None
        self._pending_intent: Optional[CommandIntent] = None
        self._retry_key: Optional[str] = None
        self._last_failure: Optional[str] = None
        self._last_sale_id: Optional[UUID] = None

    def _event(self, message: str, retryable: bool = False) -> VoiceEvent:
        return VoiceEvent(self.state, message, tuple(self.basket), self._last_sale_id, retryable)

    def _clear_cycle(self) -> None:
        self.state = SessionState.READY
        self.basket.clear()
        self.tender = None
        self._pending_intent = None
        self._retry_key = None
        self._last_failure = None
        self._last_sale_id = None

    def wake(self, word: str = "Apo") -> VoiceEvent:
        if word.strip().lower() != "apo" or self.state not in (SessionState.READY, SessionState.COMMITTED, SessionState.FAILURE):
            return self._fail("Say Apo to start a new sale.")
        self.state = SessionState.APO
        self.basket.clear()
        self.tender = None
        self._pending_intent = None
        self._retry_key = None
        self._last_failure = None
        self._last_sale_id = None
        return self._event("Apo heard. Tell me the item and quantity.")

    def capture(self, text: str) -> VoiceEvent:
        if self.state not in (SessionState.APO, SessionState.ITEM_CAPTURE):
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
        if intent.action != "record_sale" or not intent.item or not isinstance(intent.quantity, int) or intent.quantity <= 0:
            return self._fail("I need one item and a positive quantity. Repeat or cancel.")
        matches = tuple(self.catalog.resolve(intent.item))
        if len(matches) != 1:
            self._pending_intent = intent
            return self._fail("That item is ambiguous or unavailable. Clarify the item or cancel.")
        item = matches[0]
        if item.stock_qty < intent.quantity:
            self._pending_intent = intent
            return self._fail("There is not enough stock. Change the quantity or cancel.")
        self.basket = [BasketLine(item, intent.quantity)]
        self._pending_intent = None
        self.state = SessionState.NAPO
        return self._event("Say Napo when you are finished.")

    def end(self, word: str = "Napo") -> VoiceEvent:
        if word.strip().lower() != "napo" or self.state != SessionState.NAPO:
            return self._fail("Finish the item with Napo.")
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
        normalized = tender.strip().lower()
        if normalized not in {"cash", "bank"}:
            return self._fail("Tender is required: say cash or bank.")
        if amount_minor is not None and (isinstance(amount_minor, bool) or not isinstance(amount_minor, int) or amount_minor < 0):
            return self._fail("Cash amount must be a non-negative whole number.")
        total = sum(line.total_minor for line in self.basket)
        if normalized == "cash" and amount_minor is not None and amount_minor < total:
            return self._fail("Cash is insufficient for this basket. Change the amount or cancel.")
        self.tender = normalized
        return self.commit()

    def commit(self) -> VoiceEvent:
        if self.state != SessionState.PAYMENT or not self.basket or not self.tender:
            return self._fail("The sale is not ready to submit.")
        self.state = SessionState.VALIDATING
        if self._retry_key is None:
            self._retry_key = f"voice-{uuid4()}"
        lines = [{"product_id": line.item.product_id, "quantity": line.quantity} for line in self.basket]
        try:
            response = self.sales.create_sale(self.shop_id, lines, self.tender, self._retry_key)
            raw_id = response.get("id")
            self._last_sale_id = UUID(str(raw_id)) if raw_id else None
        except Exception as exc:
            self._last_failure = type(exc).__name__
            self.state = SessionState.FAILURE
            return self._event("The sale was not posted. Your basket is preserved; retry or cancel.", True)
        self.state = SessionState.COMMITTED
        return self._event("Sale posted and confirmed.")

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
