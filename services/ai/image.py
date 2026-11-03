"""Meta Muse Image adapter for the draft-only social image boundary.

The existing ``LLAMA_MODEL`` chat configuration is intentionally not reused as
an image capability. Image generation requires an explicitly configured
``MUSE_IMAGE_MODEL`` (for example, ``muse-image-1.0``) and the same server-side
API key must be verified separately by deployment smoke testing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal, Mapping

try:
    from .boundary import ImageProviderRequest, SocialImageRequest, StructuredAI
except ImportError:  # unittest discovery from services/ai
    from boundary import ImageProviderRequest, SocialImageRequest, StructuredAI

SUPPORTED_MUSE_IMAGE_MODEL = "muse-image-1.0"
MUSE_IMAGE_BASE_URL = "https://api.meta.ai/v1"
MUSE_IMAGE_GENERATIONS_ENDPOINT = f"{MUSE_IMAGE_BASE_URL}/images/generations"
MUSE_IMAGE_EDITS_ENDPOINT = f"{MUSE_IMAGE_BASE_URL}/images/edits"


@dataclass(frozen=True)
class MuseImageSettings:
    model: str
    api_key: str | None

    @classmethod
    def from_env(cls) -> "MuseImageSettings":
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:  # pragma: no cover
            pass
        return cls(os.getenv("MUSE_IMAGE_MODEL", "").strip(), os.getenv("LLAMA_API_KEY", "").strip() or None)

    @property
    def image_capable(self) -> bool:
        return bool(self.api_key and self.model == SUPPORTED_MUSE_IMAGE_MODEL)


@dataclass(frozen=True)
class MuseImageConfigurationAudit:
    """Safe configuration diagnostics; never includes the credential itself."""

    status: Literal["missing_model", "unsupported_model", "missing_api_key", "ready_for_smoke_test"]
    configured_model: str | None
    expected_model: str
    api_key_env: str
    generation_endpoint: str
    edit_endpoint: str
    live_access_verified: bool
    reason: str


def audit_muse_image_configuration(settings: MuseImageSettings | None = None) -> MuseImageConfigurationAudit:
    """Explain image configuration without claiming that a key has entitlement.

    A real provider response (or an explicit provider error) is required to
    prove account/model access. Configuration alone only establishes that a
    smoke test can be attempted.
    """

    settings = settings or MuseImageSettings.from_env()
    if not settings.model:
        return MuseImageConfigurationAudit(
            "missing_model", None, SUPPORTED_MUSE_IMAGE_MODEL, "LLAMA_API_KEY",
            MUSE_IMAGE_GENERATIONS_ENDPOINT, MUSE_IMAGE_EDITS_ENDPOINT, False,
            "MUSE_IMAGE_MODEL is not set; the current text model cannot select an image capability.",
        )
    if settings.model != SUPPORTED_MUSE_IMAGE_MODEL:
        return MuseImageConfigurationAudit(
            "unsupported_model", settings.model, SUPPORTED_MUSE_IMAGE_MODEL, "LLAMA_API_KEY",
            MUSE_IMAGE_GENERATIONS_ENDPOINT, MUSE_IMAGE_EDITS_ENDPOINT, False,
            f"{settings.model} is not the documented Muse Image model; use {SUPPORTED_MUSE_IMAGE_MODEL}.",
        )
    if not settings.api_key:
        return MuseImageConfigurationAudit(
            "missing_api_key", settings.model, SUPPORTED_MUSE_IMAGE_MODEL, "LLAMA_API_KEY",
            MUSE_IMAGE_GENERATIONS_ENDPOINT, MUSE_IMAGE_EDITS_ENDPOINT, False,
            "LLAMA_API_KEY is not set; a server-side Meta Model API key is required.",
        )
    return MuseImageConfigurationAudit(
        "ready_for_smoke_test", settings.model, SUPPORTED_MUSE_IMAGE_MODEL, "LLAMA_API_KEY",
        MUSE_IMAGE_GENERATIONS_ENDPOINT, MUSE_IMAGE_EDITS_ENDPOINT, False,
        "Model and key are configured; live image access still requires a real request and is not verified here.",
    )


class MetaMuseImageProvider:
    """Raw HTTP adapter for Meta's Muse Image single-shot endpoints."""

    def __init__(self, api_key: str, model: str, http_client: Any) -> None:
        self.api_key = api_key
        self.model = model
        self.http_client = http_client

    def generate_image(self, request: ImageProviderRequest) -> Mapping[str, Any]:
        endpoint = MUSE_IMAGE_EDITS_ENDPOINT if request.image_refs else MUSE_IMAGE_GENERATIONS_ENDPOINT
        body: dict[str, Any] = {
            "model": self.model,
            "prompt": request.prompt,
            "n": 1,
            "size": request.size,
            "output_format": request.output_format,
        }
        if request.image_refs:
            body["images"] = [
                {"image_url": ref} if ref.startswith(("http://", "https://", "data:image/")) else {"file_id": ref}
                for ref in request.image_refs
            ]
        response = self.http_client.post(endpoint, headers={"Authorization": f"Bearer {self.api_key}"}, json=body)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ValueError("Meta image response must be an object")
        data = payload.get("data")
        if not isinstance(data, list) or not data:
            raise ValueError("Meta image response did not contain image data")
        item = data[0]
        if not isinstance(item, Mapping):
            raise ValueError("Meta image item must be an object")
        image_ref = item.get("url") or item.get("b64_json")
        if not isinstance(image_ref, str) or not image_ref:
            raise ValueError("Meta image response did not contain a usable image reference")
        if item.get("b64_json"):
            image_ref = f"data:image/{request.output_format};base64,{image_ref}"
        return {
            "status": "draft",
            "provider": "meta_muse_image",
            "model": self.model,
            "image_refs": [image_ref],
            "warnings": ["Generated image is an editable draft and has not been published."],
        }


def build_muse_image_ai(settings: MuseImageSettings | None = None) -> StructuredAI:
    """Build an image-capable boundary only when explicitly configured."""

    settings = settings or MuseImageSettings.from_env()
    if not settings.image_capable:
        return StructuredAI(None)
    try:
        import httpx
        import truststore
        client = httpx.Client(verify=truststore.SSLContext(), timeout=httpx.Timeout(75.0, connect=10.0))
    except ImportError:  # pragma: no cover
        return StructuredAI(None)
    return StructuredAI(None, timeout_seconds=75.0, image_provider=MetaMuseImageProvider(settings.api_key, settings.model, client))


def generate_social_image(request: SocialImageRequest, *, ai: StructuredAI | None = None):
    """Return a validated image draft or an explicit unavailable response."""

    return (ai or build_muse_image_ai()).social_image(request)
