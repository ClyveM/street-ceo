"""Review-first invoice, product-cost, and operating-expense contracts."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator


class CostModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


InvoiceExtractionStatus = Literal["pending", "needs_review", "confirmed", "rejected", "provider_unavailable"]
InvoiceLineSource = Literal["manual_review", "ocr_provider"]
InvoiceMatchStatus = Literal["unmatched", "suggested", "accepted"]


class InvoiceLineDraft(CostModel):
    id: UUID
    description: str = Field(min_length=1, max_length=240)
    sku: str | None = Field(default=None, max_length=64)
    quantity: int = Field(gt=0, le=1_000_000)
    line_total_cents: int = Field(ge=0)
    calculated_unit_cost_micros: int | None = Field(default=None, ge=0)
    suggested_product_id: UUID | None = None
    matched_product_id: UUID | None = None
    match_status: InvoiceMatchStatus = "unmatched"
    source: InvoiceLineSource
    evidence_ref: str | None = Field(default=None, max_length=240)


class InvoiceUpload(CostModel):
    id: UUID
    shop_id: UUID
    filename: str
    content_type: Literal["application/pdf", "image/jpeg", "image/png", "image/webp"]
    size_bytes: int = Field(gt=0, le=10 * 1024 * 1024)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    storage_backend: Literal["memory"] = "memory"
    storage_ref: str
    extraction_status: InvoiceExtractionStatus = "provider_unavailable"
    extraction_source: Literal["none", "ocr_provider", "manual_review"] = "none"
    lines: list[InvoiceLineDraft] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    uploaded_at: datetime
    confirmed_at: datetime | None = None


class InvoiceLineReview(CostModel):
    description: str = Field(min_length=1, max_length=240)
    sku: str | None = Field(default=None, max_length=64)
    product_id: UUID | None = None
    quantity: int = Field(gt=0, le=1_000_000)
    line_total_cents: int = Field(ge=0)

    @field_validator("description", "sku")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return None if value is None else value.strip() or None


class InvoiceReviewRequest(CostModel):
    source: InvoiceLineSource = "manual_review"
    evidence_ref: str | None = Field(default=None, max_length=240)
    lines: list[InvoiceLineReview] = Field(min_length=1, max_length=200)


class InvoiceConfirmation(CostModel):
    invoice_id: UUID
    shop_id: UUID
    status: Literal["confirmed"] = "confirmed"
    applied_line_ids: list[UUID]
    stock_units_added: int
    cost_updates: int
    warnings: list[str] = Field(default_factory=list)
    confirmed_at: datetime


class ProductCostAudit(CostModel):
    id: UUID
    shop_id: UUID
    product_id: UUID
    invoice_id: UUID | None = None
    source_type: Literal["invoice_receipt", "direct_correction", "purchase", "stock_take", "demo_seed"] = "invoice_receipt"
    source_ref: str = ""
    actor: str = "system"
    reason: str = ""
    effective_date: date | None = None
    quantity_received: int = Field(default=0, ge=0)
    unit_cost_micros: int = Field(ge=0)
    previous_unit_cost_micros: int | None = Field(default=None, ge=0)
    new_unit_cost_micros: int = Field(ge=0)
    stock_before: int = Field(ge=0)
    stock_after: int = Field(ge=0)
    recorded_at: datetime


class ProductCostCorrectionCreate(CostModel):
    unit_cost: Decimal | None = None
    unit_cost_micros: StrictInt | None = Field(default=None, ge=0)
    effective_date: date
    reason: str = Field(min_length=1, max_length=500)
    source_ref: str = Field(min_length=1, max_length=240)
    actor: str = Field(min_length=1, max_length=80)

    @field_validator("unit_cost", mode="before")
    @classmethod
    def reject_float_cost(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("unit_cost must be a decimal string, not a float")
        return value

    @field_validator("unit_cost")
    @classmethod
    def validate_decimal_cost(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return value
        if not value.is_finite() or value < 0:
            raise ValueError("unit_cost must be finite and non-negative")
        if value.as_tuple().exponent < -6:
            raise ValueError("unit_cost supports at most 6 decimal places")
        return value

    @field_validator("reason", "source_ref", "actor")
    @classmethod
    def strip_correction_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def require_one_cost_form(self) -> "ProductCostCorrectionCreate":
        if (self.unit_cost is None) == (self.unit_cost_micros is None):
            raise ValueError("provide exactly one of unit_cost or unit_cost_micros")
        if self.unit_cost is not None:
            micros = self.unit_cost * 1_000_000
            if micros != micros.to_integral_value():
                raise ValueError("unit_cost cannot be represented exactly in micros")
        return self

    def resolved_unit_cost_micros(self) -> int:
        if self.unit_cost_micros is not None:
            return self.unit_cost_micros
        assert self.unit_cost is not None
        return int(self.unit_cost * 1_000_000)


class ProductCostCorrection(CostModel):
    id: UUID
    shop_id: UUID
    product_id: UUID
    unit_cost_micros: int = Field(ge=0)
    effective_date: date
    reason: str
    source_ref: str
    actor: str
    status: Literal["draft", "confirmed"] = "draft"
    created_at: datetime
    confirmed_at: datetime | None = None


ExpenseCategory = Literal["electricity", "transport", "rent", "wages", "airtime", "supplies", "other"]
ExpenseFrequency = Literal["one_off", "recurring"]
ExpenseStatus = Literal["draft", "confirmed", "rejected"]


class ExpenseCreate(CostModel):
    category: ExpenseCategory
    frequency: ExpenseFrequency = "one_off"
    occurred_on: date
    period_start: date | None = None
    period_end: date | None = None
    amount_cents: int = Field(gt=0)
    notes: str = Field(default="", max_length=500)
    tender: Literal["cash", "bank", "unpaid"] = "unpaid"

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_period(self) -> "ExpenseCreate":
        if (self.period_start is None) != (self.period_end is None):
            raise ValueError("period_start and period_end must be supplied together")
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end must not be before period_start")
        if self.frequency == "one_off" and self.period_start is not None:
            raise ValueError("one_off expenses must not include a period")
        if self.frequency == "recurring" and self.period_start is None:
            raise ValueError("recurring expenses require a period")
        return self


class ExpenseRecord(ExpenseCreate):
    id: UUID
    shop_id: UUID
    status: ExpenseStatus = "draft"
    created_at: datetime
    confirmed_at: datetime | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
