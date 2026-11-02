"""Backend-local request/response boundary for browser voice input."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Mapping, Protocol, Sequence
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VoiceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


MAX_TRANSCRIPT_CHARS = 16000
MAX_AUDIO_BYTES = 5 * 1024 * 1024


class VoiceTranscriptRequest(VoiceModel):
    transcript: str = Field(min_length=1, max_length=MAX_TRANSCRIPT_CHARS)
    clarification_of: UUID | None = None


class VoiceAudioRequest(VoiceModel):
    audio_base64: str = Field(min_length=1, max_length=MAX_AUDIO_BYTES * 2)
    media_type: str = Field(default="audio/webm", min_length=3, max_length=80)


class VoiceIntent(VoiceModel):
    action: str = Field(min_length=1, max_length=40)
    item: str | None = Field(default=None, max_length=120)
    quantity: int | None = Field(default=None, gt=0)
    price_override_minor: int | None = Field(default=None, ge=0)
    needs_confirmation: bool = True


class VoiceSaleLine(VoiceModel):
    product_id: UUID
    product_name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(gt=0)


class VoicePendingItem(VoiceModel):
    slot_id: int = Field(ge=0, lt=100)
    heard: str = Field(max_length=500)
    quantity: int | None = Field(default=None, ge=0)
    product_id: UUID | None = None
    product_name: str | None = None
    product_sku: str | None = None


class VoiceResponse(VoiceModel):
    request_id: UUID
    shop_id: UUID
    input_kind: str
    status: str
    transcript: str | None = None
    intent: VoiceIntent | None = None
    lines: list[VoiceSaleLine] = Field(default_factory=list, max_length=100)
    error: str | None = None
    error_code: str | None = None
    requires_match_confirmation: bool = False
    clarification_question: str | None = Field(default=None, max_length=1000)
    resolution_source: str | None = None
    provider_called: bool = False
    clarification_code: str | None = None
    clarification_product_id: UUID | None = None
    clarification_product_name: str | None = None
    clarification_product_sku: str | None = None
    retained_lines: list[VoiceSaleLine] = Field(default_factory=list, max_length=100)
    pending_items: list[VoicePendingItem] = Field(default_factory=list, max_length=100)


class VoiceSaleCommitLine(VoiceModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class VoiceSaleCommitRequest(VoiceModel):
    review_id: UUID
    lines: list[VoiceSaleCommitLine] = Field(min_length=1)
    tender: str | None = Field(default=None, max_length=32)
    amount_received_cents: int | None = Field(default=None, ge=0)
    match_confirmed: bool = Field(default=False, strict=True)

    @field_validator("tender")
    @classmethod
    def normalize_tender(cls, value: str | None) -> str | None:
        return value.strip().lower() if value is not None else None


class VoiceTenderQuestion(VoiceModel):
    status: Literal["needs_tender"] = "needs_tender"
    review_id: UUID
    question: str
    allowed_tenders: list[Literal["cash", "bank"]] = ["cash", "bank"]
    amount_due_cents: int = Field(ge=0)
    missing: list[str] = Field(default_factory=list)


class VoiceSaleUndoRequest(VoiceModel):
    actor: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=1, max_length=240)
    confirmed: bool = False

    @field_validator("actor", "reason")
    @classmethod
    def strip_undo_text(cls, value: str) -> str:
        return value.strip()


class VoiceSaleReversal(VoiceModel):
    reversal_id: UUID
    audit_id: UUID
    original_sale_id: UUID
    shop_id: UUID
    status: Literal["reversed"] = "reversed"
    lines: list[VoiceSaleCommitLine]
    actor: str
    reason: str
    created_at: datetime


class TranscriptInterpreter(Protocol):
    def interpret(self, text: str) -> Any: ...


@dataclass(frozen=True)
class VoiceRequestFingerprint:
    value: str


def request_fingerprint(input_kind: str, payload: Mapping[str, Any]) -> VoiceRequestFingerprint:
    canonical = json.dumps({"input_kind": input_kind, **payload}, sort_keys=True, separators=(",", ":"))
    return VoiceRequestFingerprint(hashlib.sha256(canonical.encode("utf-8")).hexdigest())


def decode_audio(request: VoiceAudioRequest) -> bytes:
    try:
        decoded = base64.b64decode(request.audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("audio_base64 must be valid base64") from exc
    if not decoded:
        raise ValueError("audio payload must not be empty")
    if len(decoded) > MAX_AUDIO_BYTES:
        raise ValueError("audio payload exceeds 5 MiB")
    return decoded


def normalize_intent(raw: Any) -> VoiceIntent:
    """Copy only the bounded intent fields; never return provider objects/raw JSON."""

    action = getattr(raw, "action", None)
    item = getattr(raw, "item", None)
    quantity = getattr(raw, "quantity", None)
    price = getattr(raw, "price_override_minor", None)
    confirmation = getattr(raw, "needs_confirmation", True)
    if not isinstance(action, str) or action not in {"record_sale", "check_stock", "check_cash", "cancel", "unknown"}:
        raise ValueError("unsupported voice action")
    if item is not None and not isinstance(item, str):
        raise ValueError("invalid voice item")
    if quantity is not None and (isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0):
        raise ValueError("invalid voice quantity")
    if price is not None and (isinstance(price, bool) or not isinstance(price, int) or price < 0):
        raise ValueError("invalid voice price override")
    if not isinstance(confirmation, bool):
        raise ValueError("invalid confirmation flag")
    return VoiceIntent(action=action, item=item, quantity=quantity, price_override_minor=price, needs_confirmation=True)


def parse_quantity_reply(transcript: str) -> int | None:
    """A bare explicit positive whole quantity, never an inferred default."""
    text = re.sub(r"[.!?]+$", "", transcript.strip().lower()).strip()
    words = {word: number for number, word in enumerate(("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"))}
    quantity = words.get(text)
    if quantity is None and re.fullmatch(r"[1-9]\d{0,3}", text):
        quantity = int(text)
    return quantity if quantity is not None and quantity > 0 else None


def parse_catalogue_sale(transcript: str, products: Sequence[Any]) -> list[VoiceSaleLine] | None:
    """Parse a bounded multi-item typed command using only shop catalogue facts.

    This is deliberately narrow: it accepts one or more quantity-plus-token
    pairs such as ``2 coke 2 sugar`` and never invents a product or price.
    """

    words = {word: str(index) for index, word in enumerate(("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"))}
    text = transcript.strip().lower()
    if text.startswith("apo "):
        text = text[4:].strip()
        text = re.sub(r"\s+(?:apo|napo)$", "", text).strip()
    text = re.sub(r"^(?:sell|record sale|sale)\s+", "", text)
    text = re.sub(r"\b(" + "|".join(words) + r")\b", lambda match: words[match.group()], text)
    starts = list(re.finditer(r"(?:^|\s)(\d{1,4})\s+", text))
    if not starts or starts[0].start() != 0:
        return None
    pairs = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        token = text[match.end():end].strip()
        token = re.sub(r"(?:\s+and|[,;])+$", "", token).strip()
        if not token or int(match.group(1)) <= 0:
            return None
        pairs.append((match.group(1), token))
    if len(pairs) > 100:
        return None
    lines: list[VoiceSaleLine] = []
    used: set[UUID] = set()
    for quantity_text, token in pairs:
        quantity = int(quantity_text)
        normalized_token = re.sub(r"[^a-z0-9]", "", token.lower())
        matches = []
        for product in products:
            name = str(getattr(product, "name", ""))
            sku = str(getattr(product, "sku", ""))
            aliases = {
                re.sub(r"[^a-z0-9]", "", value.lower())
                for value in (
                    name,
                    re.sub(r"\s+\d+(?:[a-z]+)?$", "", name, flags=re.IGNORECASE),
                    sku,
                    *re.findall(r"[A-Za-z0-9]+", f"{name} {sku}"),
                )
            }
            if name.lower().startswith("coca-cola"):
                aliases.add("coke")
            if normalized_token in aliases:
                matches.append(product)
        if len(matches) != 1:
            return None
        product = matches[0]
        product_id = getattr(product, "id", None)
        if not isinstance(product_id, UUID) or product_id in used:
            return None
        used.add(product_id)
        lines.append(VoiceSaleLine(product_id=product_id, product_name=str(product.name), quantity=quantity))
    return lines


def audio_fingerprint(request: VoiceAudioRequest, decoded: bytes) -> VoiceRequestFingerprint:
    return request_fingerprint("audio", {"media_type": request.media_type.strip().lower(), "sha256": hashlib.sha256(decoded).hexdigest()})
