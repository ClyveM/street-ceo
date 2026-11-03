"""Shop-scoped catalogue data contract for the Social Update workflow."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SocialDataModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ShopImageMetadata(SocialDataModel):
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(min_length=5, max_length=80)
    size_bytes: int = Field(gt=0, le=10 * 1024 * 1024)
    width: int | None = Field(default=None, ge=1, le=20_000)
    height: int | None = Field(default=None, ge=1, le=20_000)

    @field_validator("filename", "content_type")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("content_type")
    @classmethod
    def require_image_type(cls, value: str) -> str:
        if not value.lower().startswith("image/"):
            raise ValueError("content_type must be an image MIME type")
        return value.lower()


class SocialBriefRequest(SocialDataModel):
    product_ids: list[UUID] = Field(min_length=1, max_length=12)
    shop_image: ShopImageMetadata | None = None

    @field_validator("product_ids")
    @classmethod
    def reject_duplicate_products(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("product_ids must not contain duplicates")
        return value


class SelectedSocialProduct(SocialDataModel):
    product_id: UUID
    sku: str
    name: str
    unit_price_cents: int = Field(ge=0)
    stock_qty: int = Field(ge=0)


class SocialBriefResponse(SocialDataModel):
    shop_id: UUID
    products: list[SelectedSocialProduct]
    shop_image: ShopImageMetadata | None = None
    catalogue_source: Literal["repository"] = "repository"
    created_at: datetime


class ProductImageMetadata(SocialDataModel):
    id: UUID
    shop_id: UUID
    product_id: UUID
    filename: str
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    size_bytes: int = Field(gt=0, le=10 * 1024 * 1024)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    storage_backend: Literal["memory"] = "memory"
    storage_ref: str
    uploaded_at: datetime


class SocialImageGenerationRequest(SocialDataModel):
    shop_photo_data: str | None = Field(default=None, max_length=7_000_000)
    product_ids: list[UUID] = Field(min_length=1, max_length=12)
    source_image_id: UUID | None = None
    brief: str = Field(min_length=1, max_length=1000)
    aspect_ratio: Literal["1:1", "4:5", "9:16", "16:9"] = "1:1"

    @field_validator("brief")
    @classmethod
    def strip_brief(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("brief must not be blank")
        return value

    @field_validator("product_ids")
    @classmethod
    def reject_duplicate_products(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("product_ids must not contain duplicates")
        return value


class SocialClaimResponse(SocialDataModel):
    product_id: str
    claim: str
    source_field: str


class SocialDraftRequest(SocialDataModel):
    product_ids: list[UUID] = Field(min_length=1, max_length=12)
    brief: str = Field(min_length=1, max_length=1000)
    source_image_id: UUID | None = None
    duration_seconds: int = Field(default=40, gt=0, le=120)

    @field_validator("brief")
    @classmethod
    def strip_brief(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("brief must not be blank")
        return value

    @field_validator("product_ids")
    @classmethod
    def reject_duplicate_products(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("product_ids must not contain duplicates")
        return value


class SocialDraftResponse(SocialDataModel):
    id: UUID
    shop_id: UUID
    title: str
    caption: str
    voiceover_script: str
    shot_list: list[str]
    selected_product_ids: list[UUID]
    claims: list[SocialClaimResponse]
    status: Literal["draft", "unavailable"]
    source: Literal["provider", "fallback"]
    provider: str
    model: str | None = None
    warnings: list[str] = []
    draft_only: bool = True
    created_at: datetime


class SocialImageGenerationResponse(SocialDataModel):
    id: UUID
    shop_id: UUID
    product_ids: list[UUID]
    source_image_id: UUID | None = None
    brief: str
    aspect_ratio: str
    status: Literal["draft", "provider_not_configured", "unavailable"]
    provider: str
    model: str | None = None
    image_refs: list[str] = []
    warnings: list[str] = []
    draft_only: bool = True
    output_url: str | None = None
    created_at: datetime


_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_image_filename(filename: str) -> str:
    """Return a safe basename; reject paths and control/shell-like characters."""
    if not filename or filename != filename.replace("\\", "/").split("/")[-1] or not _SAFE_FILENAME.fullmatch(filename):
        raise ValueError("filename must be a safe image basename")
    return filename


def validate_image_content_type(content_type: str) -> str:
    normalized = content_type.split(";", 1)[0].strip().lower()
    if normalized not in _ALLOWED_IMAGE_TYPES:
        raise ValueError("content_type must be image/jpeg, image/png, or image/webp")
    return normalized

