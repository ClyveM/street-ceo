"""Independent report-level financial examples using exact Decimal policy references."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

import pytest

from services.api.app import InMemoryStore, Sale, SaleLine, SaleReceiptLine
from services.api import reports
from services.api.reports import sales_report


@pytest.fixture(autouse=True)
def fixed_report_clock(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):
            instant=cls(2026,11,2,20,tzinfo=timezone.utc)
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)
    monkeypatch.setattr(reports,'datetime',Clock)


def record():
    store=InMemoryStore()
    return store.shops[store.seed_demo_shop()]


def saved(record, index, cents, cost, when=None):
    product=list(record.products.values())[index]
    sale=Sale(id=uuid4(),shop_id=record.shop.id,lines=[SaleLine(product_id=product.id,quantity=1)],
              tender='cash',total_cents=cents,cogs_micros=cost,
              created_at=when or datetime(2026,11,2,9,tzinfo=timezone.utc),
              receipt_lines=[SaleReceiptLine(product_id=product.id,product_name=product.name,sku=product.sku,
                                            quantity=1,unit_price_cents=cents,line_total_cents=cents,
                                            unit_cost_micros=cost,line_cogs_micros=cost)])
    record.idempotent_sales[str(sale.id)]=('fixture',sale)
    return sale


@pytest.mark.parametrize('cents,cost',[(2,19999),(2,20001),(100,3000000),(100,0),(0,500),(0,0),(1,None)])
def test_report_profit_and_margin_match_independent_decimal_reference(cents,cost):
    r=record();saved(r,0,cents,cost)
    report=sales_report(r,start_date=datetime(2026,11,2).date(),end_date=datetime(2026,11,2).date())
    expected_profit=None if cost is None else cents*10000-cost
    expected_margin=None if cost is None or cents==0 else int((Decimal(expected_profit)*Decimal(10000)/Decimal(cents*10000)).quantize(Decimal(1),rounding=ROUND_HALF_UP))
    for actual in (report['summary'],report['products'][0]):
        assert actual['gross_profit_micros']==expected_profit
        assert actual['margin_bps']==expected_margin


def test_exact_profit_aggregates_before_display_rounding_and_snapshot_costs_are_immutable():
    r=record();first=saved(r,0,1,5000);saved(r,1,1,5000)
    r.idempotent_sales['same-receipt-again']=('fixture',first)
    for product in r.products.values():
        product.unit_cost_micros=999999999
        product.unit_price_cents=999999
    result=sales_report(r,preset='last90')
    assert [p['gross_profit_micros'] for p in result['products']]==[5000,5000]
    assert result['summary']['gross_profit_micros']==10000
    assert result['summary']['margin_bps']==5000
    assert result['summary']['transaction_count']==2


def test_shop_local_period_filters_costs_and_profits_together_without_future_leak():
    r=record()
    saved(r,0,100,500000,datetime(2026,11,1,21,59,tzinfo=timezone.utc))
    saved(r,0,100,1000000,datetime(2026,11,1,22,tzinfo=timezone.utc))
    saved(r,1,999,1,datetime(2026,11,2,22,tzinfo=timezone.utc))
    result=sales_report(r,start_date=datetime(2026,11,2).date(),end_date=datetime(2026,11,2).date())
    assert result['summary']['sales_total_cents']==100
    assert result['summary']['cogs_micros']==1000000
    assert result['summary']['gross_profit_micros']==0
    assert result['summary']['margin_bps']==0
    assert len(result['products'])==1
