"""Persistence configuration and the PostgreSQL-ready repository boundary.

The API depends on the small ``Repository`` contract rather than on a
database client.  ``memory`` is an explicit local/test mode; PostgreSQL is
the deployment mode and owns durable state, idempotency, and stock writes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class Settings:
    """Runtime configuration with a safe, credential-free local default."""

    store_backend: str = "memory"
    database_url: str | None = None
    repository_root: Path = Path.cwd()
    team_activity_enabled: bool = True

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
        if backend not in {"memory", "postgres"}:
            raise ValueError("STREET_CEO_STORE must be 'memory' or 'postgres'")
        return cls(store_backend=backend, database_url=database_url, repository_root=repository_root, team_activity_enabled=enabled)


class Repository(Protocol):
    """Persistence seam consumed by the API service.

    Implementations must make sale idempotency and stock validation/decrement
    one transaction.  The current endpoint handlers retain the W1 in-memory
    record contract while this protocol documents the durable replacement.
    """

    def check_ready(self) -> None: ...


class PostgresRepository:
    """PostgreSQL connection boundary for deployment wiring.

    Domain operations are intentionally added behind this seam in the next
    migration slice; constructing this adapter never silently substitutes the
    in-memory store.  ``check_ready`` is suitable for ``/readyz`` and makes a
    missing driver or unavailable database observable.
    """

    def __init__(self, database_url: str) -> None:
        if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("PostgreSQL mode requires a postgresql:// database URL")
        try:
            from sqlalchemy import create_engine
        except ImportError as exc:  # pragma: no cover - exercised in minimal installs
            raise RuntimeError("PostgreSQL mode requires SQLAlchemy") from exc
        self.database_url = database_url
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def check_ready(self) -> None:
        from sqlalchemy import text

        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))


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
