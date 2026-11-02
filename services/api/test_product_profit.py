from services.api.app import SaleCreate, SaleLine
from services.api.reports import sales_report
from services.api.test_reports_cash_close import setup, endpoint, sell


def test_profit_uses_saved_costs_and_unique_receipts():
    app, record = setup()
    sell(app, record)
    record.idempotent_sales['retry-alias'] = record.idempotent_sales['sale']
    product = next(iter(record.products.values()))
    product.unit_cost_micros = 5_000_000
    product.unit_price_cents = 999
    report = sales_report(record, preset='last1')
    assert report['summary']['gross_profit_micros'] == 500_000
    assert report['summary']['margin_bps'] == 3333
    assert report['products'][0]['gross_profit_micros'] == 500_000
    assert report['products'][0]['margin_bps'] == 3333


def test_zero_cost_loss_zero_revenue_and_signed_half_up_rounding():
    app, record = setup()
    products = list(record.products.values())
    for index, (price, cost) in enumerate(((2, 19999), (2, 20001), (0, 100), (100, 0))):
        product = products[index]
        product.unit_price_cents, product.unit_cost_micros = price, cost
        endpoint(app, '/shops/{shop_id}/sales')(SaleCreate(lines=[SaleLine(product_id=product.id, quantity=1)], tender='cash'), record, str(index))
    report = sales_report(record, preset='last1')
    rows = {row['product_id']: row for row in report['products']}
    positive, negative, free, zero_cost = (rows[str(product.id)] for product in products[:4])
    assert (positive['gross_profit_micros'], positive['margin_bps']) == (1, 1)
    assert (negative['gross_profit_micros'], negative['margin_bps']) == (-1, -1)
    assert (free['gross_profit_micros'], free['margin_bps']) == (-100, None)
    assert (zero_cost['gross_profit_micros'], zero_cost['margin_bps']) == (1_000_000, 10000)
    assert report['summary']['gross_profit_micros'] == 999900
    assert report['summary']['margin_bps'] == 9614


def test_unknown_costs_propagate_without_erasing_known_product_profit():
    app, record = setup()
    sell(app, record)
    bread = list(record.products.values())[1]
    bread.unit_cost_micros = None
    endpoint(app, '/shops/{shop_id}/sales')(SaleCreate(lines=[SaleLine(product_id=bread.id, quantity=1)], tender='bank'), record, 'unknown')
    report = sales_report(record, preset='last1')
    assert report['summary']['gross_profit_micros'] is None
    assert report['summary']['margin_bps'] is None
    rows = {row['product_id']: row for row in report['products']}
    assert rows[str(bread.id)]['gross_profit_micros'] is None
    assert rows[str(next(iter(record.products)))]['gross_profit_micros'] == 500_000


def test_legacy_mixed_unknown_product_revenue_keeps_complete_summary_profit():
    app, record = setup()
    coke, bread = list(record.products.values())[:2]
    receipt = endpoint(app, '/shops/{shop_id}/sales')(SaleCreate(lines=[SaleLine(product_id=coke.id, quantity=1), SaleLine(product_id=bread.id, quantity=1)], tender='cash'), record, 'legacy')
    receipt.receipt_lines = []
    report = sales_report(record, preset='last1')
    assert report['summary']['gross_profit_micros'] == 1_100_000
    assert all(row['gross_profit_micros'] is None and row['margin_bps'] is None for row in report['products'])
    # A legacy single-product receipt has exactly attributable saved totals.
    receipt.lines = [SaleLine(product_id=coke.id, quantity=1)]
    single = sales_report(record, preset='last1')['products'][0]
    assert single['gross_profit_micros'] == 1_100_000


def test_no_sales_known_zero_profit_undefined_margin():
    app, record = setup()
    summary = sales_report(record, preset='last1')['summary']
    assert summary['gross_profit_micros'] == 0
    assert summary['margin_bps'] is None
