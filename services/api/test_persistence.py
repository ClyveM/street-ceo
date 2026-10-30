import pytest

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
