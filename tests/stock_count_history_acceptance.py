"""Independent stock-count history contracts on temporary SQLite shops."""
from copy import deepcopy
from datetime import datetime, timezone
from uuid import UUID

from services.api.test_sqlite_store import SHOP, build, call


def create(app, product, key, count, count_date='2026-11-02'):
    route = f'/api/v1/shops/{SHOP}/stock-takes'
    response = call(app, 'POST', route, key, {
        'mode': 'on_demand', 'count_date': count_date, 'actor': 'Synthetic QA', 'notes': 'Physical fixture count',
        'lines': [{'product_id': str(product), 'counted_qty': count}]})
    assert response.status_code == 201
    return response.json()


def test_history_is_newest_created_not_count_date_and_get_does_not_adjust_stock(tmp_path):
    app = build(tmp_path/'counts.sqlite3')
    product = next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    older = create(app, product.id, 'old', 0, '2026-11-02')
    newer = create(app, product.id, 'new', 7, '2026-10-01')
    with app.state.store.transaction():
        record = app.state.store.shops[UUID(SHOP)]
        record.stock_takes[UUID(older['id'])].created_at = datetime(2026, 11, 1, tzinfo=timezone.utc)
        record.stock_takes[UUID(newer['id'])].created_at = datetime(2026, 11, 2, tzinfo=timezone.utc)
    before = deepcopy(app.state.store.shops[UUID(SHOP)])
    response = call(app, 'GET', f'/api/v1/shops/{SHOP}/stock-takes')
    assert response.status_code == 200
    assert [item['id'] for item in response.json()] == [newer['id'], older['id']]
    assert app.state.store.shops[UUID(SHOP)] == before
    assert all(item['status'] == 'draft' for item in response.json())
    app.state.store.close()


def test_confirmed_history_reopens_with_exact_count_and_no_repeat_adjustment(tmp_path):
    path = tmp_path/'counts.sqlite3'
    app = build(path)
    product = next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    stock = product.stock_qty
    draft = create(app, product.id, 'draft', stock-2)
    route = f"/api/v1/shops/{SHOP}/stock-takes/{draft['id']}/confirm"
    confirmed = call(app, 'POST', route)
    assert confirmed.status_code == 200
    snapshot = deepcopy(app.state.store.shops[UUID(SHOP)])
    app.state.store.close()
    app = build(path)
    for _ in range(2):
        rows = call(app, 'GET', f'/api/v1/shops/{SHOP}/stock-takes').json()
        assert len(rows) == 1 and rows[0]['status'] == 'confirmed'
        assert rows[0]['lines'][0]['counted_qty'] == stock-2
        assert rows[0]['expected_snapshot'][str(product.id)] == stock
        assert rows[0]['confirmed_at']
    assert app.state.store.shops[UUID(SHOP)] == snapshot
    assert call(app, 'POST', route).json() == confirmed.json()
    assert app.state.store.shops[UUID(SHOP)].products[product.id].stock_qty == stock-2
    assert len(app.state.store.shops[UUID(SHOP)].stock_adjustments) == 1
    assert not app.state.store.shops[UUID(SHOP)].idempotent_sales
    app.state.store.close()


def test_list_filters_foreign_shop_record_even_if_corrupted_map_contains_it(tmp_path):
    app = build(tmp_path/'counts.sqlite3')
    product = next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    own = create(app, product.id, 'own', 0)
    other = call(app, 'POST', '/shops', body={'name': 'Isolated other shop'}).json()['id']
    with app.state.store.transaction():
        record = app.state.store.shops[UUID(SHOP)]
        foreign = deepcopy(record.stock_takes[UUID(own['id'])])
        foreign.shop_id = UUID(other)
        foreign.id = UUID('ffffffff-ffff-ffff-ffff-ffffffffffff')
        record.stock_takes[foreign.id] = foreign
    rows = call(app, 'GET', f'/api/v1/shops/{SHOP}/stock-takes').json()
    assert [item['id'] for item in rows] == [own['id']]
    assert call(app, 'GET', f'/api/v1/shops/{other}/stock-takes', shop_header=other).json() == []
    assert call(app, 'GET', f'/api/v1/shops/{SHOP}/stock-takes', shop_header=other).status_code == 403
    app.state.store.close()
