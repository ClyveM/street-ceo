"""Meta Llama interpreter for the provider-neutral Apo/Napo flow.

Audio capture and speech transcription stay outside this adapter.  This class
receives a transcript and asks Meta Llama to turn it into a bounded
``CommandIntent``; the voice state machine still owns confirmation and sale
posting.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from services.ai.boundary import validate_sale_intent

from .state_machine import CommandIntent, Interpreter


class ChatClient(Protocol):
    def create(self, *, messages: Sequence[Mapping[str, str]], model: str) -> Any: ...


@dataclass(frozen=True)
class MetaLlamaSettings:
    model: str
    api_key: str | None

    @classmethod
    def from_env(cls) -> "MetaLlamaSettings":
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:  # pragma: no cover - optional in minimal environments
            pass
        return cls(
            model=os.getenv("LLAMA_MODEL", "").strip(),
            api_key=os.getenv("LLAMA_API_KEY"),
        )


class MetaLlamaInterpreter(Interpreter):
    """Interpret short shop commands through Meta's official Llama client."""

    def __init__(self, client: ChatClient, model: str) -> None:
        if not model.strip():
            raise ValueError("LLAMA_MODEL is required")
        self.client = client
        self.model = model.strip()

    def interpret(self, text: str) -> CommandIntent:
        if not text.strip():
            raise ValueError("voice transcript is empty")
        response = self.client.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Street CEO's sale-command parser. Return JSON only with exactly "
                        "action, item, quantity, price_override_minor, needs_confirmation. "
                        "Allowed actions: record_sale, check_stock, check_cash, cancel, unknown. "
                        "Never invent an item or execute a sale. A sale needs an item and a positive quantity."
                    ),
                },
                {"role": "user", "content": text.strip()},
            ],
        )
        payload = _response_json(response)
        intent = validate_sale_intent(payload)
        return CommandIntent(action=intent.action, item=intent.item, quantity=intent.quantity)


def build_meta_llama_interpreter(settings: MetaLlamaSettings | None = None) -> MetaLlamaInterpreter:
    """Build the live interpreter from local environment configuration."""

    settings = settings or MetaLlamaSettings.from_env()
    if not settings.api_key:
        raise RuntimeError("LLAMA_API_KEY is not configured")
    if not settings.model:
        raise RuntimeError("LLAMA_MODEL is not configured")
    try:
        from llama_api_client import LlamaAPIClient
    except ImportError as exc:  # pragma: no cover - depends on deployment extras
        raise RuntimeError("Install the official llama-api-client package") from exc
    client = LlamaAPIClient(api_key=settings.api_key)
    return MetaLlamaInterpreter(client.chat.completions, settings.model)


def _response_json(response: Any) -> Mapping[str, Any]:
    """Extract the JSON object from the official client's response shape."""

    message = getattr(response, "completion_message", None)
    content = getattr(message, "content", None) if message is not None else None
    if content is None and isinstance(response, Mapping):
        message = response.get("completion_message") or response.get("message")
        content = message.get("content") if isinstance(message, Mapping) else None
    if isinstance(content, list):
        content = "".join(str(part.get("text", "")) if isinstance(part, Mapping) else str(part) for part in content)
    if not isinstance(content, str):
        raise ValueError("Meta Llama response did not contain text content")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Meta Llama response was not valid JSON") from exc
    if not isinstance(parsed, Mapping):
        raise ValueError("Meta Llama response must be a JSON object")
    return parsed
