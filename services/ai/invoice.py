"""Review-only invoice image extraction over Meta's hosted chat API.

No Llama 4 Scout slug is hardcoded: the hosted model must be explicitly
authorized and supplied through ``LLAMA_VISION_MODEL`` after it appears in the
account's ``GET /v1/models`` catalog.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping

try:
    from .boundary import InvoiceImageRequest, StructuredAI
except ImportError:  # pragma: no cover
    from boundary import InvoiceImageRequest, StructuredAI

META_CHAT_ENDPOINT = "https://api.meta.ai/v1/chat/completions"


@dataclass(frozen=True)
class InvoiceVisionSettings:
    model: str
    api_key: str | None

    @classmethod
    def from_env(cls) -> "InvoiceVisionSettings":
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:  # pragma: no cover
            pass
        return cls(os.getenv("LLAMA_VISION_MODEL", "").strip(), os.getenv("LLAMA_API_KEY", "").strip() or None)

    @property
    def configured(self) -> bool:
        return bool(self.model and self.api_key)


class MetaInvoiceVisionProvider:
    """Meta chat-completions adapter using user image input and JSON output."""

    def __init__(self, api_key: str, model: str, http_client: Any) -> None:
        self.api_key = api_key
        self.model = model
        self.http_client = http_client

    def extract(self, request: Mapping[str, str]) -> Mapping[str, Any]:
        prompt = (
            "Read this supplier invoice image and return JSON only with exactly "
            "status, provider, model, lines, warnings, review_only. Each line must have "
            "description, sku, quantity, line_total_minor, unit_cost_minor. "
            "Use null when a value is not legible. Never infer missing values. "
            "Set status to review_required and review_only to true. Do not match products, "
            "update stock, update costs, or confirm the invoice. "
            f"Human review instructions: {request['instructions']}"
        )
        content = [{"type": "text", "text": prompt}]
        if request["content_type"] == "application/pdf":
            file_ref = request["image_ref"]
            # The boundary accepts both provider file-id spellings currently
            # used by Meta surfaces. Preserve either spelling as an ID rather
            # than accidentally embedding it as file_data.
            file = {"file_id": file_ref} if file_ref.startswith(("file-", "file_")) else {
                "file_data": file_ref,
                "filename": request["filename"],
            }
            content.append({"type": "file", "file": file})
        else:
            content.append({"type": "image_url", "image_url": {"url": request["image_ref"]}})
        response = self.http_client.post(
            META_CHAT_ENDPOINT,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": content}],
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        payload = response.json()
        message = payload.get("completion_message") or payload.get("message") if isinstance(payload, Mapping) else None
        if not isinstance(message, Mapping):
            choices = payload.get("choices") if isinstance(payload, Mapping) else None
            message = choices[0].get("message") if isinstance(choices, list) and choices and isinstance(choices[0], Mapping) else None
        raw_content = message.get("content") if isinstance(message, Mapping) else None
        if isinstance(raw_content, list):
            raw_content = "".join(part.get("text", "") if isinstance(part, Mapping) else str(part) for part in raw_content)
        if not isinstance(raw_content, str):
            raise ValueError("invoice vision response did not contain text")
        parsed = json.loads(raw_content)
        if not isinstance(parsed, Mapping):
            raise ValueError("invoice vision response was not an object")
        return {**parsed, "provider": "meta_invoice_vision", "model": self.model}


def build_invoice_vision_ai(settings: InvoiceVisionSettings | None = None) -> StructuredAI:
    settings = settings or InvoiceVisionSettings.from_env()
    if not settings.configured:
        return StructuredAI(None)
    try:
        import httpx
        import truststore
        client = httpx.Client(verify=truststore.SSLContext(), timeout=20.0)
    except ImportError:  # pragma: no cover
        return StructuredAI(None)
    return StructuredAI(None, timeout_seconds=20.0, invoice_provider=MetaInvoiceVisionProvider(settings.api_key, settings.model, client))


def extract_invoice_image(request: InvoiceImageRequest, *, ai: StructuredAI | None = None):
    return (ai or build_invoice_vision_ai()).invoice_extract(request)
