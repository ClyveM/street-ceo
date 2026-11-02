"""Independent repository-evidence answers; synthetic receipts, no cloud/live database."""
from datetime import datetime, timezone
from uuid import uuid4

from services.ai.boundary import StructuredAI
from services.api import app as api
from services.api import reports
from services.api import sales_answers
from services.api.app import InMemoryStore, MuseAskRequest, Sale, SaleLine, SaleReceiptLine, create_app
from services.api.persistence import Settings


class NoProvider:
    def complete(self, request):
        raise AssertionError('A repository-only factual question must not call Muse')


def setup(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            instant = cls(2026, 11, 2, 10, tzinfo=timezone.utc)
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)
    monkeypatch.setattr(api, 'datetime', Clock)
    monkeypatch.setattr(reports, 'datetime', Clock)
    monkeypatch.setattr(sales_answers, 'datetime', Clock)
    store = InMemoryStore()
    app = create_app(store, Settings(demo_seed_enabled=True), muse_ai=StructuredAI(NoProvider()))
    record = store.shops[next(iter(store.shops))]
    endpoint = next(route.endpoint for route in app.routes if route.path == '/api/v1/shops/{shop_id}/muse')
    return record, lambda question: endpoint(MuseAskRequest(question=question), record)


def receipt(record, product, qty, unit, name=None, when=None, snapshot=True):
    product = list(record.products.values())[product]
    line = SaleLine(product_id=product.id, quantity=qty)
    total = qty * unit
    sale = Sale(id=uuid4(), shop_id=record.shop.id, lines=[line], tender='cash', total_cents=total,
                created_at=when or datetime(2026, 11, 2, 9, tzinfo=timezone.utc),
                receipt_lines=[SaleReceiptLine(product_id=product.id, product_name=name or product.name,
                                              sku=product.sku, quantity=qty, unit_price_cents=unit,
                                              line_total_cents=total)] if snapshot else [])
    record.idempotent_sales[str(sale.id)] = ('synthetic', sale)
    return sale


def test_units_default_and_explicit_revenue_choose_different_saved_products(monkeypatch):
    record, ask = setup(monkeypatch)
    receipt(record, 0, 6, 150, 'Historic Cola')
    receipt(record, 1, 5, 200, 'Historic Bread')
    # Current catalogue labels and prices must not rewrite saved evidence.
    list(record.products.values())[0].name = 'Changed Cola'
    list(record.products.values())[1].unit_price_cents = 1
    quantity = ask('What is my most selling product today?')
    revenue = ask('What is my top selling product by revenue today?')
    assert quantity.status == revenue.status == 'answered'
    assert quantity.source == revenue.source == 'repository'
    assert 'Historic Cola' in quantity.answer and '6' in quantity.answer
    assert 'Historic Bread' in revenue.answer and '10.00' in revenue.answer
    assert quantity.evidence_ids and revenue.evidence_ids


def test_ties_and_empty_shop_are_explicit_repository_facts(monkeypatch):
    record, ask = setup(monkeypatch)
    empty = ask('What is my most selling product today?')
    assert empty.source == 'repository' and 'no' in empty.answer.lower()
    assert empty.status != 'unavailable'
    receipt(record, 0, 2, 150)
    receipt(record, 1, 2, 180)
    tied = ask('What is my most selling product today?')
    assert 'tie' in tied.answer.lower()
    assert 'Coca-Cola 300ml' in tied.answer and 'Bread loaf' in tied.answer


def test_today_uses_shop_timezone_unique_receipts_and_no_future_sales(monkeypatch):
    record, ask = setup(monkeypatch)
    receipt(record, 1, 20, 180, when=datetime(2026, 11, 1, 21, 59, tzinfo=timezone.utc))
    included = receipt(record, 0, 3, 150, when=datetime(2026, 11, 1, 22, tzinfo=timezone.utc))
    record.idempotent_sales['same-receipt-retry'] = ('synthetic', included)
    receipt(record, 1, 40, 180, when=datetime(2026, 11, 2, 11, tzinfo=timezone.utc))
    result = ask('What is my most selling product today?')
    assert result.source == 'repository' and 'Coca-Cola 300ml' in result.answer
    assert '3' in result.answer and 'Bread loaf' not in result.answer
    total = ask('What are my total sales today?')
    assert total.source == 'repository' and '4.50' in total.answer


def test_revenue_ranking_refuses_unknown_old_mixed_receipt_line_prices(monkeypatch):
    record, ask = setup(monkeypatch)
    coke, bread = list(record.products)[:2]
    sale = Sale(id=uuid4(), shop_id=record.shop.id, lines=[SaleLine(product_id=coke, quantity=2),
                SaleLine(product_id=bread, quantity=1)], tender='cash', total_cents=480,
                created_at=datetime(2026, 11, 2, 9, tzinfo=timezone.utc))
    record.idempotent_sales['old-mixed'] = ('synthetic', sale)
    revenue = ask('What is my top selling product by revenue today?')
    assert revenue.source == 'repository'
    assert revenue.status == 'needs_data'
    assert revenue.missing_data
    quantity = ask('What is my most selling product today?')
    assert quantity.status == 'answered' and 'Coca-Cola 300ml' in quantity.answer


def test_profit_missing_cost_remains_unknown_instead_of_becoming_sales_total(monkeypatch):
    record, ask = setup(monkeypatch)
    receipt(record, 0, 1, 150)
    result = ask('What profit did I make today?')
    assert result.status == 'needs_data'
    assert 'cannot calculate profit' in result.answer
    assert any('COGS' in value for value in result.missing_data)


def test_unsupported_filtered_rankings_and_periods_are_not_answered_as_all_sales(monkeypatch):
    record, ask = setup(monkeypatch)
    receipt(record, 0, 1, 150)
    for question in ('What is my top product by cash sales today?',
                     'What is my top product by bank revenue today?',
                     'What is my top product by net sales today?'):
        assert sales_answers.repository_sales_answer(question, record) is None
    for question in ('What is my top product last week?',
                     'What are my total sales last 0 days?',
                     'What are my total sales between 2026-11-04 and 2026-11-02?'):
        response = ask(question)
        assert response.source == 'repository' and response.status == 'needs_data'
    general = ask('What should I focus on?')
    assert general.source == 'fallback' and general.status == 'unavailable'
