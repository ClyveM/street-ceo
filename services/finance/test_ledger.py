from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from services.finance.ledger import Account, Ledger, Tender


WHEN = datetime(2026, 10, 30, 8, tzinfo=timezone.utc)


def assert_balanced(ledger: Ledger) -> None:
    assert all(entry.balanced for entry in ledger.entries)
    assert all(entry.total_debits == entry.total_credits for entry in ledger.entries)


def test_worked_demo_flow_reproduces_policy_totals() -> None:
    ledger = Ledger(shop_id="shop-1", currency="USD")
    prior = datetime(2026, 10, 29, 8, tzinfo=timezone.utc)
    ledger.opening_balance(source_id="open-cash", actor="owner", occurred_at=prior, amount="20.00", tender=Tender.CASH, source_known=True)
    ledger.opening_balance(source_id="open-bank", actor="owner", occurred_at=prior, amount="20.00", tender=Tender.BANK, source_known=True)
    ledger.purchase(source_id="purchase-1", actor="owner", occurred_at=WHEN, amount="10.00", tender=Tender.CASH, quantity=10, paid=True)
    ledger.sale(source_id="sale-1", actor="owner", occurred_at=WHEN, amount="3.00", tender=Tender.CASH, cogs="2.00", quantity=2, unit_price="1.50")
    ledger.purchase(source_id="purchase-2", actor="owner", occurred_at=WHEN, amount="14.00", tender=Tender.BANK, quantity=10, paid=True)
    ledger.sale(source_id="sale-2", actor="owner", occurred_at=WHEN, amount="4.80", tender=Tender.BANK, cogs="3.6666666666666666666666666667", quantity=3, unit_price="1.60")
    ledger.return_sale(source_id="return-1", original_sale_id="sale-2", actor="owner", occurred_at=WHEN,
                      refund="1.60", tender=Tender.BANK, original_cogs="1.2222222222222222222222222222", quantity=1, resalable=True)
    assert ledger.balance(Account.CASH) == Decimal("13.00")
    assert ledger.balance(Account.BANK) == Decimal("9.20")
    # balance() uses debit-minus-credit; revenue is credit-normal.
    assert ledger.balance(Account.SALES_REVENUE) == Decimal("-6.20")
    assert ledger.balance(Account.COGS) == Decimal("4.444444444444444444444444445")
    assert_balanced(ledger)


def test_expense_owner_and_opening_entries_use_distinct_accounts() -> None:
    ledger = Ledger(shop_id="shop-1")
    ledger.opening_balance(source_id="open", actor="a", occurred_at=WHEN, amount=20, tender="cash", source_known=False)
    ledger.owner_injection(source_id="inject", actor="a", occurred_at=WHEN, amount=5, tender="bank")
    ledger.owner_drawing(source_id="draw", actor="a", occurred_at=WHEN, amount=2, tender="cash")
    ledger.expense(source_id="expense", actor="a", occurred_at=WHEN, amount=3, tender="cash", category="airtime", paid=True)
    unpaid = ledger.expense(source_id="unpaid", actor="a", occurred_at=WHEN, amount=4, tender=None, category="rent", paid=False)
    assert "unknown_opening_balance_source" in ledger.entries[0].warnings
    assert "expense_payment_state_incomplete" in unpaid.warnings
    assert ledger.balance(Account.CASH) == Decimal("15")
    assert ledger.balance(Account.BANK) == Decimal("5")
    assert ledger.balance(Account.OPERATING_EXPENSE) == Decimal("7")
    assert ledger.balance(Account.OWNER_DRAWING) == Decimal("2")
    assert_balanced(ledger)


def test_return_requires_trace_and_damaged_return_records_stock_loss() -> None:
    ledger = Ledger(shop_id="shop-1")
    sale = ledger.sale(source_id="sale", actor="a", occurred_at=WHEN, amount=10, tender="cash", cogs=6, quantity=1, unit_price=10)
    returned = ledger.return_sale(source_id="return", original_sale_id=None, actor="a", occurred_at=WHEN,
                                  refund=10, tender="cash", original_cogs=6, quantity=1, resalable=False)
    assert "unlinked_return_review_required" in returned.warnings
    assert "damaged_return_stock_loss" in returned.warnings
    assert ledger.balance(Account.STOCK_LOSS) == Decimal("6")
    assert ledger.balance(Account.INVENTORY) == Decimal("-6")
    assert ledger.balance(Account.COGS) == Decimal("0")
    assert_balanced(ledger)


def test_reversal_is_append_only_and_exact_opposite() -> None:
    ledger = Ledger(shop_id="shop-1")
    sale = ledger.sale(source_id="sale", actor="a", occurred_at=WHEN, amount=10, tender="cash", cogs=4, quantity=1, unit_price=10)
    reversal = ledger.reverse(sale.entry_id, source_id="sale-correction", actor="a", occurred_at=WHEN)
    assert len(ledger.entries) == 2
    assert reversal.reversal_of == sale.entry_id
    assert ledger.balance(Account.CASH) == 0
    assert ledger.balance(Account.SALES_REVENUE) == 0
    assert ledger.balance(Account.COGS) == 0
    assert_balanced(ledger)
    with pytest.raises(ValueError, match="already reversed"):
        ledger.reverse(sale.entry_id, source_id="sale-correction-again", actor="a", occurred_at=WHEN)
    with pytest.raises(ValueError, match="cannot be reversed"):
        ledger.reverse(reversal.entry_id, source_id="double-reversal", actor="a", occurred_at=WHEN)


def test_cash_change_is_metadata_only_and_bank_cannot_have_change() -> None:
    ledger = Ledger(shop_id="shop-1")
    sale = ledger.sale(source_id="cash-sale", actor="a", occurred_at=WHEN, amount=1.50, tender="cash",
                       cogs=1, quantity=1, unit_price=1.50, amount_received=2, change=0.50)
    assert sale.metadata["amount_received"] == "2"
    assert sale.metadata["change"] == "0.5"
    assert ledger.balance(Account.CASH) == Decimal("1.50")
    with pytest.raises(ValueError, match="bank tender"):
        ledger.sale(source_id="bank-sale", actor="a", occurred_at=WHEN, amount=1.50, tender="bank",
                    cogs=1, quantity=1, amount_received=2, change=0.50)


def test_profitability_is_ledger_derived_and_discloses_missing_cogs() -> None:
    ledger = Ledger(shop_id="shop-1")
    ledger.sale(source_id="sale", actor="a", occurred_at=WHEN, amount=1.50, tender="cash", cogs=0.50, quantity=1)
    ledger.expense(source_id="expense", actor="a", occurred_at=WHEN, amount=0.25, tender="cash", category="airtime", paid=True)
    report = ledger.profitability(start=WHEN, end=WHEN)
    assert report.net_revenue == Decimal("1.50")
    assert report.gross_profit == Decimal("1.00")
    assert report.net_profit == Decimal("0.75")
    incomplete = Ledger(shop_id="shop-1")
    incomplete.sale(source_id="sale", actor="a", occurred_at=WHEN, amount=1.50, tender="cash", cogs=None, quantity=1)
    incomplete_report = incomplete.profitability(start=WHEN, end=WHEN)
    assert incomplete_report.gross_profit is None
    assert "profitability_incomplete_missing_cost_of_sales" in incomplete_report.warnings


def test_daily_close_is_reproducible_locked_and_surfaces_variance() -> None:
    ledger = Ledger(shop_id="shop-1")
    ledger.opening_balance(source_id="open", actor="a", occurred_at=datetime(2026, 10, 29, 8, tzinfo=timezone.utc), amount=20, tender="cash", source_known=True)
    ledger.sale(source_id="sale", actor="a", occurred_at=WHEN, amount=3, tender="cash", cogs=1, quantity=1, unit_price=3)
    close = ledger.close_day(business_date=date(2026, 10, 30), timezone_name="Africa/Harare", actual_cash=24, actual_bank=None)
    assert close.expected[Tender.CASH] == Decimal("23")
    assert close.variance[Tender.CASH] == Decimal("1")
    assert "unexplained_cash_variance" in close.warnings
    assert "missing_bank_confirmation" in close.warnings
    with pytest.raises(ValueError, match="already locked"):
        ledger.close_day(business_date=date(2026, 10, 30), timezone_name="Africa/Harare", actual_cash=24, actual_bank=None)


def test_daily_close_counts_same_day_opening_and_reversal_movements() -> None:
    ledger = Ledger(shop_id="shop-1")
    same_day = datetime(2026, 10, 30, 8, tzinfo=timezone.utc)
    sale = ledger.sale(source_id="sale", actor="a", occurred_at=same_day, amount=3, tender="cash", cogs=1, quantity=1)
    ledger.reverse(sale.entry_id, source_id="sale-reversal", actor="a", occurred_at=datetime(2026, 10, 30, 9, tzinfo=timezone.utc))
    ledger.opening_balance(source_id="open", actor="a", occurred_at=datetime(2026, 10, 30, 7, tzinfo=timezone.utc), amount=20, tender="cash", source_known=True)
    close = ledger.close_day(business_date=date(2026, 10, 30), timezone_name="Africa/Harare", actual_cash=20, actual_bank=0)
    assert close.opening[Tender.CASH] == Decimal("20")
    assert close.expected[Tender.CASH] == Decimal("20")
