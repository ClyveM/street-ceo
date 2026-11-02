"""Saved stock counts remain scoped, ordered and read-only across restarts."""
from copy import deepcopy
from datetime import datetime, timezone
from uuid import UUID

from services.api.test_sqlite_store import SHOP, build, call


def test_history_scoped_drafts_confirmed_and_sqlite_reopen(tmp_path):
    path = tmp_path / 'counts.sqlite3'
    app = build(path)
    route = f'/api/v1/shops/{SHOP}/stock-takes'
    assert call(app, 'GET', route).json() == []
    product = next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    body = {'mode': 'on_demand', 'count_date': '2026-11-02', 'actor': 'test owner', 'notes': 'saved count', 'lines': [{'product_id': str(product.id), 'counted_qty': product.stock_qty}]}
    first = call(app, 'POST', route, body=body).json()
    confirmed = call(app, 'POST', f"{route}/{first['id']}/confirm")
    assert confirmed.status_code == 200
    second = call(app, 'POST', route, body={**body, 'mode': 'monthly'}).json()
    # Controlled equal timestamps exercise deterministic ID ordering, not timing.
    with app.state.store.transaction():
        record = app.state.store.shops[UUID(SHOP)]
        for item in record.stock_takes.values():
            item.created_at = datetime(2026, 11, 2, tzinfo=timezone.utc)
    record = app.state.store.shops[UUID(SHOP)]
    before = deepcopy(record)
    result = call(app, 'GET', route)
    assert result.status_code == 200
    rows = result.json()
    assert [row['id'] for row in rows] == sorted([first['id'], second['id']], reverse=True)
    assert {row['status'] for row in rows} == {'draft', 'confirmed'}
    assert all(row['shop_id'] == SHOP for row in rows)
    assert all(row['expected_snapshot'][str(product.id)] == product.stock_qty for row in rows)
    assert app.state.store.shops[UUID(SHOP)] == before
    other = call(app, 'POST', '/shops', body={'name': 'Other isolated shop'}).json()['id']
    other_route = f'/api/v1/shops/{other}/stock-takes'
    assert call(app, 'GET', other_route, shop_header=other).json() == []
    assert call(app, 'GET', other_route).status_code == 403
    assert call(app, 'GET', route, shop_header=other).status_code == 403
    app.state.store.close()
    app = build(path)
    assert call(app, 'GET', route).json() == rows
    assert call(app, 'GET', other_route, shop_header=other).json() == []
    reopened = app.state.store.shops[UUID(SHOP)]
    assert len(reopened.stock_adjustments) == 0
    assert reopened.products[product.id].stock_qty == product.stock_qty
    assert reopened.idempotent_sales == before.idempotent_sales
    app.state.store.close()
