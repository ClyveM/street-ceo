"""Muse's zero-opening cash scenario never changes cash reconciliation."""
from datetime import datetime, time, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from services.api.app import InMemoryStore, SaleCreate, SaleLine
from services.api.cash_close import calculate_cash_preview
from services.api.costs import ExpenseRecord
from services.api.muse_tools import toolset
from services.api.retail_control import CashMovementRecord


def fixture():
    store = InMemoryStore()
    record = store.shops[store.seed_demo_shop()]
    now = datetime.now(timezone.utc)
    zone = ZoneInfo(record.shop.timezone)
    today = now.astimezone(zone).date()
    product = next(iter(record.products.values()))
    return store, record, now, zone, today, product


def receipt(store, record, product, tender, when):
    key = str(uuid4())
    sale = store.create_sale(record, SaleCreate(
        lines=[SaleLine(product_id=product.id, quantity=1)], tender=tender,
    ), key, key)
    sale.created_at = when
    return sale


def expense(record, when, day, tender):
    item = ExpenseRecord(id=uuid4(), shop_id=record.shop.id, category="supplies",
                         occurred_on=day, amount_cents=40, tender=tender, status="confirmed",
                         created_at=when, confirmed_at=when)
    record.expenses[item.id] = item


def test_zero_opening_drawer_estimate_excludes_bank_and_keeps_cash_close_unknown():
    store, record, now, _, today, product = fixture()
    receipt(store, record, product, "cash", now)
    receipt(store, record, product, "bank", now)
    expense(record, now, today, "cash")
    expense(record, now, today, "bank")
    tool = toolset(record)["query_cashflow"][1]
    result = tool({"start_date": str(today), "end_date": str(today)})
    assert result["opening_basis"] == "assumed_zero"
    assert result["recorded_opening_cash_cents"] is None
    assert result["opening_cash_used_cents"] == 0
    assert result["recorded_movements_cents"] == {"sales": 150, "expenses": -40}
    assert result["estimated_ending_cash_cents"] == 110
    assert result["recorded_ending_cash_count_cents"] is None
    assert "starts at zero" in result["assumption_note"]
    preview = calculate_cash_preview(record, today)
    assert preview.requires_opening and preview.expected_cash_cents is None
    assert not record.cash_movements


def test_known_opening_replaces_the_zero_scenario():
    store, record, now, zone, today, product = fixture()
    receipt(store, record, product, "cash", now)
    opening = CashMovementRecord(id=uuid4(), shop_id=record.shop.id, kind="opening_balance",
                                 occurred_at=datetime.combine(today, time.min, zone),
                                 amount_cents=500, tender="cash", actor="Test", reason="Opening",
                                 created_at=now)
    record.cash_movements[opening.id] = opening
    result = toolset(record)["query_cashflow"][1]({"start_date": str(today), "end_date": str(today)})
    assert result["opening_basis"] == "explicit_opening"
    assert result["recorded_opening_cash_cents"] == 500
    assert result["estimated_ending_cash_cents"] == 650


def test_forecast_drawer_cash_separate_from_total_sales_projection():
    store, record, now, zone, today, product = fixture()
    start, end = today - timedelta(days=7), today - timedelta(days=1)
    for offset in range(7):
        day = start + timedelta(days=offset)
        when = datetime.combine(day, time(9), zone)
        receipt(store, record, product, "cash", when)
        receipt(store, record, product, "bank", when)
        expense(record, when, day, "cash")
    result = toolset(record)["run_forecast"][1]({
        "start_date": str(start), "end_date": str(end), "horizon_days": 7,
    })
    assert result["projection_sales_cents"] == 2100
    scenario = result["cash_scenario"]
    assert scenario["starting_cash_basis"] == "assumed_zero"
    assert scenario["starting_cash_cents"] == 770
    assert scenario["projected_cash_movement_cents"] == 770
    assert scenario["projected_ending_cash_cents"] == 1540
    assert "starts at zero" in scenario["assumption_note"]
