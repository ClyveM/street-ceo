from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from services.api.app import MuseAskRequest, SaleCreate, SaleLine
from services.api.sales_answers import repository_sales_answer
from services.api.test_reports_cash_close import setup, endpoint


def sale(app, record, index, quantity, key):
    product = list(record.products.values())[index]
    return endpoint(app, '/shops/{shop_id}/sales')(SaleCreate(lines=[SaleLine(product_id=product.id, quantity=quantity)], tender='cash'), record, key)


def ask(app, record, text):
    return endpoint(app, '/api/v1/shops/{shop_id}/muse')(MuseAskRequest(question=text), record)


def test_top_default_month_quantity_unique_receipts_and_saved_label():
    app, record = setup()
    sale(app, record, 0, 2, 'coke')
    sale(app, record, 1, 3, 'bread')
    record.idempotent_sales['duplicate'] = record.idempotent_sales['coke']
    list(record.products.values())[1].name = 'Current renamed bread'
    result = ask(app, record, 'What is my most selling product?')
    assert result.status == 'answered' and result.source == 'repository'
    assert 'Bread loaf' in result.answer and '3 unit(s)' in result.answer
    assert 'this month to date' in result.answer and 'Africa/Harare' in result.answer
    assert 'Current renamed bread' not in result.answer
    assert result.evidence_ids[0].startswith('sales-') and '_to_' in result.evidence_ids[0]


def test_ties_revenue_different_winner_and_no_sales():
    app, record = setup()
    empty = ask(app, record, 'What is my best-selling product today?')
    assert empty.status == 'answered' and 'No sales were recorded' in empty.answer
    sale(app, record, 0, 2, 'coke')
    sale(app, record, 1, 2, 'bread')
    tied = ask(app, record, 'Which product sells the most today?')
    assert 'Tied' in tied.answer and 'Coca-Cola 300ml' in tied.answer and 'Bread loaf' in tied.answer
    ranked = ask(app, record, 'What is my top product by revenue today?')
    assert 'Bread loaf' in ranked.answer and 'USD 3.60' in ranked.answer


def test_legacy_unknown_revenue_never_uses_current_prices():
    app, record = setup()
    coke, bread = list(record.products.values())[:2]
    receipt = endpoint(app, '/shops/{shop_id}/sales')(SaleCreate(lines=[SaleLine(product_id=coke.id, quantity=2), SaleLine(product_id=bread.id, quantity=1)], tender='cash'), record, 'multi')
    receipt.receipt_lines = []
    result = ask(app, record, 'What is my top product by revenue today?')
    assert result.status == 'needs_data' and 'cannot reliably rank' in result.answer
    quantity = ask(app, record, 'What is my most selling product today?')
    assert 'Coca-Cola 300ml' in quantity.answer and 'current catalogue' in quantity.answer


def test_total_and_periods_shop_dates_future_exclusion():
    app, record = setup()
    today = datetime.now(ZoneInfo(record.shop.timezone)).date()
    yesterday = sale(app, record, 0, 1, 'yesterday')
    yesterday.created_at = datetime.combine(today-timedelta(days=1), datetime.min.time(), ZoneInfo(record.shop.timezone)).astimezone(timezone.utc)
    future = sale(app, record, 1, 1, 'future')
    future.created_at = datetime.now(timezone.utc)+timedelta(days=1)
    result = ask(app, record, 'What are my total sales today?')
    assert 'USD 0.00' in result.answer and '0 transaction(s)' in result.answer
    result = ask(app, record, 'How much did I sell yesterday?')
    assert 'USD 1.50' in result.answer and '1 transaction(s)' in result.answer
    result = ask(app, record, 'What are my total sales in the last 20 days?')
    assert 'USD 1.50' in result.answer
    date_query = f'What are my total sales between {today-timedelta(days=1)} and {today-timedelta(days=1)}?'
    assert 'USD 1.50' in ask(app, record, date_query).answer


def test_unsupported_scope_and_period_not_silently_replaced():
    app, record = setup()
    for text in ('What is my top product last week?', 'What is my top product in October?', 'What are total sales last 0 days?', 'What are total sales last 999999999999 days?'):
        assert ask(app, record, text).status == 'needs_data'
    for text in ('Why is bread my best-selling product?', 'What are my total cash sales today?', 'How much profit today?', 'What are my total sales of Bread loaf today?'):
        assert repository_sales_answer(text, record) is None
