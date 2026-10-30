"""Persistence configuration and the PostgreSQL-ready repository boundary.

The API depends on the small ``Repository`` contract rather than on a
database client.  ``memory`` is an explicit local/test mode; PostgreSQL is
the deployment mode and owns durable state, idempotency, and stock writes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Settings:
    """Runtime configuration with a safe, credential-free local default."""

    store_backend: str = "memory"
    database_url: str | None = None
    repository_root: Path = Path.cwd()
    team_activity_enabled: bool = True
    voice_enabled: bool = True

    def __post_init__(self) -> None:
        if self.store_backend not in {"memory", "postgres"}:
            raise ValueError("store_backend must be 'memory' or 'postgres'")
        if self.store_backend == "postgres" and not self.database_url:
            raise ValueError("database_url is required for postgres mode")

    @classmethod
    def from_env(cls) -> "Settings":
        backend = os.getenv("STREET_CEO_STORE", "memory").strip().lower()
        database_url = os.getenv("STREET_CEO_DATABASE_URL")
        repository_root = Path(os.getenv("STREET_CEO_REPOSITORY_ROOT", str(Path.cwd())))
        enabled_value = os.getenv("STREET_CEO_TEAM_ACTIVITY_ENABLED")
        enabled = (backend == "memory") if enabled_value is None else enabled_value.strip().lower() in {"1", "true", "yes", "on"}
        voice_value = os.getenv("STREET_CEO_VOICE_ENABLED")
        voice_enabled = (backend == "memory") if voice_value is None else voice_value.strip().lower() in {"1", "true", "yes", "on"}
        if backend not in {"memory", "postgres"}:
            raise ValueError("STREET_CEO_STORE must be 'memory' or 'postgres'")
        return cls(store_backend=backend, database_url=database_url, repository_root=repository_root, team_activity_enabled=enabled, voice_enabled=voice_enabled)


class Repository(Protocol):
    """Persistence seam consumed by the API service.

    Implementations make sale idempotency and stock validation/decrement one
    transaction. The returned record is the API's compatibility view.
    """

    def check_ready(self) -> None: ...
    def create_shop(self, request: Any) -> Any: ...
    def get_shop_record(self, shop_id: UUID) -> Any: ...
    def create_product(self, record: Any, request: Any) -> Any: ...
    def list_products(self, record: Any) -> list[Any]: ...
    def create_sale(self, record: Any, request: Any, fingerprint: str, key: str) -> Any: ...


class RepositoryNotFound(LookupError):
    pass


class RepositoryConflict(ValueError):
    pass


class RepositoryInsufficientStock(ValueError):
    pass


class RepositoryIdempotencyConflict(ValueError):
    pass


class PostgresRepository:
    """Transactional PostgreSQL repository for the existing API contract."""

    def __init__(self, database_url: str) -> None:
        if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("PostgreSQL mode requires a postgresql:// database URL")
        try:
            from sqlalchemy import create_engine
        except ImportError as exc:  # pragma: no cover - exercised in minimal installs
            raise RuntimeError("PostgreSQL mode requires SQLAlchemy") from exc
        self.database_url = database_url
        try:
            self.engine = create_engine(database_url, pool_pre_ping=True)
        except ModuleNotFoundError as exc:
            raise RuntimeError("PostgreSQL mode requires the psycopg driver") from exc

    def check_ready(self) -> None:
        from sqlalchemy import text

        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                migrated = connection.execute(text("SELECT to_regclass('public.shops')")).scalar()
                if migrated is None:
                    raise RuntimeError("PostgreSQL schema is not migrated")
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError("PostgreSQL database is unavailable") from exc

    @staticmethod
    def _models() -> tuple[Any, ...]:
        from services.api.app import Product, ProductCreate, Sale, SaleCreate, SaleLine, Shop, ShopCreate, _ShopRecord
        return Shop, ShopCreate, Product, ProductCreate, Sale, SaleCreate, SaleLine, _ShopRecord

    def _connection(self) -> Any:
        try:
            return self.engine.connect()
        except Exception as exc:
            raise RuntimeError("PostgreSQL database is unavailable") from exc

    def create_shop(self, request: Any) -> Any:
        from sqlalchemy import text

        Shop, _, _, _, _, _, _, _ = self._models()
        shop = Shop(id=uuid4(), **request.model_dump())
        try:
            with self.engine.begin() as connection:
                connection.execute(text("""
                    INSERT INTO shops (id, name, currency, timezone, created_at)
                    VALUES (:id, :name, :currency, :timezone, :created_at)
                """), {**shop.model_dump(mode="json"), "id": str(shop.id), "created_at": datetime.now(timezone.utc)})
        except Exception as exc:
            raise RuntimeError("PostgreSQL shop write failed; verify migrations and database availability") from exc
        return shop

    def get_shop_record(self, shop_id: UUID) -> Any:
        from sqlalchemy import text

        Shop, _, Product, _, Sale, _, SaleLine, ShopRecord = self._models()
        try:
            with self.engine.connect() as connection:
                shop_row = connection.execute(text("SELECT id, name, currency, timezone FROM shops WHERE id = :shop_id"), {"shop_id": str(shop_id)}).mappings().first()
                if shop_row is None:
                    raise RepositoryNotFound("shop not found")
                product_rows = connection.execute(text("SELECT id, shop_id, sku, name, unit_price_cents, stock_qty FROM products WHERE shop_id = :shop_id ORDER BY sku"), {"shop_id": str(shop_id)}).mappings().all()
                sale_rows = connection.execute(text("SELECT id, shop_id, tender, total_cents, created_at, idempotency_key, request_fingerprint FROM sales WHERE shop_id = :shop_id ORDER BY created_at"), {"shop_id": str(shop_id)}).mappings().all()
                line_rows = connection.execute(text("""
                    SELECT sl.sale_id, sl.product_id, sl.quantity
                    FROM sale_lines sl JOIN sales s ON s.id = sl.sale_id
                    WHERE s.shop_id = :shop_id ORDER BY sl.sale_id, sl.product_id
                """), {"shop_id": str(shop_id)}).mappings().all()
        except RepositoryNotFound:
            raise
        except Exception as exc:
            raise RuntimeError("PostgreSQL shop read failed; verify migrations and database availability") from exc

        shop = Shop(id=UUID(str(shop_row["id"])), name=shop_row["name"], currency=shop_row["currency"].strip(), timezone=shop_row["timezone"])
        record = ShopRecord(shop=shop)
        for row in product_rows:
            product = Product(id=UUID(str(row["id"])), shop_id=shop.id, sku=row["sku"], name=row["name"], unit_price_cents=row["unit_price_cents"], stock_qty=row["stock_qty"])
            record.products[product.id] = product
        lines_by_sale: dict[UUID, list[Any]] = {}
        for row in line_rows:
            sale_id = UUID(str(row["sale_id"]))
            lines_by_sale.setdefault(sale_id, []).append(SaleLine(product_id=UUID(str(row["product_id"])), quantity=row["quantity"]))
        for row in sale_rows:
            sale_id = UUID(str(row["id"]))
            sale = Sale(id=sale_id, shop_id=shop.id, lines=lines_by_sale.get(sale_id, []), tender=row["tender"], total_cents=row["total_cents"], created_at=row["created_at"])
            record.idempotent_sales[row["idempotency_key"]] = (row["request_fingerprint"].strip(), sale)
        return record

    def create_product(self, record: Any, request: Any) -> Any:
        from sqlalchemy import text

        _, _, Product, _, _, _, _, _ = self._models()
        product = Product(id=uuid4(), shop_id=record.shop.id, sku=request.sku, name=request.name, unit_price_cents=request.unit_price_cents, stock_qty=request.opening_stock_qty)
        try:
            with self.engine.begin() as connection:
                connection.execute(text("""
                    INSERT INTO products (id, shop_id, sku, name, unit_price_cents, stock_qty)
                    VALUES (:id, :shop_id, :sku, :name, :unit_price_cents, :stock_qty)
                """), {**product.model_dump(mode="json"), "id": str(product.id), "shop_id": str(product.shop_id)})
        except Exception as exc:
            if "duplicate key" in str(exc).lower() or "unique" in str(exc).lower():
                raise RepositoryConflict("sku already exists") from exc
            raise RuntimeError("PostgreSQL product write failed; verify migrations and database availability") from exc
        record.products[product.id] = product
        return product

    def list_products(self, record: Any) -> list[Any]:
        refreshed = self.get_shop_record(record.shop.id)
        record.products = refreshed.products
        record.idempotent_sales = refreshed.idempotent_sales
        return list(record.products.values())

    def create_sale(self, record: Any, request: Any, fingerprint: str, key: str) -> Any:
        from sqlalchemy import text

        _, _, Product, _, Sale, _, _, _ = self._models()
        try:
            with self.engine.begin() as connection:
                existing = connection.execute(text("""
                    SELECT id, shop_id, tender, total_cents, created_at, request_fingerprint
                    FROM sales WHERE shop_id = :shop_id AND idempotency_key = :key
                """), {"shop_id": str(record.shop.id), "key": key}).mappings().first()
                if existing is not None:
                    if existing["request_fingerprint"].strip() != fingerprint:
                        raise RepositoryIdempotencyConflict("idempotency key payload mismatch")
                    return self._load_sale(connection, record.shop.id, existing)

                products: list[Any] = []
                for line in request.lines:
                    row = connection.execute(text("""
                        SELECT id, shop_id, sku, name, unit_price_cents, stock_qty
                        FROM products WHERE id = :product_id AND shop_id = :shop_id FOR UPDATE
                    """), {"product_id": str(line.product_id), "shop_id": str(record.shop.id)}).mappings().first()
                    if row is None:
                        raise RepositoryNotFound("product not found")
                    if row["stock_qty"] < line.quantity:
                        raise RepositoryInsufficientStock("insufficient stock")
                    products.append(Product(id=UUID(str(row["id"])), shop_id=record.shop.id, sku=row["sku"], name=row["name"], unit_price_cents=row["unit_price_cents"], stock_qty=row["stock_qty"]))
                total_cents = sum(product.unit_price_cents * line.quantity for product, line in zip(products, request.lines))
                sale = Sale(id=uuid4(), shop_id=record.shop.id, lines=request.lines, tender=request.tender, total_cents=total_cents, created_at=datetime.now(timezone.utc))
                connection.execute(text("""
                    INSERT INTO sales (id, shop_id, tender, total_cents, created_at, idempotency_key, request_fingerprint)
                    VALUES (:id, :shop_id, :tender, :total_cents, :created_at, :key, :fingerprint)
                """), {"id": str(sale.id), "shop_id": str(sale.shop_id), "tender": sale.tender, "total_cents": sale.total_cents, "created_at": sale.created_at, "key": key, "fingerprint": fingerprint})
                for product, line in zip(products, request.lines):
                    connection.execute(text("""
                        INSERT INTO sale_lines (sale_id, product_id, quantity, unit_price_cents)
                        VALUES (:sale_id, :product_id, :quantity, :unit_price_cents)
                    """), {"sale_id": str(sale.id), "product_id": str(product.id), "quantity": line.quantity, "unit_price_cents": product.unit_price_cents})
                    connection.execute(text("UPDATE products SET stock_qty = stock_qty - :quantity WHERE id = :product_id AND shop_id = :shop_id"), {"quantity": line.quantity, "product_id": str(product.id), "shop_id": str(record.shop.id)})
        except (RepositoryIdempotencyConflict, RepositoryNotFound, RepositoryInsufficientStock):
            raise
        except Exception as exc:
            raise RuntimeError("PostgreSQL sale transaction failed; verify migrations and database availability") from exc
        record.idempotent_sales[key] = (fingerprint, sale)
        for product, line in zip(products, request.lines):
            product.stock_qty -= line.quantity
            record.products[product.id] = product
        return sale

    @staticmethod
    def _load_sale(connection: Any, shop_id: UUID, row: Any) -> Any:
        from sqlalchemy import text

        _, _, _, _, Sale, _, SaleLine, _ = PostgresRepository._models()
        lines = connection.execute(text("SELECT product_id, quantity FROM sale_lines WHERE sale_id = :sale_id ORDER BY product_id"), {"sale_id": str(row["id"])}).mappings().all()
        return Sale(id=UUID(str(row["id"])), shop_id=shop_id, lines=[SaleLine(product_id=UUID(str(line["product_id"])), quantity=line["quantity"]) for line in lines], tender=row["tender"], total_cents=row["total_cents"], created_at=row["created_at"])


def build_repository(settings: Settings | None = None) -> Any:
    """Build the selected backend; never silently downgrade PostgreSQL."""

    settings = settings or Settings.from_env()
    if settings.store_backend == "postgres":
        if not settings.database_url:  # defensive for callers constructing Settings directly
            raise ValueError("database_url is required for postgres mode")
        return PostgresRepository(settings.database_url)
    # Imported lazily to avoid a module cycle while app models are defined.
    from services.api.app import InMemoryStore

    return InMemoryStore()


POSTGRES_SCHEMA_SQL = """
-- 0001_initial.sql: additive starting point for the MVP operational store.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS shops (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name varchar(120) NOT NULL,
    currency char(3) NOT NULL,
    timezone varchar(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id uuid NOT NULL REFERENCES shops(id),
    sku varchar(64) NOT NULL,
    name varchar(120) NOT NULL,
    unit_price_cents bigint NOT NULL CHECK (unit_price_cents >= 0),
    stock_qty bigint NOT NULL CHECK (stock_qty >= 0),
    UNIQUE (shop_id, sku)
);

CREATE TABLE IF NOT EXISTS sales (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id uuid NOT NULL REFERENCES shops(id),
    tender varchar(32) NOT NULL,
    total_cents bigint NOT NULL CHECK (total_cents >= 0),
    created_at timestamptz NOT NULL,
    idempotency_key varchar(255) NOT NULL,
    request_fingerprint char(64) NOT NULL,
    UNIQUE (shop_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS sale_lines (
    sale_id uuid NOT NULL REFERENCES sales(id),
    product_id uuid NOT NULL REFERENCES products(id),
    quantity bigint NOT NULL CHECK (quantity > 0),
    unit_price_cents bigint NOT NULL CHECK (unit_price_cents >= 0),
    PRIMARY KEY (sale_id, product_id)
);
"""
