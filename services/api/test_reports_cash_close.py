from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from services.api.app import InMemoryStore, SaleCreate, SaleLine, create_app
from services.api.cash_close import calculate_cash_preview
from services.api.persistence import Settings
from services.api.reports import sales_report
from services.api.retail_control import CashCloseCreate, CashMovementCreate, CashOpeningCreate
from services.api.retail_control import PurchaseCreate, PurchaseLineCreate


def setup():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings(), voice_catalogue_resolver=None)
    return app, store.shops[shop_id]


def endpoint(app, path, method="POST"):
    return next(route.endpoint for route in app.routes if route.path == path and method in route.methods)


def sell(app, record, key="sale", quantity=1):
    product = next(iter(record.products.values()))
    return endpoint(app, "/shops/{shop_id}/sales")(SaleCreate(lines=[SaleLine(product_id=product.id, quantity=quantity)], tender="cash"), record, key)


def test_product_reports_use_saved_prices_costs_and_unique_receipt_ids():
    app, record = setup()
    receipt = sell(app, record)
    record.idempotent_sales["alias"] = record.idempotent_sales["sale"]
    product = next(iter(record.products.values()))
    product.unit_price_cents = 999
    product.unit_cost_micros = 777777
    product.name = "Renamed after sale"
    result = sales_report(record, preset="last1")
    assert result["summary"]["sales_total_cents"] == 150
    assert result["summary"]["transaction_count"] == 1
    assert result["products"][0]["revenue_cents"] == 150
    assert result["products"][0]["cogs_micros"] == 1000000
    assert result["products"][0]["product_name"] == "Coca-Cola 300ml"
    assert result["products"][0]["label_source"] == "latest_receipt_snapshot"
    assert receipt.receipt_lines[0].unit_price_cents == 150


def test_old_multiline_prices_unknown_and_singleline_attribution_known():
    app, record = setup()
    coke, bread = list(record.products.values())[:2]
    receipt = endpoint(app, "/shops/{shop_id}/sales")(SaleCreate(lines=[SaleLine(product_id=coke.id, quantity=1), SaleLine(product_id=bread.id, quantity=1)], tender="cash"), record, "multi")
    receipt.receipt_lines = []
    receipt.cogs_micros = None
    single = sell(app, record, "single")
    single.receipt_lines = []
    result = sales_report(record, preset="last1")
    assert result["summary"]["sales_total_cents"] == 480
    assert result["summary"]["unallocated_product_revenue_cents"] == 330
    assert result["summary"]["cogs_micros"] is None
    rows = {item["product_id"]: item for item in result["products"]}
    assert rows[str(coke.id)]["known_revenue_cents"] == 150
    assert rows[str(coke.id)]["revenue_cents"] is None
    assert rows[str(coke.id)]["quantity_sold"] == 2
    assert rows[str(bread.id)]["revenue_cents"] is None


def test_report_dates_are_inclusive_shop_local_days_and_presets_bounded():
    app, record = setup()
    first = sell(app, record, "first")
    first.created_at = datetime(2026, 9, 30, 22, tzinfo=timezone.utc)
    second = sell(app, record, "second")
    second.created_at = datetime(2026, 10, 1, 22, tzinfo=timezone.utc)
    result = sales_report(record, date(2026, 10, 1), date(2026, 10, 1))
    assert result["summary"]["transaction_count"] == 1
    assert result["daily"][0]["business_date"] == "2026-10-01"
    today = datetime.now(ZoneInfo(record.shop.timezone)).date()
    for preset, length in (("last1", 1), ("last20", 20), ("last90", 90)):
        report = sales_report(record, preset=preset)
        assert date.fromisoformat(report["end_date"]) == today
        assert (date.fromisoformat(report["end_date"]) - date.fromisoformat(report["start_date"])).days == length-1
    assert sales_report(record)["coverage"] == "current_month_to_date"
    with pytest.raises(ValueError):
        sales_report(record, today-timedelta(days=366), today)


def test_initial_retrospective_opening_zero_cash_only_variance_and_stale_guard():
    app, record = setup()
    day = datetime.now(ZoneInfo(record.shop.timezone)).date()
    sell(app, record)
    assert calculate_cash_preview(record, day).requires_opening is True
    opening = endpoint(app, "/api/v1/shops/{shop_id}/cash-close/opening")
    request = CashOpeningCreate(business_date=day, opening_cash_cents=0, actor="tester", reason="Remembered opening float", confirmed=True)
    opening(request, record, "opening")
    assert opening(request, record, "opening").amount_cents == 0
    with pytest.raises(HTTPException):
        opening(request, record, "other-opening")
    preview = calculate_cash_preview(record, day)
    assert preview.expected_cash_cents == 150
    close = endpoint(app, "/api/v1/shops/{shop_id}/cash-close")
    payload = CashCloseCreate(business_date=day, cash_counted_cents=140, actor="tester", confirmed=True, preview_version=preview.preview_version)
    sell(app, record, "second")
    with pytest.raises(HTTPException) as stale:
        close(payload, record, "close")
    assert stale.value.detail["code"] == "stale_preview"
    assert record.cash_closes == {}
    preview = calculate_cash_preview(record, day)
    payload = payload.model_copy(update={"preview_version": preview.preview_version})
    saved = close(payload, record, "close")
    assert saved.cash_variance_cents == -160
    assert saved.bank_card_counted_cents is None
    assert saved.bank_card_variance_cents is None
    assert close(payload, record, "close") == saved
    with pytest.raises(HTTPException):
        close(payload, record, "other-close")
    # Late recorded adjustment flags the frozen receipt without rewriting it.
    endpoint(app, "/api/v1/shops/{shop_id}/cash-movements")(CashMovementCreate(kind="adjustment", occurred_at=datetime.now(timezone.utc), amount_cents=10, tender="cash", actor="tester", reason="Late source"), record, "late")
    again = calculate_cash_preview(record, day)
    assert again.saved_close == saved
    assert again.expected_cash_cents == 300
    assert any("late/backdated" in warning for warning in again.warnings)
    assert close(payload, record, "close") == saved


def test_balance_anchor_carries_prior_trading_and_prior_counted_variance():
    app, record = setup()
    today = datetime.now(ZoneInfo(record.shop.timezone)).date()
    yesterday = today - timedelta(days=1)
    opening = endpoint(app, "/api/v1/shops/{shop_id}/cash-close/opening")
    opening(CashOpeningCreate(business_date=yesterday, opening_cash_cents=1000, actor="tester", reason="Initial float", confirmed=True), record, "opening")
    receipt = sell(app, record)
    receipt.created_at = datetime.combine(yesterday, datetime.min.time(), ZoneInfo(record.shop.timezone)).astimezone(timezone.utc) + timedelta(hours=12)
    assert calculate_cash_preview(record, today).opening_cash_cents == 1150
    preview = calculate_cash_preview(record, yesterday)
    saved = endpoint(app, "/api/v1/shops/{shop_id}/cash-close")(CashCloseCreate(business_date=yesterday, cash_counted_cents=1140, actor="tester", confirmed=True, preview_version=preview.preview_version), record, "close")
    assert saved.cash_variance_cents == -10
    next_day = calculate_cash_preview(record, today)
    assert next_day.opening_cash_cents == 1140
    assert next_day.opening_source == "prior_counted_close"
    assert any("unresolved variance" in warning for warning in next_day.warnings)


def test_fractional_purchase_payment_is_unknown_not_floored_to_cents():
    app, record = setup()
    day = datetime.now(ZoneInfo(record.shop.timezone)).date()
    endpoint(app, "/api/v1/shops/{shop_id}/cash-close/opening")(CashOpeningCreate(business_date=day, opening_cash_cents=1000, actor="tester", reason="Known opening", confirmed=True), record, "opening")
    product = next(iter(record.products.values()))
    draft = endpoint(app, "/api/v1/shops/{shop_id}/purchases")(PurchaseCreate(kind="manual", reference="fractional", purchase_date=day, actor="tester", tender="cash", total_cost_micros=10001, lines=[PurchaseLineCreate(product_id=product.id, quantity=1, purchase_unit_cost_micros=10001, line_total_micros=10001)]), record)
    endpoint(app, "/api/v1/shops/{shop_id}/purchases/{purchase_id}/confirm")(draft.id, record)
    preview = calculate_cash_preview(record, day)
    assert preview.requires_payment_review is True
    assert preview.paid_purchases_cash_cents is None
    assert preview.expected_cash_cents is None
    with pytest.raises(HTTPException):
        endpoint(app, "/api/v1/shops/{shop_id}/cash-close")(CashCloseCreate(business_date=day, cash_counted_cents=999, actor="tester", confirmed=True, preview_version=preview.preview_version), record, "close")
    assert record.cash_closes == {}


def test_generic_cash_opening_guard_preserves_legacy_replay_and_bank():
    import hashlib
    import json
    from services.api.retail_control import CashMovementRecord
    app, record = setup()
    now = datetime.now(timezone.utc)
    day = now.astimezone(ZoneInfo(record.shop.timezone)).date()
    route = endpoint(app, "/api/v1/shops/{shop_id}/cash-movements")
    old = CashMovementCreate(kind="opening_balance", occurred_at=now-timedelta(days=1), amount_cents=100, tender="cash", actor="tester", reason="Historical opening")
    saved = CashMovementRecord(id=uuid4(), shop_id=record.shop.id, created_at=now, **old.model_dump())
    digest = hashlib.sha256(json.dumps(old.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
    record.cash_movements[saved.id] = saved
    record.cash_movement_idempotency["legacy"] = (digest, saved)
    assert route(old, record, "legacy") == saved
    before = dict(record.cash_movements)
    with pytest.raises(HTTPException) as known:
        route(old, record, "new-known")
    assert known.value.status_code == 409
    assert "/cash-close/opening" in known.value.detail
    preview = calculate_cash_preview(record, day)
    close = endpoint(app, "/api/v1/shops/{shop_id}/cash-close")(CashCloseCreate(business_date=day, cash_counted_cents=100, actor="tester", confirmed=True, preview_version=preview.preview_version), record, "close")
    with pytest.raises(HTTPException):
        route(old, record, "new-frozen")
    assert route(old, record, "legacy") == saved
    assert record.cash_movements == before
    assert record.cash_closes[day] == close
    bank = route(old.model_copy(update={"tender": "bank"}), record, "bank")
    assert bank.tender == "bank"


def test_future_cash_movement_rejected_and_legacy_future_not_counted(monkeypatch):
    import services.api.cash_close as cash_module
    from services.api.retail_control import CashMovementRecord
    app, record = setup()
    fixed = datetime(2026, 11, 2, 10, tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed.astimezone(tz) if tz else fixed.replace(tzinfo=None)
    monkeypatch.setattr(cash_module, "datetime", Clock)
    monkeypatch.setattr("services.api.app.retail_utc_now", lambda: fixed)
    day = fixed.astimezone(ZoneInfo(record.shop.timezone)).date()
    endpoint(app, "/api/v1/shops/{shop_id}/cash-close/opening")(CashOpeningCreate(business_date=day, opening_cash_cents=100, actor="tester", reason="Known float", confirmed=True), record, "opening")
    movement = CashMovementCreate(kind="adjustment", occurred_at=fixed+timedelta(hours=1), amount_cents=50, tender="cash", actor="tester", reason="Future legacy source")
    route = endpoint(app, "/api/v1/shops/{shop_id}/cash-movements")
    before = dict(record.cash_movements)
    with pytest.raises(HTTPException) as future:
        route(movement, record, "future")
    assert future.value.status_code == 422
    assert record.cash_movements == before
    legacy = CashMovementRecord(id=uuid4(), shop_id=record.shop.id, created_at=fixed, **movement.model_dump())
    record.cash_movements[legacy.id] = legacy
    preview = calculate_cash_preview(record, day)
    assert preview.expected_cash_cents == 100
    assert str(legacy.id) not in preview.source_ids
    assert any("Future-effective" in warning for warning in preview.warnings)
    fixed += timedelta(hours=2)
    assert calculate_cash_preview(record, day).expected_cash_cents == 150
