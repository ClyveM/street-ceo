"""Independent policy examples; synthetic records only, no network/provider."""
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from services.api.app import InMemoryStore, Sale, SaleCreate, SaleLine
from services.api import reports
from services.api.cash_close import calculate_cash_preview
from services.api import cash_close
from services.api.retail_control import CashMovementRecord, CashCloseRecord
from types import SimpleNamespace
from copy import deepcopy


def shop():
    store = InMemoryStore()
    key = store.seed_demo_shop()
    return store, store.shops[key]


def saved(record, instant, total=150, lines=None, cogs=None, tender="cash"):
    product = next(iter(record.products))
    sale = Sale(id=uuid4(), shop_id=record.shop.id, lines=lines or [SaleLine(product_id=product, quantity=1)], tender=tender, total_cents=total, cogs_micros=cogs, created_at=instant)
    record.idempotent_sales[str(sale.id)] = ("synthetic", sale)
    return sale


def test_inclusive_harare_day_is_half_open_utc_and_counts_unique_receipts():
    _, record = shop()
    lower = datetime(2026, 10, 31, 22, tzinfo=timezone.utc)
    saved(record, lower - timedelta(microseconds=1), 10)
    included = saved(record, lower, 150)
    saved(record, lower + timedelta(days=1) - timedelta(microseconds=1), 180, tender="bank")
    saved(record, lower + timedelta(days=1), 20)
    record.idempotent_sales["same-receipt-alias"] = ("same", included)
    result = reports.sales_report(record, date(2026, 11, 1), date(2026, 11, 1))
    assert result["summary"]["transaction_count"] == 2
    assert result["summary"]["sales_total_cents"] == 330
    assert result["summary"]["cash_sales_cents"] == 150
    assert result["summary"]["bank_sales_cents"] == 180
    assert result["daily"][0]["business_date"] == "2026-11-01"


@pytest.mark.parametrize("days", [1, 20, 90])
def test_presets_include_today_and_exactly_requested_local_calendar_days(monkeypatch, days):
    _, record = shop()
    class Clock(datetime):
        @classmethod
        def now(cls, zone=None):
            return datetime(2026, 11, 2, 0, 30, tzinfo=timezone.utc).astimezone(zone)
    monkeypatch.setattr(reports, "datetime", Clock)
    result = reports.sales_report(record, preset=f"last{days}")
    assert result["start_date"] == (date(2026, 11, 2) - timedelta(days=days - 1)).isoformat()
    assert result["end_date"] == "2026-11-02"


def test_legacy_mixed_receipt_has_quantities_but_no_invented_product_amounts():
    _, record = shop()
    ids = list(record.products)[:2]
    saved(record, datetime(2026, 11, 1, tzinfo=timezone.utc), 1000, [SaleLine(product_id=ids[0], quantity=2), SaleLine(product_id=ids[1], quantity=3)])
    record.products[ids[0]].unit_price_cents = 99999
    record.products[ids[1]].unit_cost_micros = 99999999
    result = reports.sales_report(record, date(2026, 11, 1), date(2026, 11, 1))
    assert result["summary"]["sales_total_cents"] == 1000
    assert result["summary"]["cogs_micros"] is None
    assert result["summary"]["unallocated_product_revenue_cents"] == 1000
    assert sorted(item["quantity_sold"] for item in result["products"]) == [2, 3]
    assert all(item["revenue_cents"] is None and item["cogs_micros"] is None for item in result["products"])


def test_future_receipt_snapshots_survive_price_cost_and_name_changes():
    store, record = shop()
    ids = list(record.products)[:2]
    sale = store.create_sale(record, SaleCreate(lines=[SaleLine(product_id=ids[0], quantity=2), SaleLine(product_id=ids[1], quantity=1)], tender="cash", amount_received_cents=1000), "snapshot", "snapshot")
    sale.created_at = datetime(2026, 11, 1, tzinfo=timezone.utc)
    for product in record.products.values():
        product.unit_price_cents = 99999
        product.unit_cost_micros = 0
        product.name = "Changed current label"
    result = reports.sales_report(record, date(2026, 11, 1), date(2026, 11, 1))
    assert result["summary"]["sales_total_cents"] == 480
    assert result["summary"]["cogs_micros"] == 3_200_000
    by_id = {item["product_id"]: item for item in result["products"]}
    assert by_id[str(ids[0])]["revenue_cents"] == 300
    assert by_id[str(ids[1])]["revenue_cents"] == 180
    assert all(item["product_name"] != "Changed current label" and item["label_source"] == "latest_receipt_snapshot" for item in result["products"])


def movement(record, day, amount, kind="opening_balance", tender="cash"):
    instant = datetime(day.year, day.month, day.day, tzinfo=timezone.utc) - timedelta(hours=2)
    item = CashMovementRecord(id=uuid4(), shop_id=record.shop.id, created_at=instant, occurred_at=instant, amount_cents=amount, kind=kind, tender=tender, actor="QA", reason="synthetic policy example")
    record.cash_movements[item.id] = item
    return item


def test_missing_opening_is_unknown_but_explicit_zero_is_known_and_bank_null():
    _, record = shop()
    result = calculate_cash_preview(record, date(2026, 11, 1))
    assert result.requires_opening and result.expected_cash_cents is None
    movement(record, date(2026, 11, 1), 0)
    result = calculate_cash_preview(record, date(2026, 11, 1))
    assert not result.requires_opening and result.opening_cash_cents == result.expected_cash_cents == 0
    assert result.bank_card_counted_cents is None and result.bank_card_variance_cents is None


def test_opening_is_one_latest_anchor_plus_intervening_trade_not_cumulative_counts():
    _, record = shop()
    movement(record, date(2026, 11, 1), 2000)
    latest = movement(record, date(2026, 11, 2), 2200)
    saved(record, datetime(2026, 11, 2, 10, tzinfo=timezone.utc), 100)
    result = calculate_cash_preview(record, date(2026, 11, 3))
    assert result.opening_source_id == latest.id
    assert result.opening_cash_cents == result.expected_cash_cents == 2300


def test_expected_cash_uses_sale_total_and_all_paid_signed_components():
    _, record = shop()
    day = date(2026, 11, 1)
    movement(record, day, 1000)
    sale = saved(record, datetime(2026, 11, 1, 10, tzinfo=timezone.utc), 150)
    sale.amount_received_cents = 500
    sale.change_cents = 350
    saved(record, datetime(2026, 11, 1, 11, tzinfo=timezone.utc), 999, tender="bank")
    for status, tender, amount in [("confirmed", "cash", 200), ("draft", "cash", 900), ("confirmed", "unpaid", 900)]:
        item = SimpleNamespace(id=uuid4(), status=status, tender=tender, occurred_on=day, amount_cents=amount, created_at=datetime(2026, 11, 1, 12, tzinfo=timezone.utc), confirmed_at=datetime(2026, 11, 1, 13, tzinfo=timezone.utc) if status == "confirmed" else None)
        record.expenses[item.id] = item
    purchase = SimpleNamespace(id=uuid4(), status="confirmed", tender="cash", purchase_date=day, total_cost_micros=3_000_000, created_at=datetime(2026, 11, 1, 12, tzinfo=timezone.utc), confirmed_at=datetime(2026, 11, 1, 13, tzinfo=timezone.utc))
    record.purchases[purchase.id] = purchase
    movement(record, day, 50, "refund")
    movement(record, day, -25, "adjustment")
    result = calculate_cash_preview(record, day)
    assert result.sales_cash_cents == 150
    assert result.expected_cash_cents == 575
    purchase.total_cost_micros = 3_000_001
    result = calculate_cash_preview(record, day)
    assert result.requires_payment_review and result.expected_cash_cents is None
    assert result.paid_purchases_cash_cents is None


def test_prior_count_carries_unresolved_variance_and_late_activity_without_rewriting_close():
    _, record = shop()
    day = date(2026, 11, 1)
    movement(record, day, 2000)
    saved(record, datetime(2026, 11, 1, 10, tzinfo=timezone.utc), 300)
    preview = calculate_cash_preview(record, day)
    data = preview.model_dump(exclude={"preview_version", "saved_close"})
    cutoff = datetime(2026, 11, 1, 20, tzinfo=timezone.utc)
    close = CashCloseRecord(**data, id=uuid4(), audit_id=uuid4(), shop_id=record.shop.id, cash_counted_cents=2200, cash_variance_cents=-100, actor="QA", notes="synthetic short count", confirmed_at=cutoff, as_of_cutoff=cutoff, source_version=preview.preview_version)
    record.cash_closes[day] = close
    frozen = deepcopy(close)
    saved(record, datetime(2026, 11, 1, 21, tzinfo=timezone.utc), 50)
    saved(record, datetime(2026, 11, 2, 10, tzinfo=timezone.utc), 150)
    result = calculate_cash_preview(record, date(2026, 11, 3))
    assert result.opening_cash_cents == 2400
    assert any("variance" in warning.lower() for warning in result.warnings)
    assert any("late" in warning.lower() for warning in result.warnings)
    assert record.cash_closes[day] == frozen
    original = calculate_cash_preview(record, day)
    assert original.saved_close == frozen and original.expected_cash_cents == 2300
    assert any("late" in warning.lower() for warning in original.warnings)


def test_legacy_single_receipt_is_attributable_and_stock_only_undo_is_not_cash_refund():
    _, record = shop()
    day = date(2026, 11, 1)
    movement(record, day, 0)
    sale = saved(record, datetime(2026, 11, 1, 10, tzinfo=timezone.utc), 150, cogs=1_000_000)
    reversal = SimpleNamespace(created_at=datetime(2026, 11, 1, 11, tzinfo=timezone.utc))
    record.voice_sale_reversals[sale.id] = reversal
    result = reports.sales_report(record, day, day)
    assert result["summary"]["sales_total_cents"] == 150
    assert result["products"][0]["revenue_cents"] == 150
    assert result["products"][0]["cogs_micros"] == 1_000_000
    assert result["stock_reversal_count"] == 1
    preview = calculate_cash_preview(record, day)
    assert preview.expected_cash_cents == 150 and preview.refunds_cash_cents == 0
    assert any("stock-only" in warning.lower() for warning in preview.warnings)


def test_local_day_spanning_dst_has_real_calendar_midnights_not_fixed_24_hours():
    _, record = shop()
    record.shop.timezone = "America/New_York"
    lower = datetime(2026, 3, 8, 5, tzinfo=timezone.utc)
    upper = datetime(2026, 3, 9, 4, tzinfo=timezone.utc)
    for instant in [lower-timedelta(microseconds=1), lower, upper-timedelta(microseconds=1), upper]:
        saved(record, instant, 100)
    result = reports.sales_report(record, date(2026, 3, 8), date(2026, 3, 8))
    assert result["summary"]["transaction_count"] == 2
    assert result["summary"]["sales_total_cents"] == 200


def test_legacy_future_cash_movement_is_excluded_from_present_count_with_warning(monkeypatch):
    _, record = shop()
    day = date(2026, 11, 1)
    movement(record, day, 1000)
    future = movement(record, day, -200, "adjustment")
    future.occurred_at = datetime(2026, 11, 1, 15, tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls, zone=None):
            return datetime(2026, 11, 1, 12, tzinfo=timezone.utc).astimezone(zone)
    monkeypatch.setattr(cash_close, "datetime", Clock)
    preview = cash_close.calculate_cash_preview(record, day)
    assert preview.expected_cash_cents == 1000
    assert any("future" in warning.lower() for warning in preview.warnings)
