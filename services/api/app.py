"""Street CEO API foundation with an explicit persistence boundary."""

from __future__ import annotations

import hashlib
import json
import base64
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from services.api.persistence import (
    RepositoryConflict,
    RepositoryIdempotencyConflict,
    RepositoryInsufficientStock,
    RepositoryNotFound,
    Settings,
    build_repository,
)
from services.api.social_data import (
    ProductImageMetadata,
    SelectedSocialProduct,
    ShopImageMetadata,
    SocialBriefRequest,
    SocialBriefResponse,
    SocialClaimResponse,
    SocialDraftRequest,
    SocialDraftResponse,
    SocialImageGenerationRequest,
    SocialImageGenerationResponse,
    validate_image_content_type,
    validate_image_filename,
)
from services.api.costs import (
    ExpenseCreate,
    ExpenseRecord,
    InvoiceConfirmation,
    InvoiceLineDraft,
    InvoiceReviewRequest,
    InvoiceUpload,
    ProductCostCorrection,
    ProductCostCorrectionCreate,
    ProductCostAudit,
    utc_now,
)
from services.api.retail_control import (
    DayCloseCreate,
    DayCloseRecord,
    DayClosePreview,
    CashMovementCreate,
    CashMovementRecord,
    CashOpeningCreate,
    CashCloseCreate,
    CashCloseRecord,
    CashClosePreview,
    PurchaseConfirmation,
    PurchaseCreate,
    PurchaseLineResult,
    PurchaseRecord,
    StockAdjustmentAudit,
    StockTakeConfirmation,
    StockTakeCreate,
    StockTakeRecord,
    utc_now as retail_utc_now,
)
from services.api.voice_boundary import (
    VoiceAudioRequest,
    VoiceIntent,
    VoiceResponse,
    VoiceSaleCommitRequest,
    VoiceSaleCommitLine,
    VoiceSaleLine,
    VoiceSaleReversal,
    VoiceTenderQuestion,
    VoiceSaleUndoRequest,
    VoiceTranscriptRequest,
    audio_fingerprint,
    parse_catalogue_sale,
    parse_quantity_reply,
    decode_audio,
    normalize_intent,
    request_fingerprint,
)
from services.ai.boundary import Evidence, InsightRequest, InvoiceCatalogueProduct, InvoiceImageRequest, StructuredAI
from services.ai.boundary import SocialImageRequest, SocialProduct, SocialRequest
from services.ai.image import build_muse_image_ai
from services.ai.invoice import build_invoice_vision_ai
from services.ai.muse import build_muse_ai


_AUTO_CATALOGUE_RESOLVER = object()


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ShopCreate(ApiModel):
    name: str = Field(min_length=1, max_length=120)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    timezone: str = Field(default="Africa/Harare", min_length=1, max_length=64)

    @field_validator("name", "currency", "timezone")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class Shop(ApiModel):
    id: UUID
    name: str
    currency: str
    timezone: str


class ProductCreate(ApiModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    unit_price_cents: int = Field(ge=0)
    opening_stock_qty: int = Field(default=0, ge=0)

    @field_validator("sku", "name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class Product(ApiModel):
    id: UUID
    shop_id: UUID
    sku: str
    name: str
    unit_price_cents: int
    stock_qty: int
    unit_cost_micros: int | None = Field(default=None, ge=0)
    cost_source_invoice_id: UUID | None = None


class SaleLine(ApiModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class SaleCreate(ApiModel):
    lines: list[SaleLine] = Field(min_length=1)
    tender: str = Field(min_length=1, max_length=32)
    amount_received_cents: int | None = Field(default=None, ge=0, strict=True)

    @field_validator("tender")
    @classmethod
    def normalize_tender(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("lines")
    @classmethod
    def reject_duplicate_products(cls, lines: list[SaleLine]) -> list[SaleLine]:
        ids = [line.product_id for line in lines]
        if len(ids) != len(set(ids)):
            raise ValueError("product_id may appear only once")
        return lines


class SaleReceiptLine(ApiModel):
    product_id: UUID
    product_name: str
    sku: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int
    unit_cost_micros: int | None = None
    line_cogs_micros: int | None = None


class Sale(ApiModel):
    id: UUID
    shop_id: UUID
    lines: list[SaleLine]
    tender: str
    total_cents: int
    cogs_micros: int | None = Field(default=None, ge=0)
    amount_received_cents: int | None = Field(default=None, ge=0)
    change_cents: int = Field(default=0, ge=0)
    stock_after: dict[UUID, int] = Field(default_factory=dict)
    created_at: datetime
    receipt_lines: list[SaleReceiptLine] = Field(default_factory=list)


class DemoResetResponse(ApiModel):
    shop_id: UUID
    reset: bool = True
    product_count: int
    sales_count: int
    invoice_count: int
    expense_count: int
    cost_audit_count: int


class ShopSummary(ApiModel):
    sales_total_cents: int = Field(ge=0)
    transaction_count: int = Field(ge=0)
    low_stock_count: int = Field(ge=0)
    sales_change_percent: float | None = None
    insight: str


class ErrorResponse(ApiModel):
    detail: str


class MuseAskRequest(ApiModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class MuseAskResponse(ApiModel):
    status: str
    answer: str
    title: str
    evidence_ids: list[str]
    missing_data: list[str]
    source: str
    confidence: float = Field(ge=0, le=1)


@dataclass
class _ShopRecord:
    shop: Shop
    cash_closes: dict[date, CashCloseRecord] = field(default_factory=dict)
    cash_close_idempotency: dict[str, tuple[str, CashCloseRecord]] = field(default_factory=dict)
    products: dict[UUID, Product] = field(default_factory=dict)
    idempotent_sales: dict[str, tuple[str, Sale]] = field(default_factory=dict)
    voice_requests: dict[str, tuple[str, VoiceResponse]] = field(default_factory=dict)
    voice_reviews: dict[UUID, VoiceResponse] = field(default_factory=dict)
    voice_review_commits: dict[UUID, tuple[str, str, Sale]] = field(default_factory=dict)
    voice_sale_ids: set[UUID] = field(default_factory=set)
    voice_sale_reversals: dict[UUID, VoiceSaleReversal] = field(default_factory=dict)
    voice_reversal_idempotency: dict[str, tuple[str, VoiceSaleReversal]] = field(default_factory=dict)
    invoices: dict[UUID, InvoiceUpload] = field(default_factory=dict)
    invoice_bytes: dict[UUID, bytes] = field(default_factory=dict)
    expenses: dict[UUID, ExpenseRecord] = field(default_factory=dict)
    cost_audits: list[ProductCostAudit] = field(default_factory=list)
    cost_corrections: dict[UUID, ProductCostCorrection] = field(default_factory=dict)
    product_images: dict[UUID, ProductImageMetadata] = field(default_factory=dict)
    product_image_bytes: dict[UUID, bytes] = field(default_factory=dict)
    social_image_generations: dict[UUID, SocialImageGenerationResponse] = field(default_factory=dict)
    purchases: dict[UUID, PurchaseRecord] = field(default_factory=dict)
    stock_takes: dict[UUID, StockTakeRecord] = field(default_factory=dict)
    stock_adjustments: list[StockAdjustmentAudit] = field(default_factory=list)
    day_closes: dict[date, DayCloseRecord] = field(default_factory=dict)
    cash_movements: dict[UUID, CashMovementRecord] = field(default_factory=dict)
    cash_movement_idempotency: dict[str, tuple[str, CashMovementRecord]] = field(default_factory=dict)
    day_close_idempotency: dict[str, tuple[str, DayCloseRecord]] = field(default_factory=dict)
    purchase_confirmations: dict[UUID, PurchaseConfirmation] = field(default_factory=dict)
    stock_take_confirmations: dict[UUID, StockTakeConfirmation] = field(default_factory=dict)


class InMemoryStore:
    def __init__(self) -> None:
        self.shops: dict[UUID, _ShopRecord] = {}

    def check_ready(self) -> None:
        """Local mode has no external dependency to probe."""
        return None

    def create_shop(self, request: ShopCreate) -> Shop:
        shop = Shop(id=uuid4(), **request.model_dump())
        self.shops[shop.id] = _ShopRecord(shop=shop)
        return shop

    def get_shop_record(self, shop_id: UUID) -> _ShopRecord:
        record = self.shops.get(shop_id)
        if record is None:
            raise RepositoryNotFound("shop not found")
        return record

    def create_product(self, record: _ShopRecord, request: ProductCreate) -> Product:
        if any(product.sku == request.sku for product in record.products.values()):
            raise RepositoryConflict("sku already exists")
        product = Product(
            id=uuid4(), shop_id=record.shop.id, sku=request.sku, name=request.name,
            unit_price_cents=request.unit_price_cents, stock_qty=request.opening_stock_qty,
        )
        record.products[product.id] = product
        return product

    def list_products(self, record: _ShopRecord) -> list[Product]:
        return list(record.products.values())

    def create_sale(
        self,
        record: _ShopRecord,
        request: SaleCreate,
        fingerprint: str,
        key: str,
        amount_received_cents: int | None = None,
        change_cents: int = 0,
    ) -> Sale:
        previous = record.idempotent_sales.get(key)
        if previous:
            old_fingerprint, old_sale = previous
            if old_fingerprint != fingerprint:
                raise RepositoryIdempotencyConflict("idempotency key payload mismatch")
            return old_sale
        products: list[Product] = []
        for line in request.lines:
            product = record.products.get(line.product_id)
            if product is None:
                raise RepositoryNotFound("product not found")
            if product.stock_qty < line.quantity:
                raise RepositoryInsufficientStock("insufficient stock")
            products.append(product)
        total_cents = sum(product.unit_price_cents * line.quantity for product, line in zip(products, request.lines))
        if amount_received_cents is None and request.amount_received_cents is not None:
            amount_received_cents = request.amount_received_cents
            if request.tender not in {"cash", "bank"}:
                raise RepositoryConflict("cash received requires cash or bank tender")
            if request.tender == "cash" and amount_received_cents < total_cents:
                raise HTTPException(status_code=409, detail={"code": "insufficient_cash", "message": "Cash received is less than the sale total.", "amount_due_cents": total_cents, "amount_received_cents": amount_received_cents})
            if request.tender == "bank" and amount_received_cents != total_cents:
                raise HTTPException(status_code=409, detail={"code": "invalid_bank_amount", "message": "Bank payment amount must equal the sale total.", "amount_due_cents": total_cents})
            change_cents = amount_received_cents - total_cents if request.tender == "cash" else 0
        cogs_micros = sum(
            product.unit_cost_micros * line.quantity
            for product, line in zip(products, request.lines)
            if product.unit_cost_micros is not None
        )
        has_all_costs = all(product.unit_cost_micros is not None for product in products)
        sale = Sale(
            id=uuid4(), shop_id=record.shop.id, lines=request.lines, tender=request.tender,
            total_cents=total_cents,
            cogs_micros=cogs_micros if has_all_costs else None,
            amount_received_cents=amount_received_cents,
            change_cents=change_cents,
            created_at=datetime.now(timezone.utc),
            receipt_lines=[SaleReceiptLine(product_id=product.id, product_name=product.name, sku=product.sku, quantity=line.quantity, unit_price_cents=product.unit_price_cents, line_total_cents=product.unit_price_cents * line.quantity, unit_cost_micros=product.unit_cost_micros, line_cogs_micros=product.unit_cost_micros * line.quantity if product.unit_cost_micros is not None else None) for product, line in zip(products, request.lines)],
        )
        for product, line in zip(products, request.lines):
            product.stock_qty -= line.quantity
        sale.stock_after = {product.id: product.stock_qty for product in products}
        record.idempotent_sales[key] = (fingerprint, sale)
        return sale

    def seed_demo_shop(self) -> UUID:
        """Create the stable local catalogue used by the browser demo."""
        from pathlib import Path
        starter = json.loads(Path(__file__).with_name("demo_catalogue.json").read_text(encoding="utf-8"))
        shop_id = UUID(starter["shop"]["id"])
        if shop_id in self.shops:
            self._backfill_demo_costs(self.shops[shop_id], starter)
            return shop_id
        shop = Shop.model_validate(starter["shop"])
        record = _ShopRecord(shop=shop)
        for item in starter["products"]:
            product = Product(id=UUID(item["id"]), shop_id=shop_id, sku=item["sku"], name=item["name"], unit_price_cents=item["unit_price_cents"], stock_qty=item["stock_qty"])
            record.products[product.id] = product
        self.shops[shop_id] = record
        self._backfill_demo_costs(record, starter)
        return shop_id

    @staticmethod
    def _backfill_demo_costs(record: _ShopRecord, starter: dict) -> None:
        """Missing-only assumptions for exact demo identities; never rewrite sales."""
        if record.shop.model_dump(mode="json") != starter["shop"]:
            return
        audited_products = {audit.product_id for audit in record.cost_audits}
        for item in starter["products"]:
            product = record.products.get(UUID(item["id"]))
            if product is None or product.shop_id != record.shop.id or product.sku != item["sku"] or product.name != item["name"]:
                continue
            if product.unit_cost_micros is not None or product.cost_source_invoice_id is not None or product.id in audited_products:
                continue
            product.unit_cost_micros = item["unit_cost_micros"]
            record.cost_audits.append(ProductCostAudit(
                id=uuid4(), shop_id=record.shop.id, product_id=product.id,
                source_type="demo_seed", source_ref="STARTER-COGS-001", actor="demo_seed",
                reason=starter["cost_basis"], quantity_received=0,
                unit_cost_micros=item["unit_cost_micros"], previous_unit_cost_micros=None,
                new_unit_cost_micros=item["unit_cost_micros"],
                stock_before=product.stock_qty, stock_after=product.stock_qty,
                recorded_at=utc_now(),
            ))

    def reset_demo_shop(self) -> UUID:
        shop_id = UUID("00000000-0000-0000-0000-000000000001")
        self.shops.pop(shop_id, None)
        return self.seed_demo_shop()


def _payload_fingerprint(request: SaleCreate) -> str:
    canonical = json.dumps(request.model_dump(mode="json", exclude_none=True), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _muse_period_name(question: str) -> str:
    if "today" in question:
        return "today"
    if "this month" in question or "month" in question:
        return "this_month"
    import re
    match = re.search(r"(?:last|past)\s+(\d+)\s+days?", question)
    return f"last_{match.group(1)}_days" if match else "available"


def _muse_period_start(question: str, now: datetime) -> datetime:
    if "today" in question:
        return datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    if "this month" in question:
        return datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    import re
    match = re.search(r"(?:last|past)\s+(\d+)\s+days?", question)
    if match:
        return now - timedelta(days=int(match.group(1)))
    return datetime.min.replace(tzinfo=timezone.utc)


def _money(currency: str, cents: int) -> str:
    return f"{currency} {cents / 100:.2f}"


def _memory_image_ref(record: _ShopRecord, image_id: UUID | None) -> str | None:
    if image_id is None:
        return None
    metadata = record.product_images.get(image_id)
    content = record.product_image_bytes.get(image_id)
    if metadata is None or content is None:
        return None
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{metadata.content_type};base64,{encoded}"


def _social_products(record: _ShopRecord, product_ids: list[UUID]) -> tuple[SocialProduct, ...]:
    products: list[SocialProduct] = []
    for product_id in product_ids:
        product = record.products.get(product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="selected product not found in shop")
        latest_image = next(
            (image for image in reversed(list(record.product_images.values())) if image.product_id == product_id),
            None,
        )
        products.append(SocialProduct(
            product_id=str(product.id), name=product.name, sku=product.sku,
            price_minor=product.unit_price_cents, currency=record.shop.currency,
            image_ref=_memory_image_ref(record, latest_image.id if latest_image else None),
        ))
    return tuple(products)


def create_app(
    store: InMemoryStore | None = None,
    settings: Settings | None = None,
    voice_interpreter: object | None = None,
    muse_ai: StructuredAI | None = None,
    social_ai: StructuredAI | None = None,
    image_ai: StructuredAI | None = None,
    invoice_ai: StructuredAI | None = None,
    voice_catalogue_resolver: object | None = _AUTO_CATALOGUE_RESOLVER,
) -> FastAPI:
    settings = settings or Settings.from_env()
    store = store or build_repository(settings)
    app = FastAPI(title="Street CEO API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",  # Bundled Capacitor Android WebView origin.
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://192.168.10.213:5173",
        ],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.state.store = store
    app.state.voice_interpreter = voice_interpreter
    app.state.muse_ai = muse_ai
    app.state.social_ai = social_ai
    app.state.image_ai = image_ai
    app.state.invoice_ai = invoice_ai
    app.state.voice_catalogue_resolver = voice_catalogue_resolver
    if settings.local_team_enabled:
        try:
            from services.api.local_team import mount_local_team
        except ModuleNotFoundError as exc:
            raise RuntimeError("Local team view is enabled but its optional local modules are missing") from exc
        mount_local_team(app, settings)
    if settings.demo_seed_enabled and isinstance(store, InMemoryStore):
        if hasattr(store, "transaction") and hasattr(store, "path"):
            with store.transaction():
                app.state.demo_shop_id = str(store.seed_demo_shop())
        else:
            app.state.demo_shop_id = str(store.seed_demo_shop())
    if hasattr(store, "transaction") and hasattr(store, "path"):
        from services.api.sqlite_store import SQLiteTransactionMiddleware
        app.add_middleware(SQLiteTransactionMiddleware, store=store)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/demo/runtime")
    def demo_runtime() -> dict:
        import os
        from pathlib import Path
        is_sqlite = hasattr(store, "transaction") and hasattr(store, "path")
        database_path = Path(store.path).resolve() if is_sqlite else None
        return {
            "store_backend": "sqlite" if is_sqlite else ("memory" if isinstance(store, InMemoryStore) else "postgres"),
            "database_name": database_path.name if database_path else None,
            "database_identity": hashlib.sha256(str(database_path).encode("utf-8")).hexdigest() if database_path else None,
            "process_id": os.getpid(),
            "single_worker_demo": is_sqlite,
        }

    @app.get("/readyz")
    def readyz() -> dict[str, str]:
        try:
            store.check_ready()
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
        return {"status": "ready"}

    @app.post("/api/v1/dev/demo/reset", response_model=DemoResetResponse)
    def reset_demo_data() -> DemoResetResponse:
        """Reset the local seeded demo shop; never available in PostgreSQL mode."""
        if not settings.demo_seed_enabled or not isinstance(store, InMemoryStore):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="demo reset is disabled")
        shop_id = store.reset_demo_shop()
        app.state.demo_shop_id = str(shop_id)
        record = store.get_shop_record(shop_id)
        return DemoResetResponse(
            shop_id=shop_id, product_count=len(record.products),
            sales_count=len(record.idempotent_sales), invoice_count=len(record.invoices),
            expense_count=len(record.expenses), cost_audit_count=len(record.cost_audits),
        )

    def shop_scope(
        shop_id: UUID,
        x_shop_id: Annotated[UUID | None, Header()] = None,
    ) -> _ShopRecord:
        if x_shop_id != shop_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="shop scope mismatch")
        try:
            return store.get_shop_record(shop_id)
        except RepositoryNotFound as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="repository unavailable") from exc

    @app.get("/api/v1/shops/{shop_id}/investigations/requests")
    def recent_investigation_requests(
        record: _ShopRecord = Depends(shop_scope),
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        correlation_id: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    ) -> dict:
        from services.api.trace_reader import read_shop_traces
        try:
            return {"shop_id": str(record.shop.id), "events": read_shop_traces(str(record.shop.id), limit, correlation_id)}
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Request investigation logs are unavailable") from exc

    def voice_disabled() -> None:
        if not settings.voice_enabled:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="voice input is disabled")

    @app.get("/api/v1/shops/{shop_id}/reports/sales")
    def get_sales_report(record: _ShopRecord = Depends(shop_scope), start_date: date | None = None, end_date: date | None = None, preset: str | None = None, month: str | None = None) -> dict:
        from services.api.reports import sales_report
        try:
            return sales_report(record, start_date, end_date, preset, month)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/v1/shops/{shop_id}/cash-close/preview", response_model=CashClosePreview)
    def preview_cash_close(record: _ShopRecord = Depends(shop_scope), business_date: date | None = None) -> CashClosePreview:
        from services.api.cash_close import calculate_cash_preview
        business_date = business_date or datetime.now(ZoneInfo(record.shop.timezone)).date()
        return calculate_cash_preview(record, business_date)

    @app.get("/api/v1/shops/{shop_id}/cash-close/{business_date}", response_model=CashCloseRecord)
    def get_cash_close(business_date: date, record: _ShopRecord = Depends(shop_scope)) -> CashCloseRecord:
        item = record.cash_closes.get(business_date)
        if item is None:
            raise HTTPException(status_code=404, detail="cash close not found")
        return item

    @app.post("/api/v1/shops/{shop_id}/cash-close/opening", response_model=CashMovementRecord, status_code=201)
    def declare_cash_opening(request: CashOpeningCreate, record: _ShopRecord = Depends(shop_scope), idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> CashMovementRecord:
        from services.api.cash_close import calculate_cash_preview
        key = require_voice_key(idempotency_key)
        if not request.confirmed:
            raise HTTPException(status_code=409, detail="opening declaration requires explicit confirmation")
        fingerprint = hashlib.sha256(json.dumps(request.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
        previous = record.cash_movement_idempotency.get(key)
        if previous:
            if previous[0] != fingerprint:
                raise HTTPException(status_code=409, detail="opening idempotency key payload mismatch")
            return previous[1]
        if request.business_date in record.cash_closes or request.business_date in record.day_closes:
            raise HTTPException(status_code=409, detail="closed date cannot receive a replacement opening")
        preview = calculate_cash_preview(record, request.business_date)
        if not preview.requires_opening:
            raise HTTPException(status_code=409, detail="opening is already anchored; explicit corrections require separate review")
        if request.business_date > datetime.now(ZoneInfo(record.shop.timezone)).date():
            raise HTTPException(status_code=409, detail="future opening declaration is not supported")
        occurred_at = datetime.combine(request.business_date, datetime.min.time(), ZoneInfo(record.shop.timezone)).astimezone(timezone.utc)
        item = CashMovementRecord(id=uuid4(), shop_id=record.shop.id, kind="opening_balance", occurred_at=occurred_at, amount_cents=request.opening_cash_cents, tender="cash", actor=request.actor, reason=("Explicit late start-of-day opening declaration: " + request.reason)[:240], created_at=retail_utc_now())
        record.cash_movements[item.id] = item
        record.cash_movement_idempotency[key] = (fingerprint, item)
        return item

    @app.post("/api/v1/shops/{shop_id}/cash-close", response_model=CashCloseRecord, status_code=201)
    def post_cash_close(request: CashCloseCreate, record: _ShopRecord = Depends(shop_scope), idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> CashCloseRecord:
        from services.api.cash_close import calculate_cash_preview
        key = require_voice_key(idempotency_key)
        if not request.confirmed:
            raise HTTPException(status_code=409, detail="cash close requires explicit confirmation")
        fingerprint = hashlib.sha256(json.dumps(request.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
        previous = record.cash_close_idempotency.get(key)
        if previous:
            if previous[0] != fingerprint:
                raise HTTPException(status_code=409, detail="cash close idempotency key payload mismatch")
            return previous[1]
        if request.business_date in record.cash_closes or request.business_date in record.day_closes:
            raise HTTPException(status_code=409, detail={"code": "already_closed", "message": "Recover the saved close instead of submitting another count"})
        if request.business_date > datetime.now(ZoneInfo(record.shop.timezone)).date():
            raise HTTPException(status_code=409, detail="future cash close is not supported")
        preview = calculate_cash_preview(record, request.business_date)
        if preview.requires_opening or preview.expected_cash_cents is None:
            raise HTTPException(status_code=409, detail={"code": "opening_or_payment_required", "message": "Resolve opening/payment evidence before closing"})
        if request.preview_version != preview.preview_version:
            raise HTTPException(status_code=409, detail={"code": "stale_preview", "message": "Recorded movements changed; review the refreshed expected cash"})
        now = retail_utc_now()
        close_id = uuid4()
        data = preview.model_dump(exclude={"preview_version", "saved_close"})
        if request.cash_counted_cents != preview.expected_cash_cents:
            data["warnings"] = [*data["warnings"], "Counted cash differs from expected recorded cash; variance requires review."]
        item = CashCloseRecord(**data, id=close_id, audit_id=close_id, shop_id=record.shop.id, cash_counted_cents=request.cash_counted_cents, cash_variance_cents=request.cash_counted_cents-preview.expected_cash_cents, actor=request.actor, notes=request.notes, confirmed_at=now, as_of_cutoff=now, source_version=preview.preview_version)
        record.cash_closes[request.business_date] = item
        record.cash_close_idempotency[key] = (fingerprint, item)
        return item

    def voice_replay(record: _ShopRecord, key: str, fingerprint: str) -> VoiceResponse | None:
        previous = record.voice_requests.get(key)
        if previous is None:
            return None
        old_fingerprint, old_response = previous
        if old_fingerprint != fingerprint:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="idempotency key payload mismatch")
        return old_response

    def require_voice_key(idempotency_key: str | None) -> str:
        if not idempotency_key or not idempotency_key.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key is required")
        return idempotency_key.strip()

    def get_interpreter() -> object:
        if app.state.voice_interpreter is not None:
            return app.state.voice_interpreter
        try:
            from services.voice.meta_llama import build_meta_llama_interpreter
            return build_meta_llama_interpreter()
        except Exception:
            return None

    def resolve_catalogue_response(transcript: str, record: _ShopRecord, input_kind: str) -> VoiceResponse:
        """Uncertain matches are proposals only; never trust provider prices/IDs."""
        resolver = app.state.voice_catalogue_resolver
        catalogue = tuple({"product_id": str(product.id), "name": product.name, "sku": product.sku, "unit_price_cents": product.unit_price_cents, "stock_qty": product.stock_qty} for product in record.products.values())
        provider_called = False
        try:
            if resolver is _AUTO_CATALOGUE_RESOLVER:
                from services.ai.catalogue_voice import resolve_catalogue_voice
                resolver = resolve_catalogue_voice
            if resolver is None:
                raise RuntimeError("catalogue resolver disabled")
            resolution = resolver(transcript, catalogue)
            provider_called = bool(resolution.provider_called)
            source = resolution.source
            question = str(resolution.question or "Please say the quantity and catalogue name for every item.")[:1000]
            if resolution.status == "proposed":
                proposed = []
                used = set()
                for line in resolution.lines:
                    product_id = UUID(str(line.product_id))
                    quantity = line.quantity
                    product = record.products.get(product_id)
                    if product is None or product_id in used or isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0 or quantity > product.stock_qty:
                        raise ValueError("invalid catalogue proposal")
                    used.add(product_id)
                    proposed.append(VoiceSaleLine(product_id=product.id, product_name=product.name, quantity=quantity))
                if not proposed:
                    raise ValueError("empty catalogue proposal")
                question = "Did you mean " + ", ".join(f"{line.quantity} {line.product_name}" for line in proposed) + "? Please say yes or no."
                intent = VoiceIntent(action="record_sale", item=proposed[0].product_name, quantity=proposed[0].quantity, needs_confirmation=True)
                return VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind=input_kind, status="needs_match_confirmation", transcript=transcript, intent=intent, lines=proposed, requires_match_confirmation=True, clarification_question=question, resolution_source=source, provider_called=provider_called)
            clarification_product_id = getattr(resolution, "clarification_product_id", None)
            if clarification_product_id is not None:
                clarification_product_id = UUID(str(clarification_product_id))
                if resolution.reason != "missing_quantity" or clarification_product_id not in record.products:
                    raise ValueError("invalid clarification product")
            clarification_product = record.products.get(clarification_product_id) if clarification_product_id else None
            if clarification_product is not None:
                question = f"How many {clarification_product.name}? Say just the quantity."
            return VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind=input_kind, status="needs_clarification", transcript=transcript, clarification_question=question, error=question, error_code="quantity_required" if resolution.reason == "missing_quantity" else "product_not_found", clarification_code=resolution.reason, clarification_product_id=clarification_product_id, clarification_product_name=clarification_product.name if clarification_product else None, clarification_product_sku=clarification_product.sku if clarification_product else None, resolution_source=source, provider_called=provider_called)
        except Exception:
            question = "I could not confirm every product. Please say the quantity and exact catalogue name for every item, for example one Coke."
            return VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind=input_kind, status="needs_clarification", transcript=transcript, clarification_question=question, error=question, error_code="product_not_found", clarification_code="resolution_unavailable", resolution_source="unavailable", provider_called=provider_called)

    @app.post("/api/v1/shops/{shop_id}/voice/transcript", response_model=VoiceResponse)
    def interpret_voice_transcript(
        request: VoiceTranscriptRequest,
        record: _ShopRecord = Depends(shop_scope),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> VoiceResponse:
        voice_disabled()
        key = require_voice_key(idempotency_key)
        transcript = request.transcript.strip()
        transcript_payload = {"transcript": transcript}
        if request.clarification_of is not None:
            transcript_payload["clarification_of"] = str(request.clarification_of)
        fingerprint = request_fingerprint("transcript", transcript_payload).value
        replay = voice_replay(record, key, fingerprint)
        if replay is not None:
            return replay
        contextual = request.clarification_of is not None
        context_lines = None
        if contextual:
            previous = next((response for _, response in record.voice_requests.values() if response.request_id == request.clarification_of), None)
            if previous is None or previous.status != "needs_clarification":
                raise HTTPException(status_code=409, detail="clarification context is missing or not applicable")
            if previous.clarification_code == "missing_quantity":
                quantity = parse_quantity_reply(transcript)
                if quantity is not None and previous.clarification_product_id is not None:
                    product = record.products.get(previous.clarification_product_id)
                    if product is None:
                        raise HTTPException(status_code=409, detail="clarification product is no longer available")
                    if product.name != previous.clarification_product_name or product.sku != previous.clarification_product_sku:
                        raise HTTPException(status_code=409, detail="clarification product changed; please name the product again")
                    if quantity > product.stock_qty:
                        question = f"Only {product.stock_qty} {product.name} units are recorded in stock. What quantity do you want?"
                        response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="transcript", status="needs_clarification", transcript=previous.transcript, clarification_code="missing_quantity", clarification_product_id=product.id, clarification_product_name=product.name, clarification_product_sku=product.sku, clarification_question=question, error=question, error_code="insufficient_stock", resolution_source="local_clarification")
                        record.voice_requests[key] = (fingerprint, response)
                        return response
                    context_lines = [VoiceSaleLine(product_id=product.id, product_name=product.name, quantity=quantity)]
                    transcript = f"{quantity} {product.name}"
                elif quantity is not None:
                    # Old unstructured exact contexts remain compatible; noisy ones
                    # still use the validated resolver rather than guessing an ID.
                    transcript = transcript + " " + (previous.transcript or "")
        lines = context_lines if context_lines is not None else parse_catalogue_sale(transcript, record.products.values())
        if lines and contextual:
            question = "Did you mean " + ", ".join(f"{line.quantity} {line.product_name}" for line in lines) + "? Please say yes or no."
            intent = VoiceIntent(action="record_sale", item=lines[0].product_name, quantity=lines[0].quantity, needs_confirmation=True)
            response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="transcript", status="needs_match_confirmation", transcript=transcript, intent=intent, lines=lines, requires_match_confirmation=True, clarification_question=question, resolution_source="local_clarification")
            record.voice_requests[key] = (fingerprint, response)
            record.voice_reviews[response.request_id] = response
            return response
        if not lines and record.products:
            response = resolve_catalogue_response(transcript, record, "transcript")
            record.voice_requests[key] = (fingerprint, response)
            if response.status == "needs_match_confirmation" and response.lines:
                record.voice_reviews[response.request_id] = response
            return response
        if lines:
            first = lines[0]
            intent = VoiceIntent(action="record_sale", item=first.product_name, quantity=first.quantity, needs_confirmation=True)
            response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="transcript", status="needs_confirmation", transcript=transcript, intent=intent, lines=lines, resolution_source="catalogue_parser")
        else:
            interpreter = get_interpreter()
        if not lines and interpreter is None:
            response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="transcript", status="unavailable", transcript=transcript, error="AI understanding is not configured. Check the server model settings or use the catalogue format.", error_code="provider_unavailable")
        elif not lines:
            try:
                intent = normalize_intent(interpreter.interpret(transcript))
                response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="transcript", status="needs_confirmation" if intent.action == "record_sale" else "interpreted", transcript=transcript, intent=intent)
            except Exception:
                response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="transcript", status="rejected", transcript=transcript, error="I could not safely understand that command. Try a format such as ‘2 Coke 2 Sugar’.", error_code="invalid_or_unsafe_provider_response")
        record.voice_requests[key] = (fingerprint, response)
        if response.status == "needs_confirmation" and response.lines:
            record.voice_reviews[response.request_id] = response
        return response

    @app.post("/api/v1/shops/{shop_id}/voice/commit", response_model=Sale | VoiceTenderQuestion)
    def commit_voice_sale(
        request: VoiceSaleCommitRequest,
        record: _ShopRecord = Depends(shop_scope),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> Sale:
        """Commit only a previously reviewed voice basket through the sale path."""
        voice_disabled()
        key = require_voice_key(idempotency_key)
        commit_payload = request.model_dump(mode="json")
        if not request.match_confirmed:
            commit_payload.pop("match_confirmed", None)
        commit_fingerprint = hashlib.sha256(json.dumps(commit_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        committed = record.voice_review_commits.get(request.review_id)
        if committed is not None:
            original_key, original_fingerprint, original_sale = committed
            if key != original_key:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="voice review is already committed; retry with the original Idempotency-Key")
            if commit_fingerprint != original_fingerprint:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="idempotency key payload mismatch")
            return original_sale
        review = record.voice_reviews.get(request.review_id)
        if review is None or review.status not in {"needs_confirmation", "needs_match_confirmation"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="voice review is missing or already committed")
        if review.requires_match_confirmation and not request.match_confirmed:
            raise HTTPException(status_code=409, detail={"code": "match_confirmation_required", "question": review.clarification_question or "Please confirm the proposed catalogue products before payment."})
        expected = [(line.product_id, line.quantity) for line in review.lines]
        actual = [(line.product_id, line.quantity) for line in request.lines]
        if expected != actual:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="voice basket changed after review")
        products = []
        for line in request.lines:
            product = record.products.get(line.product_id)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")
            products.append(product)
        amount_due_cents = sum(product.unit_price_cents * line.quantity for product, line in zip(products, request.lines))
        if request.tender not in {"cash", "bank"}:
            return VoiceTenderQuestion(
                review_id=request.review_id,
                question="Should I record this sale as cash or bank?",
                amount_due_cents=amount_due_cents,
                missing=["tender"],
            )
        if request.tender == "cash" and request.amount_received_cents is None:
            return VoiceTenderQuestion(
                review_id=request.review_id,
                question=f"How much cash did you receive? The total is {record.shop.currency} {amount_due_cents / 100:.2f}.",
                amount_due_cents=amount_due_cents,
                missing=["amount_received_cents"],
            )
        if request.tender == "cash" and request.amount_received_cents < amount_due_cents:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "insufficient_cash",
                    "message": "Cash received is less than the sale total.",
                    "amount_due_cents": amount_due_cents,
                    "amount_received_cents": request.amount_received_cents,
                },
            )
        if request.tender == "bank" and request.amount_received_cents not in {None, amount_due_cents}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "invalid_bank_amount", "message": "Bank payment amount must equal the sale total.", "amount_due_cents": amount_due_cents})
        amount_received_cents = request.amount_received_cents if request.tender == "cash" else amount_due_cents
        change_cents = amount_received_cents - amount_due_cents if request.tender == "cash" else 0
        sale_request = SaleCreate(
            lines=[SaleLine(product_id=line.product_id, quantity=line.quantity) for line in request.lines],
            tender=request.tender,
        )
        fingerprint = hashlib.sha256(json.dumps({"sale": sale_request.model_dump(mode="json"), "amount_received_cents": amount_received_cents, "change_cents": change_cents}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        try:
            sale = store.create_sale(record, sale_request, fingerprint, key, amount_received_cents, change_cents)
            record.voice_sale_ids.add(sale.id)
            record.voice_review_commits[request.review_id] = (key, commit_fingerprint, sale)
            return sale
        except RepositoryIdempotencyConflict as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except RepositoryNotFound as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except RepositoryInsufficientStock as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="repository unavailable") from exc

    @app.post("/api/v1/shops/{shop_id}/voice/commit/{sale_id}/undo", response_model=VoiceSaleReversal, status_code=status.HTTP_201_CREATED)
    def undo_voice_sale(
        sale_id: UUID,
        request: VoiceSaleUndoRequest,
        record: _ShopRecord = Depends(shop_scope),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> VoiceSaleReversal:
        """Reverse one committed Apo sale with an explicit, audited action."""
        voice_disabled()
        key = require_voice_key(idempotency_key)
        fingerprint = hashlib.sha256(json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        previous = record.voice_reversal_idempotency.get(key)
        if previous:
            old_fingerprint, old_reversal = previous
            if old_fingerprint != fingerprint:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="voice reversal idempotency key payload mismatch")
            return old_reversal
        if not request.confirmed:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="voice reversal requires explicit confirmation")
        if sale_id not in record.voice_sale_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="voice sale receipt not found")
        sale = next((item for _, item in record.idempotent_sales.values() if item.id == sale_id), None)
        if sale is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="voice sale receipt not found")
        if sale_id in record.voice_sale_reversals:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="voice sale is already reversed")
        for line in sale.lines:
            product = record.products.get(line.product_id)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="voice sale product no longer exists")
        for line in sale.lines:
            record.products[line.product_id].stock_qty += line.quantity
        reversal_id = uuid4()
        reversal = VoiceSaleReversal(
            reversal_id=reversal_id, audit_id=reversal_id, original_sale_id=sale.id,
            shop_id=record.shop.id, lines=[VoiceSaleCommitLine(product_id=line.product_id, quantity=line.quantity) for line in sale.lines],
            actor=request.actor, reason=request.reason, created_at=datetime.now(timezone.utc),
        )
        record.voice_sale_reversals[sale_id] = reversal
        record.voice_reversal_idempotency[key] = (fingerprint, reversal)
        return reversal

    @app.post("/api/v1/shops/{shop_id}/voice/audio", response_model=VoiceResponse)
    def accept_voice_audio(
        request: VoiceAudioRequest,
        record: _ShopRecord = Depends(shop_scope),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> VoiceResponse:
        voice_disabled()
        key = require_voice_key(idempotency_key)
        try:
            decoded = decode_audio(request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        fingerprint = audio_fingerprint(request, decoded).value
        replay = voice_replay(record, key, fingerprint)
        if replay is not None:
            return replay
        try:
            from services.voice.meta_voice import build_meta_voice_transcriber
            from services.voice.meta_llama import build_meta_llama_interpreter
            transcript = build_meta_voice_transcriber().transcribe(decoded, request.media_type)
            lines = parse_catalogue_sale(transcript, record.products.values())
            if lines:
                first = lines[0]
                intent = VoiceIntent(action="record_sale", item=first.product_name, quantity=first.quantity, needs_confirmation=True)
                response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="audio", status="needs_confirmation", transcript=transcript, intent=intent, lines=lines, resolution_source="catalogue_parser")
            elif record.products:
                response = resolve_catalogue_response(transcript, record, "audio")
            else:
                intent = normalize_intent(build_meta_llama_interpreter().interpret(transcript))
                response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="audio", status="interpreted", transcript=transcript, intent=intent)
        except Exception:
            response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="audio", status="unavailable", error="audio_transcription_unavailable")
        if response.status in {"needs_confirmation", "needs_match_confirmation"} and response.lines:
            record.voice_reviews[response.request_id] = response
        record.voice_requests[key] = (fingerprint, response)
        return response

    @app.post("/api/v1/shops/{shop_id}/invoices", response_model=InvoiceUpload, status_code=status.HTTP_201_CREATED)
    def upload_invoice(
        record: _ShopRecord = Depends(shop_scope),
        invoice: UploadFile = File(...),
    ) -> InvoiceUpload:
        contents = invoice.file.read()
        if not contents:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invoice file is empty")
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="invoice file exceeds 10 MiB")
        content_type = (invoice.content_type or "").split(";", 1)[0].strip().lower()
        allowed_types = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
        if content_type not in allowed_types:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invoice must be a PDF or JPEG/PNG/WEBP image")
        try:
            filename = validate_image_filename(invoice.filename or "invoice")
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        encoded = base64.b64encode(contents).decode("ascii")
        document_ref = f"data:{content_type};base64,{encoded}"
        catalogue = tuple(
            InvoiceCatalogueProduct(str(product.id), product.sku, product.name)
            for product in record.products.values()
        )
        extraction = (app.state.invoice_ai or build_invoice_vision_ai()).invoice_extract(
            InvoiceImageRequest(document_ref, content_type, filename, catalogue=catalogue)
        )
        # The adapter is review-only. Build the complete record and all line
        # drafts before publishing either one to the store.
        extraction_value = extraction.value
        extracted_lines: list[InvoiceLineDraft] = []
        if extraction_value.status == "review_required" and extraction_value.review_only:
            for line in extraction_value.lines:
                if line.line_total_minor is None:
                    continue
                unit_cost_micros = (line.line_total_minor * 10_000) // line.quantity
                extracted_lines.append(InvoiceLineDraft(
                    id=uuid4(), description=line.description, sku=line.sku,
                    quantity=line.quantity, line_total_cents=line.line_total_minor,
                    calculated_unit_cost_micros=unit_cost_micros,
                    suggested_product_id=UUID(line.suggested_product_id) if line.suggested_product_id else None,
                    matched_product_id=None, match_status="suggested" if line.suggested_product_id else "unmatched",
                    source="ocr_provider", evidence_ref="invoice-vision",
                ))
        invoice_id = uuid4()
        provider_review = extraction.source == "provider" and extraction_value.status == "review_required" and extraction_value.review_only
        status_value = "needs_review" if provider_review else "provider_unavailable"
        source_value = "ocr_provider" if provider_review else "none"
        warnings = list(extraction_value.warnings)
        if not warnings and not provider_review:
            warnings = ["No OCR provider is configured; no line items were inferred from the file."]
        item = InvoiceUpload(
            id=invoice_id,
            shop_id=record.shop.id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(contents),
            sha256=hashlib.sha256(contents).hexdigest(),
            storage_ref=f"memory://invoices/{invoice_id}",
            extraction_status=status_value,
            extraction_source=source_value,
            lines=extracted_lines,
            warnings=warnings,
            uploaded_at=utc_now(),
        )
        record.invoices[invoice_id] = item
        record.invoice_bytes[invoice_id] = contents
        return item

    @app.get("/api/v1/shops/{shop_id}/invoices", response_model=list[InvoiceUpload])
    def list_invoices(record: _ShopRecord = Depends(shop_scope)) -> list[InvoiceUpload]:
        return sorted(record.invoices.values(), key=lambda item: item.uploaded_at, reverse=True)

    @app.get("/api/v1/shops/{shop_id}/invoices/{invoice_id}", response_model=InvoiceUpload)
    def get_invoice(invoice_id: UUID, record: _ShopRecord = Depends(shop_scope)) -> InvoiceUpload:
        item = record.invoices.get(invoice_id)
        if item is None or item.shop_id != record.shop.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invoice not found")
        return item

    @app.post("/api/v1/shops/{shop_id}/invoices/{invoice_id}/review", response_model=InvoiceUpload)
    def review_invoice(
        invoice_id: UUID,
        request: InvoiceReviewRequest,
        record: _ShopRecord = Depends(shop_scope),
    ) -> InvoiceUpload:
        item = record.invoices.get(invoice_id)
        if item is None or item.shop_id != record.shop.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invoice not found")
        if item.extraction_status == "confirmed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="confirmed invoice cannot be reviewed")
        reviewed_lines: list[InvoiceLineDraft] = []
        for line in request.lines:
            product = record.products.get(line.product_id) if line.product_id else None
            if line.product_id is not None and product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="review product not found in shop")
            exact_sku = next((candidate for candidate in record.products.values() if line.sku and candidate.sku.lower() == line.sku.lower()), None)
            exact_name = [candidate for candidate in record.products.values() if candidate.name.lower() == line.description.lower()]
            suggested = product or exact_sku or (exact_name[0] if len(exact_name) == 1 else None)
            unit_cost_micros = (line.line_total_cents * 10_000) // line.quantity
            warnings = item.warnings[:]
            if (line.line_total_cents * 10_000) % line.quantity:
                warnings.append(f"unit cost rounded down for {line.description}")
            reviewed_lines.append(InvoiceLineDraft(
                id=uuid4(), description=line.description, sku=line.sku,
                quantity=line.quantity, line_total_cents=line.line_total_cents,
                calculated_unit_cost_micros=unit_cost_micros,
                suggested_product_id=suggested.id if suggested else None,
                matched_product_id=product.id if product else None,
                match_status="accepted" if product else ("suggested" if suggested else "unmatched"),
                source=request.source, evidence_ref=request.evidence_ref,
            ))
        item.lines = reviewed_lines
        item.extraction_status = "needs_review"
        item.extraction_source = request.source
        item.warnings = sorted(set(item.warnings + ["Review every line and explicitly match products before confirming."]))
        return item

    @app.post("/api/v1/shops/{shop_id}/invoices/{invoice_id}/confirm", response_model=InvoiceConfirmation)
    def confirm_invoice(
        invoice_id: UUID,
        record: _ShopRecord = Depends(shop_scope),
    ) -> InvoiceConfirmation:
        item = record.invoices.get(invoice_id)
        if item is None or item.shop_id != record.shop.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invoice not found")
        if item.extraction_status != "needs_review":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="invoice must be reviewed before confirmation")
        if not item.lines or any(line.match_status != "accepted" or line.matched_product_id is None for line in item.lines):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="every invoice line needs an explicit product match before confirmation")
        warnings: list[str] = []
        applied: list[UUID] = []
        for line in item.lines:
            product = record.products.get(line.matched_product_id)
            if product is None or line.calculated_unit_cost_micros is None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="reviewed product or calculated unit cost is missing")
            before_qty = product.stock_qty
            previous_cost = product.unit_cost_micros
            if previous_cost is None:
                new_cost = line.calculated_unit_cost_micros
                if before_qty:
                    warnings.append(f"historical cost missing for {product.sku}; new receipt cost does not reconstruct prior stock")
            else:
                new_cost = ((before_qty * previous_cost) + (line.quantity * line.calculated_unit_cost_micros)) // (before_qty + line.quantity)
            product.stock_qty += line.quantity
            product.unit_cost_micros = new_cost
            product.cost_source_invoice_id = item.id
            record.cost_audits.append(ProductCostAudit(
                id=uuid4(), shop_id=record.shop.id, product_id=product.id,
                invoice_id=item.id, quantity_received=line.quantity,
                source_type="invoice_receipt", source_ref=item.storage_ref,
                actor="invoice_confirmation", reason="confirmed supplier invoice receipt",
                effective_date=item.uploaded_at.date(),
                unit_cost_micros=line.calculated_unit_cost_micros,
                previous_unit_cost_micros=previous_cost, new_unit_cost_micros=new_cost,
                stock_before=before_qty, stock_after=product.stock_qty, recorded_at=utc_now(),
            ))
            applied.append(line.id)
        confirmed_at = utc_now()
        item.extraction_status = "confirmed"
        item.confirmed_at = confirmed_at
        return InvoiceConfirmation(
            invoice_id=item.id, shop_id=record.shop.id, applied_line_ids=applied,
            stock_units_added=sum(line.quantity for line in item.lines),
            cost_updates=len(applied), warnings=sorted(set(warnings)), confirmed_at=confirmed_at,
        )

    @app.get("/api/v1/shops/{shop_id}/products/{product_id}/cost-history", response_model=list[ProductCostAudit])
    def product_cost_history(product_id: UUID, record: _ShopRecord = Depends(shop_scope)) -> list[ProductCostAudit]:
        if product_id not in record.products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found in shop")
        return [audit for audit in record.cost_audits if audit.product_id == product_id]

    @app.post("/api/v1/shops/{shop_id}/products/{product_id}/cost-corrections", response_model=ProductCostCorrection, status_code=status.HTTP_201_CREATED)
    def create_product_cost_correction(
        product_id: UUID,
        request: ProductCostCorrectionCreate,
        record: _ShopRecord = Depends(shop_scope),
    ) -> ProductCostCorrection:
        if product_id not in record.products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found in shop")
        item = ProductCostCorrection(
            id=uuid4(), shop_id=record.shop.id, product_id=product_id,
            unit_cost_micros=request.resolved_unit_cost_micros(),
            effective_date=request.effective_date, reason=request.reason,
            source_ref=request.source_ref, actor=request.actor,
            created_at=utc_now(),
        )
        record.cost_corrections[item.id] = item
        return item

    @app.post("/api/v1/shops/{shop_id}/products/{product_id}/cost-corrections/{correction_id}/confirm", response_model=ProductCostCorrection)
    def confirm_product_cost_correction(
        product_id: UUID,
        correction_id: UUID,
        record: _ShopRecord = Depends(shop_scope),
    ) -> ProductCostCorrection:
        product = record.products.get(product_id)
        item = record.cost_corrections.get(correction_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found in shop")
        if item is None or item.shop_id != record.shop.id or item.product_id != product_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cost correction not found")
        if item.status != "draft":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cost correction is not a draft")
        previous_cost = product.unit_cost_micros
        stock_before = product.stock_qty
        product.unit_cost_micros = item.unit_cost_micros
        product.cost_source_invoice_id = None
        item.status = "confirmed"
        item.confirmed_at = utc_now()
        record.cost_audits.append(ProductCostAudit(
            id=uuid4(), shop_id=record.shop.id, product_id=product_id,
            source_type="direct_correction", source_ref=item.source_ref,
            actor=item.actor, reason=item.reason, effective_date=item.effective_date,
            quantity_received=0, unit_cost_micros=item.unit_cost_micros,
            previous_unit_cost_micros=previous_cost, new_unit_cost_micros=item.unit_cost_micros,
            stock_before=stock_before, stock_after=product.stock_qty, recorded_at=item.confirmed_at,
        ))
        return item

    @app.post("/api/v1/shops/{shop_id}/expenses", response_model=ExpenseRecord, status_code=status.HTTP_201_CREATED)
    def create_expense(request: ExpenseCreate, record: _ShopRecord = Depends(shop_scope)) -> ExpenseRecord:
        item = ExpenseRecord(id=uuid4(), shop_id=record.shop.id, created_at=utc_now(), **request.model_dump())
        record.expenses[item.id] = item
        return item

    @app.get("/api/v1/shops/{shop_id}/expenses", response_model=list[ExpenseRecord])
    def list_expenses(record: _ShopRecord = Depends(shop_scope)) -> list[ExpenseRecord]:
        return sorted(record.expenses.values(), key=lambda item: item.occurred_on, reverse=True)

    @app.post("/api/v1/shops/{shop_id}/expenses/{expense_id}/confirm", response_model=ExpenseRecord)
    def confirm_expense(expense_id: UUID, record: _ShopRecord = Depends(shop_scope)) -> ExpenseRecord:
        item = record.expenses.get(expense_id)
        if item is None or item.shop_id != record.shop.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="expense not found")
        if item.status != "draft":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="expense is not a draft")
        item.status = "confirmed"
        item.confirmed_at = utc_now()
        return item

    @app.post("/api/v1/shops/{shop_id}/products/{product_id}/image", response_model=ProductImageMetadata, status_code=status.HTTP_201_CREATED)
    def upload_product_image(
        product_id: UUID,
        record: _ShopRecord = Depends(shop_scope),
        image: UploadFile = File(...),
    ) -> ProductImageMetadata:
        if product_id not in record.products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found in shop")
        try:
            filename = validate_image_filename(image.filename or "")
            content_type = validate_image_content_type(image.content_type or "")
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        contents = image.file.read()
        if not contents:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="image file is empty")
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="image file exceeds 10 MiB")
        image_id = uuid4()
        item = ProductImageMetadata(
            id=image_id,
            shop_id=record.shop.id,
            product_id=product_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(contents),
            sha256=hashlib.sha256(contents).hexdigest(),
            storage_backend="memory",
            storage_ref=f"memory://product-images/{image_id}",
            uploaded_at=datetime.now(timezone.utc),
        )
        record.product_images[image_id] = item
        record.product_image_bytes[image_id] = contents
        return item

    @app.get("/api/v1/shops/{shop_id}/products/{product_id}/image", response_model=ProductImageMetadata)
    def get_product_image(product_id: UUID, record: _ShopRecord = Depends(shop_scope)) -> ProductImageMetadata:
        if product_id not in record.products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found in shop")
        item = next((image for image in reversed(list(record.product_images.values())) if image.product_id == product_id), None)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product image not found")
        return item

    @app.post("/api/v1/shops/{shop_id}/social/draft", response_model=SocialDraftResponse)
    def request_social_draft(
        request: SocialDraftRequest,
        record: _ShopRecord = Depends(shop_scope),
    ) -> SocialDraftResponse:
        source_ref = _memory_image_ref(record, request.source_image_id)
        if request.source_image_id is not None:
            source = record.product_images.get(request.source_image_id)
            if source is None or source.product_id not in request.product_ids:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source image not found for selected products")
        products = _social_products(record, request.product_ids)
        result = (app.state.social_ai or build_muse_ai()).social_draft(
            SocialRequest(request.brief, products, shop_image_ref=source_ref, duration_seconds=request.duration_seconds)
        )
        draft = result.value
        claims = [SocialClaimResponse(product_id=claim.product_id, claim=claim.claim, source_field=claim.source_field) for claim in draft.claims]
        return SocialDraftResponse(
            id=uuid4(), shop_id=record.shop.id, title=draft.title, caption=draft.caption,
            voiceover_script=draft.voiceover_script, shot_list=list(draft.shot_list),
            selected_product_ids=[UUID(value) for value in draft.selected_product_ids],
            claims=claims, status=draft.status, source=result.source,
            provider="meta_muse_text" if result.source == "provider" else "none",
            warnings=[result.reason] if result.reason else [], created_at=datetime.now(timezone.utc),
        )

    @app.post("/api/v1/shops/{shop_id}/social/image-generation", response_model=SocialImageGenerationResponse)
    def request_social_image_generation(
        request: SocialImageGenerationRequest,
        record: _ShopRecord = Depends(shop_scope),
    ) -> SocialImageGenerationResponse:
        source_ref = _memory_image_ref(record, request.source_image_id)
        if request.source_image_id is not None:
            source = record.product_images.get(request.source_image_id)
            if source is None or source.product_id not in request.product_ids:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source image not found for selected products")
        products = _social_products(record, request.product_ids)
        size = {"1:1": "1024x1024", "4:5": "1024x1536", "9:16": "1024x1536", "16:9": "1536x1024"}[request.aspect_ratio]
        result = (app.state.image_ai or build_muse_image_ai()).social_image(
            SocialImageRequest(request.brief, products, shop_image_ref=source_ref, size=size, output_format="png")
        )
        draft = result.value
        image_refs = list(draft.image_refs)
        item = SocialImageGenerationResponse(
            id=uuid4(), shop_id=record.shop.id, product_ids=request.product_ids,
            source_image_id=request.source_image_id, brief=request.brief,
            aspect_ratio=request.aspect_ratio, status=draft.status,
            provider=draft.provider, model=draft.model, image_refs=image_refs,
            warnings=list(draft.warnings), draft_only=draft.draft_only,
            output_url=image_refs[0] if image_refs else None,
            created_at=datetime.now(timezone.utc),
        )
        record.social_image_generations[item.id] = item
        return item

    @app.get("/api/v1/shops/{shop_id}/social/image-generation/{generation_id}", response_model=SocialImageGenerationResponse)
    def get_social_image_generation(generation_id: UUID, record: _ShopRecord = Depends(shop_scope)) -> SocialImageGenerationResponse:
        item = record.social_image_generations.get(generation_id)
        if item is None or item.shop_id != record.shop.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="image generation not found")
        return item

    @app.post("/shops", response_model=Shop, status_code=status.HTTP_201_CREATED)
    def create_shop(request: ShopCreate) -> Shop:
        try:
            return store.create_shop(request)
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="repository unavailable") from exc

    @app.get("/shops/{shop_id}", response_model=Shop)
    def get_shop(record: _ShopRecord = Depends(shop_scope)) -> Shop:
        return record.shop

    @app.get("/shops/{shop_id}/summary", response_model=ShopSummary)
    def get_summary(record: _ShopRecord = Depends(shop_scope)) -> ShopSummary:
        today = datetime.now(timezone.utc).date()
        todays_sales = [sale for _, sale in record.idempotent_sales.values() if sale.created_at.date() == today]
        total = sum(sale.total_cents for sale in todays_sales)
        low_stock = sum(1 for product in record.products.values() if product.stock_qty < 8)
        fastest = min(record.products.values(), key=lambda product: product.stock_qty, default=None)
        insight = (
            f"{fastest.name} is running low at {fastest.stock_qty} units. Review stock before the next rush."
            if fastest and fastest.stock_qty < 8 else
            "Stock is holding steady. Keep recording sales to build today’s live picture."
        )
        return ShopSummary(sales_total_cents=total, transaction_count=len(todays_sales), low_stock_count=low_stock, sales_change_percent=None, insight=insight)

    @app.post("/api/v1/shops/{shop_id}/purchases", response_model=PurchaseRecord, status_code=status.HTTP_201_CREATED)
    def create_purchase(request: PurchaseCreate, record: _ShopRecord = Depends(shop_scope)) -> PurchaseRecord:
        if request.kind == "invoice" and any(item.kind == "invoice" and item.reference.lower() == request.reference.lower() for item in record.purchases.values()):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="invoice reference already exists for shop")
        item = PurchaseRecord(id=uuid4(), shop_id=record.shop.id, created_at=retail_utc_now(), **request.model_dump())
        record.purchases[item.id] = item
        return item

    @app.get("/api/v1/shops/{shop_id}/purchases/{purchase_id}", response_model=PurchaseRecord)
    def get_purchase(purchase_id: UUID, record: _ShopRecord = Depends(shop_scope)) -> PurchaseRecord:
        item = record.purchases.get(purchase_id)
        if item is None or item.shop_id != record.shop.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="purchase not found")
        return item

    @app.post("/api/v1/shops/{shop_id}/purchases/{purchase_id}/confirm", response_model=PurchaseConfirmation)
    def confirm_purchase(purchase_id: UUID, record: _ShopRecord = Depends(shop_scope)) -> PurchaseConfirmation:
        item = record.purchases.get(purchase_id)
        if item is None or item.shop_id != record.shop.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="purchase not found")
        if item.status == "confirmed":
            previous = record.purchase_confirmations.get(item.id)
            if previous is not None:
                return previous
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="purchase confirmation is unavailable")
        staged_products: list[Product] = []
        staged_updates: list[tuple[Product, int, int, PurchaseLineResult, ProductCostAudit]] = []
        reserved_skus = {product.sku.lower() for product in record.products.values()}
        for line in item.lines:
            product = record.products.get(line.product_id) if line.product_id else None
            if line.product_id and product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="purchase product not found in shop")
            if product is None:
                if not line.sku or not line.name or line.unit_price_cents is None:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="new purchase product requires sku, name, and unit price")
                if line.sku.lower() in reserved_skus:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="purchase SKU already exists")
                product = Product(id=uuid4(), shop_id=record.shop.id, sku=line.sku, name=line.name, unit_price_cents=line.unit_price_cents, stock_qty=0)
                staged_products.append(product)
                reserved_skus.add(line.sku.lower())
            before_qty = product.stock_qty
            previous_cost = product.unit_cost_micros
            new_qty = before_qty + line.quantity
            new_cost = line.purchase_unit_cost_micros if previous_cost is None else ((before_qty * previous_cost) + (line.quantity * line.purchase_unit_cost_micros)) // new_qty
            change = None if previous_cost is None else new_cost - previous_cost
            insight = "baseline_established" if previous_cost is None else ("cost_increased" if change and change > 0 else "cost_decreased" if change and change < 0 else "cost_unchanged")
            audit = ProductCostAudit(
                id=uuid4(), shop_id=record.shop.id, product_id=product.id, source_type="purchase",
                source_ref=item.reference, actor=item.actor, reason=f"confirmed {item.kind} purchase",
                effective_date=item.purchase_date, quantity_received=line.quantity,
                unit_cost_micros=line.purchase_unit_cost_micros, previous_unit_cost_micros=previous_cost,
                new_unit_cost_micros=new_cost, stock_before=before_qty, stock_after=new_qty,
                recorded_at=retail_utc_now(),
            )
            result = PurchaseLineResult(
                product_id=product.id, quantity_received=line.quantity, stock_before=before_qty,
                stock_after=new_qty, purchase_unit_cost_micros=line.purchase_unit_cost_micros,
                previous_unit_cost_micros=previous_cost, new_average_unit_cost_micros=new_cost,
                cost_change_micros=change, insight=insight,
            )
            staged_updates.append((product, new_qty, new_cost, result, audit))
        # All validation and audit objects are complete before any shop state changes.
        for product in staged_products:
            record.products[product.id] = product
        results: list[PurchaseLineResult] = []
        audits: list[ProductCostAudit] = []
        for product, new_qty, new_cost, result, audit in staged_updates:
            product.stock_qty = new_qty
            product.unit_cost_micros = new_cost
            results.append(result)
            audits.append(audit)
        record.cost_audits.extend(audits)
        confirmed_at = retail_utc_now()
        item.status = "confirmed"
        item.confirmed_at = confirmed_at
        insights = [
            f"{result.insight}: product {result.product_id} purchase cost basis updated"
            for result in results
        ]
        confirmation = PurchaseConfirmation(
            purchase_id=item.id, shop_id=record.shop.id, total_cost_micros=item.total_cost_micros,
            lines=results, insights=insights, confirmed_at=confirmed_at,
        )
        record.purchase_confirmations[item.id] = confirmation
        return confirmation

    @app.post("/api/v1/shops/{shop_id}/stock-takes", response_model=StockTakeRecord, status_code=status.HTTP_201_CREATED)
    def create_stock_take(request: StockTakeCreate, record: _ShopRecord = Depends(shop_scope)) -> StockTakeRecord:
        for line in request.lines:
            if line.product_id not in record.products:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stock-take product not found in shop")
        expected_snapshot = {line.product_id: record.products[line.product_id].stock_qty for line in request.lines}
        item = StockTakeRecord(id=uuid4(), shop_id=record.shop.id, created_at=retail_utc_now(), expected_snapshot=expected_snapshot, **request.model_dump())
        record.stock_takes[item.id] = item
        return item

    @app.get("/api/v1/shops/{shop_id}/stock-takes/{stock_take_id}", response_model=StockTakeRecord)
    def get_stock_take(stock_take_id: UUID, record: _ShopRecord = Depends(shop_scope)) -> StockTakeRecord:
        item = record.stock_takes.get(stock_take_id)
        if item is None or item.shop_id != record.shop.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stock take not found")
        return item

    @app.post("/api/v1/shops/{shop_id}/stock-takes/{stock_take_id}/confirm", response_model=StockTakeConfirmation)
    def confirm_stock_take(stock_take_id: UUID, record: _ShopRecord = Depends(shop_scope)) -> StockTakeConfirmation:
        item = record.stock_takes.get(stock_take_id)
        if item is None or item.shop_id != record.shop.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stock take not found")
        if item.status == "confirmed":
            previous = record.stock_take_confirmations.get(item.id)
            if previous is not None:
                return previous
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="stock-take confirmation is unavailable")
        conflicts = [
            line.product_id for line in item.lines
            if record.products.get(line.product_id) is None
            or record.products[line.product_id].stock_qty != item.expected_snapshot.get(line.product_id)
        ]
        if conflicts:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="stock take baseline conflict; refresh and review before confirming")
        adjustments: list[StockAdjustmentAudit] = []
        for line in item.lines:
            product = record.products.get(line.product_id)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stock-take product not found in shop")
            expected = product.stock_qty
            if expected == line.counted_qty:
                continue
            product.stock_qty = line.counted_qty
            adjustments.append(StockAdjustmentAudit(
                id=uuid4(), stock_take_id=item.id, shop_id=record.shop.id, product_id=product.id,
                expected_qty=expected, counted_qty=line.counted_qty, adjustment_qty=line.counted_qty - expected,
                actor=item.actor, reason=f"confirmed {item.mode} stock take", recorded_at=retail_utc_now(),
            ))
        confirmed_at = retail_utc_now()
        item.status = "confirmed"
        item.confirmed_at = confirmed_at
        record.stock_adjustments.extend(adjustments)
        confirmation = StockTakeConfirmation(stock_take_id=item.id, shop_id=record.shop.id, adjustments=adjustments, confirmed_at=confirmed_at)
        record.stock_take_confirmations[item.id] = confirmation
        return confirmation

    def _day_close_breakdown(record: _ShopRecord, business_date: date) -> dict[str, int | str]:
        zone = ZoneInfo(record.shop.timezone)
        start = datetime.combine(business_date, datetime.min.time(), tzinfo=zone).astimezone(timezone.utc)
        end = datetime.combine(business_date + timedelta(days=1), datetime.min.time(), tzinfo=zone).astimezone(timezone.utc)

        def during(value: datetime) -> bool:
            normalized = value.astimezone(timezone.utc)
            return start <= normalized < end

        opening = {"cash": 0, "bank": 0}
        refunds = {"cash": 0, "bank": 0}
        adjustments = {"cash": 0, "bank": 0}
        for movement in record.cash_movements.values():
            tender = movement.tender
            if movement.kind == "opening_balance" and movement.occurred_at < start:
                opening[tender] += movement.amount_cents
            elif movement.kind == "refund" and during(movement.occurred_at):
                refunds[tender] += movement.amount_cents
            elif movement.kind == "adjustment" and during(movement.occurred_at):
                adjustments[tender] += movement.amount_cents
        sales = {"cash": 0, "bank": 0}
        for sale in (sale for _, sale in record.idempotent_sales.values() if during(sale.created_at)):
            sales[sale.tender] += sale.total_cents
        expenses = {"cash": 0, "bank": 0}
        for expense in record.expenses.values():
            if expense.status == "confirmed" and expense.occurred_on == business_date and expense.tender in expenses:
                expenses[expense.tender] += expense.amount_cents
        purchases = {"cash": 0, "bank": 0}
        for purchase in record.purchases.values():
            if purchase.status == "confirmed" and purchase.purchase_date == business_date and purchase.tender in purchases:
                purchases[purchase.tender] += purchase.total_cost_micros // 10_000
        from services.api.cash_close import calculate_cash_preview
        cash_preview = calculate_cash_preview(record, business_date)
        if cash_preview.opening_cash_cents is None or cash_preview.expected_cash_cents is None:
            raise HTTPException(status_code=409, detail="Opening/payment evidence is missing; use the cash-close preview and explicit opening declaration")
        opening["cash"] = cash_preview.opening_cash_cents
        sales["cash"] = cash_preview.sales_cash_cents
        expenses["cash"] = cash_preview.paid_expenses_cash_cents
        purchases["cash"] = cash_preview.paid_purchases_cash_cents
        refunds["cash"] = cash_preview.refunds_cash_cents
        adjustments["cash"] = cash_preview.adjustments_cash_cents
        return {
            "opening_cash_cents": opening["cash"], "opening_bank_card_cents": opening["bank"],
            "sales_cash_cents": sales["cash"], "sales_bank_card_cents": sales["bank"],
            "paid_expenses_cash_cents": expenses["cash"], "paid_expenses_bank_card_cents": expenses["bank"],
            "paid_purchases_cash_cents": purchases["cash"], "paid_purchases_bank_card_cents": purchases["bank"],
            "refunds_cash_cents": refunds["cash"], "refunds_bank_card_cents": refunds["bank"],
            "adjustments_cash_cents": adjustments["cash"], "adjustments_bank_card_cents": adjustments["bank"],
            "expected_cash_cents": opening["cash"] + sales["cash"] - expenses["cash"] - purchases["cash"] - refunds["cash"] + adjustments["cash"],
            "expected_bank_card_cents": opening["bank"] + sales["bank"] - expenses["bank"] - purchases["bank"] - refunds["bank"] + adjustments["bank"],
            "shop_timezone": record.shop.timezone,
            "warnings": [warning for warning in cash_preview.warnings if not warning.startswith("Bank/card")] + ["Legacy bank/card figures are recorded-movement estimates, not verified settlement; use cash-only close when bank is uncounted."],
        }

    @app.post("/api/v1/shops/{shop_id}/cash-movements", response_model=CashMovementRecord, status_code=status.HTTP_201_CREATED)
    def create_cash_movement(
        request: CashMovementCreate,
        record: _ShopRecord = Depends(shop_scope),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> CashMovementRecord:
        if not idempotency_key or not idempotency_key.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key is required")
        key = idempotency_key.strip()
        fingerprint = hashlib.sha256(json.dumps(request.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
        previous = record.cash_movement_idempotency.get(key)
        if previous:
            old_fingerprint, old_record = previous
            if old_fingerprint != fingerprint:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cash movement idempotency key payload mismatch")
            return old_record
        if request.tender == "cash" and request.kind == "opening_balance":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="New cash opening balances require explicit confirmation through /cash-close/opening")
        if request.tender == "cash" and request.occurred_at > retail_utc_now():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Actual cash movements cannot have a future occurred_at")
        item = CashMovementRecord(id=uuid4(), shop_id=record.shop.id, created_at=retail_utc_now(), **request.model_dump())
        record.cash_movements[item.id] = item
        record.cash_movement_idempotency[key] = (fingerprint, item)
        return item

    @app.get("/api/v1/shops/{shop_id}/day-close/preview", response_model=DayClosePreview)
    def preview_day_close(business_date: date, record: _ShopRecord = Depends(shop_scope)) -> DayClosePreview:
        breakdown = _day_close_breakdown(record, business_date)
        return DayClosePreview(business_date=business_date, **breakdown)

    @app.get("/api/v1/shops/{shop_id}/day-close/{business_date}", response_model=DayCloseRecord)
    def get_day_close(business_date: date, record: _ShopRecord = Depends(shop_scope)) -> DayCloseRecord:
        item = record.day_closes.get(business_date)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="day close not found")
        return item

    @app.post("/api/v1/shops/{shop_id}/day-close", response_model=DayCloseRecord, status_code=status.HTTP_201_CREATED)
    def close_day(
        request: DayCloseCreate,
        record: _ShopRecord = Depends(shop_scope),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> DayCloseRecord:
        if not request.confirmed:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="day close requires explicit confirmation")
        if not idempotency_key or not idempotency_key.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key is required")
        key = idempotency_key.strip()
        if request.business_date in record.cash_closes:
            raise HTTPException(status_code=409, detail="cash-only close already exists; recover its saved receipt")
        fingerprint = hashlib.sha256(json.dumps(request.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
        previous = record.day_close_idempotency.get(key)
        if previous:
            old_fingerprint, old_record = previous
            if old_fingerprint != fingerprint:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="day close idempotency key payload mismatch")
            return old_record
        if request.business_date in record.day_closes:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="daily close is already locked")
        breakdown = _day_close_breakdown(record, request.business_date)
        close_id = uuid4()
        item = DayCloseRecord(
            id=close_id, audit_id=close_id, shop_id=record.shop.id, business_date=request.business_date,
            opening_cash_cents=int(breakdown["opening_cash_cents"]), opening_bank_card_cents=int(breakdown["opening_bank_card_cents"]),
            sales_cash_cents=int(breakdown["sales_cash_cents"]), sales_bank_card_cents=int(breakdown["sales_bank_card_cents"]),
            paid_expenses_cash_cents=int(breakdown["paid_expenses_cash_cents"]), paid_expenses_bank_card_cents=int(breakdown["paid_expenses_bank_card_cents"]),
            paid_purchases_cash_cents=int(breakdown["paid_purchases_cash_cents"]), paid_purchases_bank_card_cents=int(breakdown["paid_purchases_bank_card_cents"]),
            refunds_cash_cents=int(breakdown["refunds_cash_cents"]), refunds_bank_card_cents=int(breakdown["refunds_bank_card_cents"]),
            adjustments_cash_cents=int(breakdown["adjustments_cash_cents"]), adjustments_bank_card_cents=int(breakdown["adjustments_bank_card_cents"]),
            expected_cash_cents=int(breakdown["expected_cash_cents"]), expected_bank_card_cents=int(breakdown["expected_bank_card_cents"]),
            cash_counted_cents=request.cash_counted_cents, bank_card_counted_cents=request.bank_card_counted_cents,
            cash_variance_cents=request.cash_counted_cents - int(breakdown["expected_cash_cents"]),
            bank_card_variance_cents=request.bank_card_counted_cents - int(breakdown["expected_bank_card_cents"]),
            notes=request.notes, actor=request.actor, confirmed_at=retail_utc_now(),
            shop_timezone=record.shop.timezone, calculation_basis="full_recorded_movements",
            warnings=list(breakdown.get("warnings", [])),
        )
        record.day_closes[request.business_date] = item
        record.day_close_idempotency[key] = (fingerprint, item)
        return item

    @app.post("/api/v1/shops/{shop_id}/muse", response_model=MuseAskResponse)
    def ask_muse_endpoint(request: MuseAskRequest, record: _ShopRecord = Depends(shop_scope)) -> MuseAskResponse:
        """Answer a shop question from the selected period's repository evidence."""

        now = datetime.now(timezone.utc)
        question = request.question
        lowered = question.lower()
        from .sales_answers import repository_sales_answer
        repository_answer = repository_sales_answer(question, record)
        if repository_answer is not None:
            return MuseAskResponse(**repository_answer)
        period_start = _muse_period_start(lowered, now)
        sales = [
            sale for _, sale in record.idempotent_sales.values()
            if sale.created_at >= period_start
        ]
        period_name = _muse_period_name(lowered)
        sales_cents = sum(sale.total_cents for sale in sales)
        evidence = (
            Evidence(f"sales-{period_name}", "sales_total", float(sales_cents), "cents", period_name),
            Evidence(f"transactions-{period_name}", "transaction_count", float(len(sales)), "transactions", period_name),
        )

        asks_profit = any(token in lowered for token in ("profit", "margin", "cogs", "cost of goods", "expense"))
        if asks_profit:
            missing: list[str] = []
            cogs_known = bool(sales) and all(sale.cogs_micros is not None for sale in sales)
            confirmed_expenses = [
                expense for expense in record.expenses.values()
                if expense.status == "confirmed"
                and (
                    expense.period_end is not None
                    and expense.period_start is not None
                    and expense.period_end >= period_start.date()
                    and expense.period_start <= now.date()
                    or expense.period_end is None
                    and expense.occurred_on >= period_start.date()
                    and expense.occurred_on <= now.date()
                )
            ]
            if not cogs_known:
                missing.append("cost of goods sold (COGS) for sales without a confirmed product cost")
            cogs_micros = sum(sale.cogs_micros or 0 for sale in sales)
            expenses_cents = sum(expense.amount_cents for expense in confirmed_expenses)
            if sales or confirmed_expenses:
                evidence = evidence + (
                    Evidence(f"cogs-{period_name}", "cogs_total", float(cogs_micros), "micros", period_name),
                    Evidence(f"expenses-{period_name}", "operating_expenses", float(expenses_cents), "cents", period_name),
                )
            if missing:
                missing.append("confirmed operating expenses for the selected period" if not confirmed_expenses else "")
                missing = [item for item in missing if item]
                return MuseAskResponse(
                    status="needs_data",
                    answer=(
                        f"I found {len(sales)} recorded transaction(s) and "
                        f"{_money(record.shop.currency, sales_cents)} in sales for {period_name}. "
                        "I cannot calculate profit yet because some confirmed cost data is missing."
                    ),
                    title="Profit needs more confirmed cost data",
                    evidence_ids=[item.evidence_id for item in evidence],
                    missing_data=missing,
                    source="repository",
                    confidence=1.0,
                )
            profit_micros = (sales_cents * 10_000) - cogs_micros - (expenses_cents * 10_000)
            return MuseAskResponse(
                status="answered",
                answer=(
                    f"Profit for {period_name}: {_money(record.shop.currency, profit_micros // 10_000)}. "
                    f"Sales {_money(record.shop.currency, sales_cents)}, "
                    f"COGS {_money(record.shop.currency, cogs_micros // 10_000)}, "
                    f"operating expenses {_money(record.shop.currency, expenses_cents)}."
                ),
                title="Profitability from confirmed records",
                evidence_ids=[item.evidence_id for item in evidence],
                missing_data=[],
                source="repository",
                confidence=1.0,
            )

        ai = app.state.muse_ai or build_muse_ai()
        result = ai.business_insight(InsightRequest(evidence=evidence, question=question))
        insight = result.value
        if result.source == "fallback":
            return MuseAskResponse(
                status="unavailable",
                answer=insight.summary,
                title=insight.title,
                evidence_ids=list(insight.evidence_ids),
                missing_data=[],
                source="fallback",
                confidence=insight.confidence,
            )
        return MuseAskResponse(
            status="answered",
            answer=insight.summary,
            title=insight.title,
            evidence_ids=list(insight.evidence_ids),
            missing_data=[],
            source="meta",
            confidence=insight.confidence,
        )

    @app.post("/api/v1/shops/{shop_id}/social/brief", response_model=SocialBriefResponse)
    def social_brief(request: SocialBriefRequest, record: _ShopRecord = Depends(shop_scope)) -> SocialBriefResponse:
        selected: list[SelectedSocialProduct] = []
        for product_id in request.product_ids:
            product = record.products.get(product_id)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="selected product not found in shop")
            selected.append(SelectedSocialProduct(
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                unit_price_cents=product.unit_price_cents,
                stock_qty=product.stock_qty,
            ))
        return SocialBriefResponse(
            shop_id=record.shop.id,
            products=selected,
            shop_image=request.shop_image,
            created_at=datetime.now(timezone.utc),
        )

    @app.post("/shops/{shop_id}/products", response_model=Product, status_code=status.HTTP_201_CREATED)
    def create_product(
        request: ProductCreate,
        record: _ShopRecord = Depends(shop_scope),
    ) -> Product:
        try:
            return store.create_product(record, request)
        except RepositoryConflict as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="repository unavailable") from exc

    @app.get("/shops/{shop_id}/products", response_model=list[Product])
    def list_products(record: _ShopRecord = Depends(shop_scope)) -> list[Product]:
        try:
            return store.list_products(record)
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="repository unavailable") from exc

    @app.post("/shops/{shop_id}/sales", response_model=Sale, status_code=status.HTTP_201_CREATED)
    def create_sale(
        request: SaleCreate,
        record: _ShopRecord = Depends(shop_scope),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> Sale:
        if not idempotency_key or not idempotency_key.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key is required")
        key = idempotency_key.strip()
        fingerprint = _payload_fingerprint(request)
        try:
            return store.create_sale(record, request, fingerprint, key)
        except RepositoryConflict as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except RepositoryIdempotencyConflict as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except RepositoryNotFound as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except RepositoryInsufficientStock as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="repository unavailable") from exc

    @app.get("/shops/{shop_id}/sales", response_model=list[Sale])
    def list_sales(record: _ShopRecord = Depends(shop_scope)) -> list[Sale]:
        return sorted((sale for _, sale in record.idempotent_sales.values()), key=lambda sale: sale.created_at, reverse=True)

    return app


app = create_app()
