from uuid import UUID

import pytest
from fastapi import HTTPException

from services.api.app import (
    InMemoryStore,
    ProductCreate,
    SaleCreate,
    SaleLine,
    ShopCreate,
    create_app,
)


def endpoint(app, path: str):
    return next(route.endpoint for route in app.routes if route.path == path)


def setup_product(stock: int = 3):
    app = create_app(InMemoryStore())
    shop = endpoint(app, "/shops")(ShopCreate(name="Mbare Tuckshop"))
    record = app.state.store.shops[shop.id]
    product = endpoint(app, "/shops/{shop_id}/products")(
        ProductCreate(sku="COKE-500", name="Coke 500ml", unit_price_cents=150, opening_stock_qty=stock), record
    )
    return app, record, product


def sale(app, record, product_id: UUID, quantity: int, key: str, tender: str = "cash"):
    request = SaleCreate(lines=[SaleLine(product_id=product_id, quantity=quantity)], tender=tender)
    return endpoint(app, "/shops/{shop_id}/sales")(request, record, key)


def test_health_and_readiness_handlers() -> None:
    app = create_app(InMemoryStore())
    assert endpoint(app, "/healthz")() == {"status": "ok"}
    assert endpoint(app, "/readyz")() == {"status": "ready"}


def test_shop_scope_is_represented_by_shop_id() -> None:
    _, record, product = setup_product()
    assert record.shop.id == product.shop_id
    assert product.shop_id in {record.shop.id}


def test_sale_is_idempotent_for_same_key_and_payload() -> None:
    app, record, product = setup_product()
    first = sale(app, record, product.id, 1, "sale-1")
    replay = sale(app, record, product.id, 1, "sale-1")
    assert first == replay
    assert record.products[product.id].stock_qty == 2


def test_sale_rejects_changed_payload_for_reused_key() -> None:
    _, record, product = setup_product()
    app, record, product = setup_product()
    sale(app, record, product.id, 1, "sale-1")
    with pytest.raises(HTTPException, match="payload mismatch"):
        sale(app, record, product.id, 2, "sale-1")


def test_sale_never_silently_creates_negative_stock() -> None:
    app, record, product = setup_product(stock=1)
    with pytest.raises(HTTPException, match="insufficient stock"):
        sale(app, record, product.id, 2, "sale-too-large")
    assert record.products[product.id].stock_qty == 1


def test_validation_is_deterministic_and_rejects_duplicate_lines() -> None:
    _, _, product = setup_product()
    with pytest.raises(ValueError, match="product_id may appear only once"):
        SaleCreate(lines=[SaleLine(product_id=product.id, quantity=1), SaleLine(product_id=product.id, quantity=1)])


def test_shop_summary_reports_live_sales_and_stock_alerts() -> None:
    app, record, product = setup_product(stock=3)
    summary = endpoint(app, "/shops/{shop_id}/summary")(record)
    assert summary.sales_total_cents == 0
    assert summary.transaction_count == 0
    assert summary.low_stock_count == 1
    assert "Coke 500ml" in summary.insight
