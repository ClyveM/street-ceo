"""Street CEO API foundation with an explicit persistence boundary."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from services.api.persistence import Settings, build_repository


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


class ErrorResponse(ApiModel):
    detail: str


@dataclass
class _ShopRecord:
    shop: Shop
    products: dict[UUID, Product] = field(default_factory=dict)
    idempotent_sales: dict[str, tuple[str, Sale]] = field(default_factory=dict)


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


def _payload_fingerprint(request: SaleCreate) -> str:
    canonical = json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_app(store: InMemoryStore | None = None, settings: Settings | None = None) -> FastAPI:
    store = store or build_repository(settings)
    app = FastAPI(title="Street CEO API", version="0.1.0")
    app.state.store = store

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> dict[str, str]:
        store.check_ready()
        return {"status": "ready"}

    @app.post("/shops", response_model=Shop, status_code=status.HTTP_201_CREATED)
    def create_shop(request: ShopCreate) -> Shop:
        return store.create_shop(request)

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

    @app.get("/shops/{shop_id}", response_model=Shop)
    def get_shop(record: Annotated[_ShopRecord, Depends(shop_scope)]) -> Shop:
        return record.shop

    @app.post("/shops/{shop_id}/products", response_model=Product, status_code=status.HTTP_201_CREATED)
    def create_product(
        request: ProductCreate,
        record: Annotated[_ShopRecord, Depends(shop_scope)],
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
    def list_products(record: Annotated[_ShopRecord, Depends(shop_scope)]) -> list[Product]:
        return list(record.products.values())

    @app.post("/shops/{shop_id}/sales", response_model=Sale, status_code=status.HTTP_201_CREATED)
    def create_sale(
        request: SaleCreate,
        record: Annotated[_ShopRecord, Depends(shop_scope)],
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
