import pytest
from fastapi import HTTPException

from services.api.app import create_app
from services.api.persistence import POSTGRES_SCHEMA_SQL, Settings, build_repository


def test_local_mode_is_explicit_and_credential_free() -> None:
    settings = Settings.from_env()
    assert settings.store_backend == "memory"
    assert settings.database_url is None
    assert build_repository(settings).__class__.__name__ == "InMemoryStore"


def test_postgres_mode_requires_database_url() -> None:
    with pytest.raises(ValueError, match="database_url"):
        Settings(store_backend="postgres")


def test_schema_has_shop_scope_and_idempotency_constraints() -> None:
    assert "UNIQUE (shop_id, sku)" in POSTGRES_SCHEMA_SQL
    assert "UNIQUE (shop_id, idempotency_key)" in POSTGRES_SCHEMA_SQL
    assert "CHECK (stock_qty >= 0)" in POSTGRES_SCHEMA_SQL
    assert "request_fingerprint" in POSTGRES_SCHEMA_SQL


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
