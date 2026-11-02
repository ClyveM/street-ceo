"""Review-first retail control contracts for purchases, stock takes, and close."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RetailModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


PurchaseKind = Literal["invoice", "manual"]
PurchaseTender = Literal["cash", "bank", "unpaid"]
PurchaseStatus = Literal["draft", "confirmed"]
StockTakeMode = Literal["monthly", "on_demand"]
CashMovementKind = Literal["opening_balance", "refund", "adjustment"]
CashTender = Literal["cash", "bank"]


class PurchaseLineCreate(RetailModel):
    product_id: UUID | None = None
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    unit_price_cents: int | None = Field(default=None, ge=0)
    quantity: int = Field(gt=0, le=1_000_000)
    purchase_unit_cost_micros: int = Field(ge=0)
    line_total_micros: int = Field(ge=0)

    @field_validator("sku", "name")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return None if value is None else value.strip() or None

    @model_validator(mode="after")
    def validate_product_reference(self) -> "PurchaseLineCreate":
        if self.product_id is None and not self.sku:
            raise ValueError("new purchase lines require sku")
        if self.product_id is None and not self.name:
            raise ValueError("new purchase lines require name")
        if self.product_id is None and self.unit_price_cents is None:
            raise ValueError("new purchase lines require unit price")
        expected = self.quantity * self.purchase_unit_cost_micros
        if self.line_total_micros != expected:
            raise ValueError("line_total_micros must equal quantity multiplied by purchase_unit_cost_micros")
        return self


class PurchaseCreate(RetailModel):
    kind: PurchaseKind
    reference: str = Field(min_length=1, max_length=120)
    purchase_date: date
    actor: str = Field(min_length=1, max_length=80)
    supplier: str | None = Field(default=None, max_length=160)
    tender: PurchaseTender = "unpaid"
    notes: str = Field(default="", max_length=500)
    lines: list[PurchaseLineCreate] = Field(min_length=1, max_length=200)
    total_cost_micros: int = Field(ge=0)

    @field_validator("reference", "actor", "supplier", "notes")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return None if value is None else value.strip()

    @model_validator(mode="after")
    def validate_total(self) -> "PurchaseCreate":
        if self.total_cost_micros != sum(line.line_total_micros for line in self.lines):
            raise ValueError("total_cost_micros must equal the sum of line totals")
        product_ids = [line.product_id for line in self.lines if line.product_id is not None]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("purchase product may appear only once")
        new_skus = [line.sku.lower() for line in self.lines if line.product_id is None and line.sku]
        if len(new_skus) != len(set(new_skus)):
            raise ValueError("new purchase SKU may appear only once")
        return self


class PurchaseRecord(PurchaseCreate):
    id: UUID
    shop_id: UUID
    status: PurchaseStatus = "draft"
    created_at: datetime
    confirmed_at: datetime | None = None


class PurchaseLineResult(RetailModel):
    product_id: UUID
    quantity_received: int
    stock_before: int
    stock_after: int
    purchase_unit_cost_micros: int
    previous_unit_cost_micros: int | None = None
    new_average_unit_cost_micros: int
    cost_change_micros: int | None = None
    insight: Literal["baseline_established", "cost_increased", "cost_decreased", "cost_unchanged"]


class PurchaseConfirmation(RetailModel):
    purchase_id: UUID
    shop_id: UUID
    status: Literal["confirmed"] = "confirmed"
    total_cost_micros: int
    lines: list[PurchaseLineResult]
    insights: list[str] = Field(default_factory=list)
    confirmed_at: datetime


class StockTakeLineCreate(RetailModel):
    product_id: UUID
    counted_qty: int = Field(ge=0)


class StockTakeCreate(RetailModel):
    mode: StockTakeMode
    count_date: date
    actor: str = Field(min_length=1, max_length=80)
    notes: str = Field(default="", max_length=500)
    lines: list[StockTakeLineCreate] = Field(min_length=1, max_length=500)

    @field_validator("actor", "notes")
    @classmethod
    def strip_stock_take_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def reject_duplicate_products(self) -> "StockTakeCreate":
        ids = [line.product_id for line in self.lines]
        if len(ids) != len(set(ids)):
            raise ValueError("stock-take product may appear only once")
        return self


class StockTakeRecord(StockTakeCreate):
    id: UUID
    shop_id: UUID
    status: PurchaseStatus = "draft"
    created_at: datetime
    confirmed_at: datetime | None = None
    expected_snapshot: dict[UUID, int] = Field(default_factory=dict)


class StockAdjustmentAudit(RetailModel):
    id: UUID
    stock_take_id: UUID
    shop_id: UUID
    product_id: UUID
    expected_qty: int
    counted_qty: int
    adjustment_qty: int
    actor: str
    reason: str
    recorded_at: datetime


class StockTakeConfirmation(RetailModel):
    stock_take_id: UUID
    shop_id: UUID
    status: Literal["confirmed"] = "confirmed"
    adjustments: list[StockAdjustmentAudit]
    confirmed_at: datetime


class CashMovementCreate(RetailModel):
    kind: CashMovementKind
    occurred_at: datetime
    amount_cents: int
    tender: CashTender
    actor: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=1, max_length=240)

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        return value.astimezone(timezone.utc)

    @field_validator("actor", "reason")
    @classmethod
    def strip_movement_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_amount(self) -> "CashMovementCreate":
        if self.kind in {"opening_balance", "refund"} and self.amount_cents <= 0:
            raise ValueError("opening balance and refund amounts must be positive")
        if self.kind == "adjustment" and self.amount_cents == 0:
            raise ValueError("adjustment amount must not be zero")
        return self


class CashMovementRecord(CashMovementCreate):
    id: UUID
    shop_id: UUID
    created_at: datetime


class DayCloseCreate(RetailModel):
    business_date: date
    cash_counted_cents: int = Field(ge=0)
    bank_card_counted_cents: int = Field(ge=0)
    actor: str = Field(min_length=1, max_length=80)
    notes: str = Field(default="", max_length=500)
    confirmed: bool = False

    @field_validator("actor", "notes")
    @classmethod
    def strip_close_text(cls, value: str) -> str:
        return value.strip()


class DayCloseRecord(RetailModel):
    id: UUID
    audit_id: UUID
    shop_id: UUID
    business_date: date
    opening_cash_cents: int
    opening_bank_card_cents: int
    sales_cash_cents: int
    sales_bank_card_cents: int
    paid_expenses_cash_cents: int
    paid_expenses_bank_card_cents: int
    paid_purchases_cash_cents: int
    paid_purchases_bank_card_cents: int
    refunds_cash_cents: int
    refunds_bank_card_cents: int
    adjustments_cash_cents: int
    adjustments_bank_card_cents: int
    expected_cash_cents: int
    expected_bank_card_cents: int
    cash_counted_cents: int
    bank_card_counted_cents: int
    cash_variance_cents: int
    bank_card_variance_cents: int
    notes: str
    actor: str
    confirmed_at: datetime
    calculation_basis: Literal["full_recorded_movements"] = "full_recorded_movements"
    shop_timezone: str
    warnings: list[str] = Field(default_factory=list)


class DayClosePreview(RetailModel):
    business_date: date
    opening_cash_cents: int
    opening_bank_card_cents: int
    sales_cash_cents: int
    sales_bank_card_cents: int
    paid_expenses_cash_cents: int
    paid_expenses_bank_card_cents: int
    paid_purchases_cash_cents: int
    paid_purchases_bank_card_cents: int
    refunds_cash_cents: int
    refunds_bank_card_cents: int
    adjustments_cash_cents: int
    adjustments_bank_card_cents: int
    expected_cash_cents: int
    expected_bank_card_cents: int
    shop_timezone: str
    calculation_basis: Literal["full_recorded_movements"] = "full_recorded_movements"
    warnings: list[str] = Field(default_factory=list)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
