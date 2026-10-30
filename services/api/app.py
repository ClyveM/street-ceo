"""Street CEO API foundation with an explicit persistence boundary."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from services.api.persistence import Settings, build_repository
from services.api.team_activity import TeamActivity, build_team_activity
from services.api.voice_boundary import (
    VoiceAudioRequest,
    VoiceResponse,
    VoiceTranscriptRequest,
    audio_fingerprint,
    decode_audio,
    normalize_intent,
    request_fingerprint,
)


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


class SaleLine(ApiModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class SaleCreate(ApiModel):
    lines: list[SaleLine] = Field(min_length=1)
    tender: str = Field(default="cash", min_length=1, max_length=32)

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


class Sale(ApiModel):
    id: UUID
    shop_id: UUID
    lines: list[SaleLine]
    tender: str
    total_cents: int
    created_at: datetime


class ShopSummary(ApiModel):
    sales_total_cents: int = Field(ge=0)
    transaction_count: int = Field(ge=0)
    low_stock_count: int = Field(ge=0)
    sales_change_percent: float | None = None
    insight: str


class ErrorResponse(ApiModel):
    detail: str


@dataclass
class _ShopRecord:
    shop: Shop
    products: dict[UUID, Product] = field(default_factory=dict)
    idempotent_sales: dict[str, tuple[str, Sale]] = field(default_factory=dict)
    voice_requests: dict[str, tuple[str, VoiceResponse]] = field(default_factory=dict)


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

    def seed_demo_shop(self) -> UUID:
        """Create the stable local catalogue used by the browser demo."""
        shop_id = UUID("00000000-0000-0000-0000-000000000001")
        if shop_id in self.shops:
            return shop_id
        shop = Shop(id=shop_id, name="Street CEO Demo Tuckshop", currency="USD", timezone="Africa/Harare")
        record = _ShopRecord(shop=shop)
        products = (
            ("COKE-300", "Coca-Cola 300ml", 150, 18), ("BREAD-700", "Bread loaf", 180, 11),
            ("SUGAR-1KG", "Sugar 1kg", 240, 7), ("MILK-500", "Milk 500ml", 130, 15),
            ("CHIPS-100", "Potato chips", 100, 23), ("SOAP-175", "Bath soap", 220, 5),
        )
        for index, (sku, name, price, stock) in enumerate(products, start=1):
            product = Product(id=UUID(f"00000000-0000-0000-0000-{index:012d}"), shop_id=shop_id, sku=sku, name=name, unit_price_cents=price, stock_qty=stock)
            record.products[product.id] = product
        self.shops[shop_id] = record
        return shop_id


def _payload_fingerprint(request: SaleCreate) -> str:
    canonical = json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_app(store: InMemoryStore | None = None, settings: Settings | None = None, voice_interpreter: object | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    store = store or build_repository(settings)
    app = FastAPI(title="Street CEO API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://192.168.10.213:5173",
        ],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.state.store = store
    app.state.voice_interpreter = voice_interpreter
    if os.getenv("STREET_CEO_SEED_DEMO", "false").strip().lower() in {"1", "true", "yes", "on"} and isinstance(store, InMemoryStore):
        app.state.demo_shop_id = str(store.seed_demo_shop())

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> dict[str, str]:
        store.check_ready()
        return {"status": "ready"}

    @app.get("/api/v1/team/activity", response_model=TeamActivity)
    def team_activity() -> TeamActivity:
        if not settings.team_activity_enabled:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="team activity is disabled")
        return build_team_activity(settings.repository_root, settings.team_activity_enabled)

    def shop_scope(
        shop_id: UUID,
        x_shop_id: Annotated[UUID | None, Header()] = None,
    ) -> _ShopRecord:
        if x_shop_id != shop_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="shop scope mismatch")
        record = store.shops.get(shop_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="shop not found")
        return record

    def voice_disabled() -> None:
        if not settings.voice_enabled:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="voice input is disabled")

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

    @app.post("/api/v1/shops/{shop_id}/voice/transcript", response_model=VoiceResponse)
    def interpret_voice_transcript(
        request: VoiceTranscriptRequest,
        record: _ShopRecord = Depends(shop_scope),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> VoiceResponse:
        voice_disabled()
        key = require_voice_key(idempotency_key)
        transcript = request.transcript.strip()
        fingerprint = request_fingerprint("transcript", {"transcript": transcript}).value
        replay = voice_replay(record, key, fingerprint)
        if replay is not None:
            return replay
        interpreter = get_interpreter()
        if interpreter is None:
            response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="transcript", status="unavailable", transcript=transcript, error="provider_unavailable")
        else:
            try:
                intent = normalize_intent(interpreter.interpret(transcript))
                response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="transcript", status="needs_confirmation" if intent.action == "record_sale" else "interpreted", transcript=transcript, intent=intent)
            except Exception:
                response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="transcript", status="rejected", transcript=transcript, error="invalid_or_unsafe_provider_response")
        record.voice_requests[key] = (fingerprint, response)
        return response

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
        response = VoiceResponse(request_id=uuid4(), shop_id=record.shop.id, input_kind="audio", status="unavailable", error="audio_transcription_unavailable")
        record.voice_requests[key] = (fingerprint, response)
        return response

    @app.post("/shops", response_model=Shop, status_code=status.HTTP_201_CREATED)
    def create_shop(request: ShopCreate) -> Shop:
        return store.create_shop(request)

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

    @app.post("/shops/{shop_id}/products", response_model=Product, status_code=status.HTTP_201_CREATED)
    def create_product(
        request: ProductCreate,
        record: _ShopRecord = Depends(shop_scope),
    ) -> Product:
        if any(product.sku == request.sku for product in record.products.values()):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="sku already exists")
        product = Product(
            id=uuid4(), shop_id=record.shop.id, sku=request.sku, name=request.name,
            unit_price_cents=request.unit_price_cents, stock_qty=request.opening_stock_qty,
        )
        record.products[product.id] = product
        return product

    @app.get("/shops/{shop_id}/products", response_model=list[Product])
    def list_products(record: _ShopRecord = Depends(shop_scope)) -> list[Product]:
        return list(record.products.values())

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
        previous = record.idempotent_sales.get(key)
        if previous:
            old_fingerprint, old_sale = previous
            if old_fingerprint != fingerprint:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="idempotency key payload mismatch")
            return old_sale

        products: list[Product] = []
        for line in request.lines:
            product = record.products.get(line.product_id)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")
            if product.stock_qty < line.quantity:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="insufficient stock")
            products.append(product)

        total_cents = sum(product.unit_price_cents * line.quantity for product, line in zip(products, request.lines))
        sale = Sale(
            id=uuid4(), shop_id=record.shop.id, lines=request.lines, tender=request.tender,
            total_cents=total_cents, created_at=datetime.now(timezone.utc),
        )
        for product, line in zip(products, request.lines):
            product.stock_qty -= line.quantity
        record.idempotent_sales[key] = (fingerprint, sale)
        return sale

    return app


app = create_app()
