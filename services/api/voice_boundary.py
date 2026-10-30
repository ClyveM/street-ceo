"""Backend-local request/response boundary for browser voice input."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class VoiceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


MAX_TRANSCRIPT_CHARS = 1000
MAX_AUDIO_BYTES = 5 * 1024 * 1024


class VoiceTranscriptRequest(VoiceModel):
    transcript: str = Field(min_length=1, max_length=MAX_TRANSCRIPT_CHARS)


class VoiceAudioRequest(VoiceModel):
    audio_base64: str = Field(min_length=1, max_length=MAX_AUDIO_BYTES * 2)
    media_type: str = Field(default="audio/webm", min_length=3, max_length=80)


class VoiceIntent(VoiceModel):
    action: str = Field(min_length=1, max_length=40)
    item: str | None = Field(default=None, max_length=120)
    quantity: int | None = Field(default=None, gt=0)
    price_override_minor: int | None = Field(default=None, ge=0)
    needs_confirmation: bool = True


class VoiceResponse(VoiceModel):
    request_id: UUID
    shop_id: UUID
    input_kind: str
    status: str
    transcript: str | None = None
    intent: VoiceIntent | None = None
    error: str | None = None


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


def audio_fingerprint(request: VoiceAudioRequest, decoded: bytes) -> VoiceRequestFingerprint:
    return request_fingerprint("audio", {"media_type": request.media_type.strip().lower(), "sha256": hashlib.sha256(decoded).hexdigest()})
