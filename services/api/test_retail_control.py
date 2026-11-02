from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
from copy import deepcopy
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from services.api.app import InMemoryStore, SaleCreate, SaleLine, create_app
from services.api.costs import ExpenseCreate
from services.api.persistence import Settings
from services.api.retail_control import (
    CashMovementCreate,
    CashOpeningCreate,
    DayCloseCreate,
    PurchaseCreate,
    PurchaseLineCreate,
    StockTakeCreate,
    StockTakeLineCreate,
)


def route(app, path: str, method: str):
    return next(item.endpoint for item in app.routes if item.path == path and method in item.methods)


def test_purchase_review_confirm_supports_existing_and_new_products_with_wac():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings())
    record = store.shops[shop_id]
    coke = next(product for product in record.products.values() if product.sku == "COKE-300")
    coke.unit_cost_micros = 1_000_000
    opening_audits = deepcopy(record.cost_audits)
    create = route(app, "/api/v1/shops/{shop_id}/purchases", "POST")
    confirm = route(app, "/api/v1/shops/{shop_id}/purchases/{purchase_id}/confirm", "POST")
    # The declared total must include every line; this proves the confirmation gate.
    with pytest.raises(ValueError, match="sum of line totals"):
        PurchaseCreate(
            kind="manual", reference="BAD", purchase_date=date.today(), actor="owner",
            total_cost_micros=2, lines=[PurchaseLineCreate(product_id=coke.id, quantity=1, purchase_unit_cost_micros=1, line_total_micros=1)],
        )

    corrected = create(PurchaseCreate(
        kind="manual", reference="PUR-002", purchase_date=date.today(), actor="owner", tender="cash",
        total_cost_micros=3_900_000,
        lines=[
            PurchaseLineCreate(product_id=coke.id, quantity=2, purchase_unit_cost_micros=1_200_000, line_total_micros=2_400_000),
            PurchaseLineCreate(sku="BISCUIT-100", name="Biscuits", unit_price_cents=100, quantity=3, purchase_unit_cost_micros=500_000, line_total_micros=1_500_000),
        ],
    ), record)
    result = confirm(corrected.id, record)

    assert result.total_cost_micros == 3_900_000
    coke_result = next(line for line in result.lines if line.product_id == coke.id)
    assert coke_result.new_average_unit_cost_micros == 1_020_000
    biscuits = next(product for product in record.products.values() if product.sku == "BISCUIT-100")
    assert biscuits.stock_qty == 3
    assert biscuits.unit_cost_micros == 500_000
    assert record.cost_audits[:len(opening_audits)] == opening_audits
    purchase_audits = record.cost_audits[len(opening_audits):]
    assert len(purchase_audits) == 2
    assert {audit.product_id for audit in purchase_audits} == {coke.id, biscuits.id}
    assert all(audit.source_type == "purchase" and audit.quantity_received > 0 for audit in purchase_audits)
    confirmed_audits = deepcopy(record.cost_audits)
    replay = confirm(corrected.id, record)
    assert replay == result
    assert record.products[coke.id].stock_qty == 20
    assert record.cost_audits == confirmed_audits


def test_purchase_confirmation_prevalidates_all_lines_and_cannot_partially_mutate():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings())
    record = store.shops[shop_id]
    coke = next(product for product in record.products.values() if product.sku == "COKE-300")
    opening_audits = deepcopy(record.cost_audits)
    opening_products = deepcopy(record.products)
    create = route(app, "/api/v1/shops/{shop_id}/purchases", "POST")
    confirm = route(app, "/api/v1/shops/{shop_id}/purchases/{purchase_id}/confirm", "POST")
    purchase = create(PurchaseCreate(
        kind="invoice", reference="INV-ATOMIC-1", purchase_date=date.today(), actor="owner",
        total_cost_micros=2_000_000,
        lines=[
            PurchaseLineCreate(product_id=coke.id, quantity=1, purchase_unit_cost_micros=1_000_000, line_total_micros=1_000_000),
            PurchaseLineCreate(product_id=uuid4(), quantity=1, purchase_unit_cost_micros=1_000_000, line_total_micros=1_000_000),
        ],
    ), record)

    with pytest.raises(HTTPException, match="product not found"):
        confirm(purchase.id, record)
    assert coke.stock_qty == 18
    assert record.cost_audits == opening_audits
    assert record.products == opening_products

    with pytest.raises(HTTPException, match="invoice reference already exists"):
        create(PurchaseCreate(
            kind="invoice", reference="inv-atomic-1", purchase_date=date.today(), actor="owner",
            total_cost_micros=1, lines=[PurchaseLineCreate(product_id=coke.id, quantity=1, purchase_unit_cost_micros=1, line_total_micros=1)],
        ), record)


def test_stock_take_is_review_first_and_audits_adjustment():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings())
    record = store.shops[shop_id]
    coke = next(product for product in record.products.values() if product.sku == "COKE-300")
    create = route(app, "/api/v1/shops/{shop_id}/stock-takes", "POST")
    confirm = route(app, "/api/v1/shops/{shop_id}/stock-takes/{stock_take_id}/confirm", "POST")
    take = create(StockTakeCreate(mode="monthly", count_date=date.today(), actor="owner", lines=[StockTakeLineCreate(product_id=coke.id, counted_qty=12)]), record)

    assert coke.stock_qty == 18
    result = confirm(take.id, record)
    assert coke.stock_qty == 12
    assert result.adjustments[0].expected_qty == 18
    assert result.adjustments[0].adjustment_qty == -6
    assert record.stock_adjustments[0].reason == "confirmed monthly stock take"


def test_stock_take_baseline_conflict_and_get_recovery():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings())
    record = store.shops[shop_id]
    coke = next(product for product in record.products.values() if product.sku == "COKE-300")
    create = route(app, "/api/v1/shops/{shop_id}/stock-takes", "POST")
    get_take = route(app, "/api/v1/shops/{shop_id}/stock-takes/{stock_take_id}", "GET")
    confirm = route(app, "/api/v1/shops/{shop_id}/stock-takes/{stock_take_id}/confirm", "POST")
    take = create(StockTakeCreate(mode="on_demand", count_date=date.today(), actor="owner", lines=[StockTakeLineCreate(product_id=coke.id, counted_qty=17)]), record)
    coke.stock_qty = 16

    with pytest.raises(HTTPException, match="baseline conflict"):
        confirm(take.id, record)
    recovered = get_take(take.id, record)
    assert recovered.status == "draft"
    assert recovered.expected_snapshot[coke.id] == 18
    assert coke.stock_qty == 16


def test_day_close_requires_confirmation_and_returns_cash_bank_variances():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings())
    record = store.shops[shop_id]
    route(app, "/api/v1/shops/{shop_id}/cash-close/opening", "POST")(CashOpeningCreate(business_date=date.today(), opening_cash_cents=0, actor="tester", reason="Explicit known zero opening", confirmed=True), record, "known-opening")
    coke = next(product for product in record.products.values() if product.sku == "COKE-300")
    sale = route(app, "/shops/{shop_id}/sales", "POST")
    sale(SaleCreate(lines=[SaleLine(product_id=coke.id, quantity=1)], tender="cash"), record, "close-sale-cash")
    sale(SaleCreate(lines=[SaleLine(product_id=coke.id, quantity=1)], tender="bank"), record, "close-sale-bank")
    close = route(app, "/api/v1/shops/{shop_id}/day-close", "POST")
    preview = route(app, "/api/v1/shops/{shop_id}/day-close/preview", "GET")

    preview_result = preview(date.today(), record)
    assert preview_result.calculation_basis == "full_recorded_movements"
    assert preview_result.shop_timezone == "Africa/Harare"
    assert preview_result.expected_cash_cents == 150
    assert preview_result.expected_bank_card_cents == 150

    with pytest.raises(HTTPException, match="explicit confirmation"):
        close(DayCloseCreate(business_date=date.today(), cash_counted_cents=200, bank_card_counted_cents=150, actor="owner"), record, None)
    result = close(DayCloseCreate(business_date=date.today(), cash_counted_cents=200, bank_card_counted_cents=150, actor="owner", confirmed=True, notes="Till counted"), record, "close-key-1")

    assert result.expected_cash_cents == 150
    assert result.expected_bank_card_cents == 150
    assert result.cash_variance_cents == 50
    assert result.bank_card_variance_cents == 0
    with pytest.raises(HTTPException, match="already locked"):
        close(DayCloseCreate(business_date=date.today(), cash_counted_cents=200, bank_card_counted_cents=150, actor="owner", confirmed=True), record, "close-key-2")


def test_day_close_full_breakdown_and_idempotent_cash_movements():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings())
    record = store.shops[shop_id]
    coke = next(product for product in record.products.values() if product.sku == "COKE-300")
    today = date.today()
    now = datetime.now(timezone.utc)
    movement = route(app, "/api/v1/shops/{shop_id}/cash-movements", "POST")
    opening_route = route(app, "/api/v1/shops/{shop_id}/cash-close/opening", "POST")
    opening_request = CashOpeningCreate(business_date=today - timedelta(days=1), opening_cash_cents=1000, actor="owner", reason="opening float", confirmed=True)
    opening = opening_route(opening_request, record, "movement-opening")
    assert opening_route(opening_request, record, "movement-opening") == opening
    with pytest.raises(HTTPException):
        opening_route(opening_request.model_copy(update={"opening_cash_cents": 900}), record, "movement-opening")
    movement(CashMovementCreate(
        kind="refund", occurred_at=now, amount_cents=20, tender="cash", actor="owner", reason="customer refund",
    ), record, "movement-refund")
    movement(CashMovementCreate(
        kind="adjustment", occurred_at=now, amount_cents=-5, tender="bank", actor="owner", reason="bank correction",
    ), record, "movement-adjustment")

    sale = route(app, "/shops/{shop_id}/sales", "POST")
    sale(SaleCreate(lines=[SaleLine(product_id=coke.id, quantity=1)], tender="cash"), record, "full-close-sale-cash")
    sale(SaleCreate(lines=[SaleLine(product_id=coke.id, quantity=1)], tender="bank"), record, "full-close-sale-bank")

    create_expense = route(app, "/api/v1/shops/{shop_id}/expenses", "POST")
    confirm_expense = route(app, "/api/v1/shops/{shop_id}/expenses/{expense_id}/confirm", "POST")
    expense = create_expense(ExpenseCreate(
        category="transport", frequency="one_off", occurred_on=today,
        amount_cents=30, tender="cash", notes="delivery",
    ), record)
    confirm_expense(expense.id, record)

    create_purchase = route(app, "/api/v1/shops/{shop_id}/purchases", "POST")
    confirm_purchase = route(app, "/api/v1/shops/{shop_id}/purchases/{purchase_id}/confirm", "POST")
    purchase = create_purchase(PurchaseCreate(
        kind="manual", reference="FULL-CLOSE-PURCHASE", purchase_date=today, actor="owner", tender="bank",
        total_cost_micros=100_000, lines=[PurchaseLineCreate(
            product_id=coke.id, quantity=1, purchase_unit_cost_micros=100_000, line_total_micros=100_000,
        )],
    ), record)
    confirm_purchase(purchase.id, record)

    preview = route(app, "/api/v1/shops/{shop_id}/day-close/preview", "GET")(today, record)
    assert preview.opening_cash_cents == 1_000
    assert preview.sales_cash_cents == 150
    assert preview.sales_bank_card_cents == 150
    assert preview.paid_expenses_cash_cents == 30
    assert preview.paid_purchases_bank_card_cents == 10
    assert preview.refunds_cash_cents == 20
    assert preview.adjustments_bank_card_cents == -5
    assert preview.expected_cash_cents == 1_100
    assert preview.expected_bank_card_cents == 135
    assert any("Legacy bank/card" in warning for warning in preview.warnings)

    close = route(app, "/api/v1/shops/{shop_id}/day-close", "POST")
    request = DayCloseCreate(
        business_date=today, cash_counted_cents=1_100, bank_card_counted_cents=135,
        actor="owner", confirmed=True, notes="full close",
    )
    result = close(request, record, "full-close-key")
    assert result.audit_id == result.id
    assert result.cash_variance_cents == 0
    assert result.bank_card_variance_cents == 0
    assert result.calculation_basis == "full_recorded_movements"
    assert close(request, record, "full-close-key") == result
    with pytest.raises(HTTPException, match="payload mismatch"):
        close(request.model_copy(update={"cash_counted_cents": 1_101}), record, "full-close-key")


def test_day_close_get_readback_and_missing_date():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings())
    record = store.shops[shop_id]
    route(app, "/api/v1/shops/{shop_id}/cash-close/opening", "POST")(CashOpeningCreate(business_date=date.today(), opening_cash_cents=0, actor="tester", reason="Explicit known zero opening", confirmed=True), record, "known-opening")
    today = date.today()
    close = route(app, "/api/v1/shops/{shop_id}/day-close", "POST")
    get_close = route(app, "/api/v1/shops/{shop_id}/day-close/{business_date}", "GET")
    request = DayCloseCreate(
        business_date=today, cash_counted_cents=0, bank_card_counted_cents=0,
        actor="owner", confirmed=True, notes="readback test",
    )
    result = close(request, record, "readback-close-key")
    assert get_close(today, record) == result
    with pytest.raises(HTTPException, match="day close not found"):
        get_close(today - timedelta(days=1), record)
