import pytest
from fastapi import HTTPException
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from services.api.app import SaleCreate, SaleLine, Shop, _ShopRecord, create_app
from services.api.persistence import POSTGRES_SCHEMA_SQL, PostgresRepository, Settings, build_repository


def test_sqlite_default_matches_demo_launcher_from_any_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("STREET_CEO_SQLITE_PATH", raising=False)
    expected = Path(__file__).resolve().parents[2] / "data" / "demo-mvp.sqlite3"
    assert Path(Settings.from_env().sqlite_path) == Path(Settings().sqlite_path) == expected
    monkeypatch.setenv("STREET_CEO_SQLITE_PATH", "explicit.sqlite3")
    assert Settings.from_env().sqlite_path == "explicit.sqlite3"


def test_local_mode_is_explicit_and_credential_free(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("STREET_CEO_STORE", raising=False)
    monkeypatch.setenv("STREET_CEO_DATABASE_URL", "")
    monkeypatch.setenv("STREET_CEO_SQLITE_PATH", str(tmp_path / "local.sqlite3"))
    settings = Settings.from_env()
    assert settings.store_backend == "sqlite"
    assert settings.database_url is None
    repository = build_repository(settings)
    assert repository.__class__.__name__ == "SQLiteStore"
    repository.close()


def test_postgres_mode_requires_database_url() -> None:
    with pytest.raises(ValueError, match="database_url"):
        Settings(store_backend="postgres")


def test_local_memory_settings_enable_demo_seed_but_postgres_does_not(monkeypatch) -> None:
    monkeypatch.delenv("STREET_CEO_STORE", raising=False)
    monkeypatch.delenv("STREET_CEO_SEED_DEMO", raising=False)
    assert Settings.from_env().demo_seed_enabled is True

    monkeypatch.setenv("STREET_CEO_STORE", "postgres")
    monkeypatch.setenv("STREET_CEO_DATABASE_URL", "postgresql://local/test")
    assert Settings.from_env().demo_seed_enabled is False


def test_schema_has_shop_scope_and_idempotency_constraints() -> None:
    assert "UNIQUE (shop_id, sku)" in POSTGRES_SCHEMA_SQL
    assert "UNIQUE (shop_id, idempotency_key)" in POSTGRES_SCHEMA_SQL
    assert "CHECK (stock_qty >= 0)" in POSTGRES_SCHEMA_SQL
    assert "request_fingerprint" in POSTGRES_SCHEMA_SQL


def test_checked_in_migration_contains_adapter_durability_contract() -> None:
    migration = (Path(__file__).parent / "migrations" / "0001_initial.sql").read_text(encoding="utf-8")

    for table in ("shops", "products", "sales", "sale_lines"):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in migration
    assert "UNIQUE (shop_id, sku)" in migration
    assert "UNIQUE (shop_id, idempotency_key)" in migration
    assert "CHECK (stock_qty >= 0)" in migration
    assert "request_fingerprint char(64) NOT NULL" in migration
    assert "cogs_micros bigint" in migration


def test_postgres_backend_rejects_non_postgres_url_without_fallback() -> None:
    with pytest.raises(ValueError, match="postgresql"):
        build_repository(Settings(store_backend="postgres", database_url="sqlite:///not-postgres"))


def test_unavailable_postgres_readiness_is_a_503() -> None:
    class UnavailableRepository:
        def check_ready(self) -> None:
            raise RuntimeError("PostgreSQL database is unavailable")

    app = create_app(UnavailableRepository(), Settings(store_backend="postgres", database_url="postgresql://local/test"))
    readyz = next(route.endpoint for route in app.routes if route.path == "/readyz")
    with pytest.raises(HTTPException) as error:
        readyz()
    assert error.value.status_code == 503
    assert error.value.detail == "PostgreSQL database is unavailable"


def test_postgres_sale_transaction_persists_and_reloads_cogs() -> None:
    shop_id = UUID("00000000-0000-0000-0000-000000000001")
    product_id = UUID("00000000-0000-0000-0000-000000000002")

    class Result:
        def __init__(self, first=None, rows=None):
            self._first = first
            self._rows = rows or []

        def mappings(self):
            return self

        def first(self):
            return self._first

        def all(self):
            return self._rows

    class Connection:
        def __init__(self):
            self.statements = []

        def execute(self, statement, params=None):
            sql = str(statement)
            self.statements.append((sql, params))
            if "FROM sales WHERE" in sql:
                return Result(first=None)
            if "FROM products WHERE" in sql:
                return Result(first={
                    "id": str(product_id), "shop_id": str(shop_id), "sku": "COKE",
                    "name": "Coke", "unit_price_cents": 150, "stock_qty": 4,
                    "unit_cost_micros": 1200000,
                })
            return Result()

    class Transaction:
        def __init__(self, connection):
            self.connection = connection

        def __enter__(self):
            return self.connection

        def __exit__(self, exc_type, exc, traceback):
            return False

    class Engine:
        def __init__(self):
            self.connection = Connection()

        def begin(self):
            return Transaction(self.connection)

    repository = PostgresRepository.__new__(PostgresRepository)
    repository.engine = Engine()
    record = _ShopRecord(shop=Shop(id=shop_id, name="Demo", currency="USD", timezone="Africa/Harare"))
    request = SaleCreate(lines=[SaleLine(product_id=product_id, quantity=2)], tender="cash")

    sale = repository.create_sale(record, request, "fingerprint", "sale-1")

    assert sale.cogs_micros == 2_400_000
    insert_sql, insert_params = next(
        call for call in repository.engine.connection.statements if "INSERT INTO sales" in call[0]
    )
    assert "cogs_micros" in insert_sql
    assert insert_params["cogs_micros"] == 2_400_000

    reload_connection = Connection()
    reload_connection.execute = lambda statement, params=None: Result(rows=[{"product_id": str(product_id), "quantity": 2}])
    loaded = repository._load_sale(reload_connection, shop_id, {
        "id": str(sale.id), "tender": "cash", "total_cents": 300,
        "cogs_micros": 2_400_000, "created_at": datetime.now(timezone.utc),
    })
    assert loaded.cogs_micros == 2_400_000
