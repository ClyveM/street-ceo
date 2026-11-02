from uuid import UUID, uuid4

from services.ai.catalogue_voice import resolve_catalogue_voice
from services.api.app import Product
from services.api.test_sqlite_store import SHOP, build, call


def resolver(text, products):
    return resolve_catalogue_voice(text, products, provider=None)


def test_100_items_preserved_focused_reply_after_sqlite_restart_then_full_confirmation(tmp_path, monkeypatch):
    monkeypatch.setenv('STREET_CEO_TRACE_DATABASE', str(tmp_path/'trace.sqlite3'))
    path = tmp_path/'shop.sqlite3'
    app = build(path, resolver)
    with app.state.store.transaction():
        record = app.state.store.shops[UUID(SHOP)]
        record.products = {}
        for i in range(100):
            suffix = chr(97+i//26)+chr(97+i%26)
            product = Product(id=uuid4(), shop_id=UUID(SHOP), sku=f'BASKET-{suffix}', name=f'Basket item {suffix}', unit_price_cents=100, stock_qty=2)
            record.products[product.id] = product
    products = list(app.state.store.shops[UUID(SHOP)].products.values())
    route = f'/api/v1/shops/{SHOP}/voice'
    text = ', '.join('one '+product.name for product in products[:-1])+', one mystery widget'
    assert len(text) > 1000
    first = call(app, 'POST', route+'/transcript', 'first', {'transcript': text})
    assert first.status_code == 200, first.text
    context = first.json()
    assert context['status'] == 'needs_clarification' and context['lines'] == []
    assert len(context['retained_lines']) == 99 and len(context['pending_items']) == 1
    assert 'repeat the complete' not in context['clarification_question'].lower()
    bad = call(app, 'POST', route+'/commit', 'partial', {'review_id': context['request_id'], 'lines': [{'product_id': str(products[0].id), 'quantity': 1}], 'tender': 'bank', 'match_confirmed': True})
    assert bad.status_code == 409
    app.state.store.close()
    app = build(path, resolver)
    body = {'transcript': products[-1].name, 'clarification_of': context['request_id']}
    response = call(app, 'POST', route+'/transcript', 'focused', body)
    assert response.status_code == 200, response.text
    reviewed = response.json()
    assert reviewed['status'] == 'needs_match_confirmation' and len(reviewed['lines']) == 100
    assert not reviewed['pending_items']
    assert call(app, 'POST', route+'/transcript', 'focused', body).json() == reviewed
    assert call(app, 'POST', route+'/transcript', 'fork', body).status_code == 409
    commit = {'review_id': reviewed['request_id'], 'lines': [{'product_id': row['product_id'], 'quantity': row['quantity']} for row in reviewed['lines']], 'tender': 'bank'}
    assert call(app, 'POST', route+'/commit', 'payment', commit).status_code == 409
    paid = call(app, 'POST', route+'/commit', 'payment', {**commit, 'match_confirmed': True})
    assert paid.status_code == 200, paid.text
    assert paid.json()['total_cents'] == 10000
    assert len(app.state.store.shops[UUID(SHOP)].idempotent_sales) == 1
    app.state.store.close()


def test_multiple_pending_missing_quantity_and_product_only_answers(tmp_path, monkeypatch):
    monkeypatch.setenv('STREET_CEO_TRACE_DATABASE', str(tmp_path/'trace.sqlite3'))
    app = build(tmp_path/'shop.sqlite3', resolver)
    route = f'/api/v1/shops/{SHOP}/voice/transcript'
    initial = call(app, 'POST', route, 'start', {'transcript': 'one coke, bread, two mystery widget'}).json()
    assert len(initial['retained_lines']) == 1
    assert len(initial['pending_items']) == 2
    assert initial['clarification_product_name'] == 'Bread loaf'
    follow = call(app, 'POST', route, 'quantity', {'transcript': 'one', 'clarification_of': initial['request_id']}).json()
    assert len(follow['retained_lines']) == 2 and len(follow['pending_items']) == 1
    invalid = call(app, 'POST', route, 'two-items', {'transcript': 'one milk two sugar', 'clarification_of': follow['request_id']}).json()
    assert invalid['lines'] == [] and len(invalid['retained_lines']) == 2 and len(invalid['pending_items']) == 1
    final = call(app, 'POST', route, 'last-item', {'transcript': 'milk', 'clarification_of': invalid['request_id']}).json()
    assert final['status'] == 'needs_match_confirmation'
    assert {line['product_name']: line['quantity'] for line in final['lines']} == {'Coca-Cola 300ml': 1, 'Bread loaf': 1, 'Milk 500ml': 2}
    assert app.state.store.shops[UUID(SHOP)].idempotent_sales == {}
    app.state.store.close()


def test_duplicate_replacement_cannot_drop_pending_or_change_retained_quantity(tmp_path, monkeypatch):
    monkeypatch.setenv('STREET_CEO_TRACE_DATABASE', str(tmp_path/'trace.sqlite3'))
    app = build(tmp_path/'shop.sqlite3', resolver)
    route = f'/api/v1/shops/{SHOP}/voice/transcript'
    first = call(app, 'POST', route, 'start', {'transcript': 'one coke, one mystery'}).json()
    duplicate = call(app, 'POST', route, 'duplicate', {'transcript': 'two coke', 'clarification_of': first['request_id']}).json()
    assert duplicate['status'] == 'needs_clarification' and not duplicate['lines']
    assert duplicate['retained_lines'][0]['quantity'] == 1 and len(duplicate['pending_items']) == 1
    assert 'already retained' in duplicate['clarification_question']
    app.state.store.close()


def test_provider_grounded_matches_preserved_but_changed_quantities_not_trusted():
    products = [
        {'product_id': 'coke', 'name': 'Coca-Cola 300ml', 'sku': 'COKE-300'},
        {'product_id': 'bread', 'name': 'Bread loaf', 'sku': 'BREAD-700'},
    ]
    class Provider:
        changed = False
        def complete(self, request):
            return {'segments': [
                {'segment_id': 0, 'product_id': 'coke', 'quantity': 1, 'resolution': 'matched'},
                {'segment_id': 1, 'product_id': 'bread', 'quantity': 9 if self.changed else 2, 'resolution': 'uncertain'},
                {'segment_id': 2, 'product_id': None, 'quantity': 1, 'resolution': 'unknown'},
            ]}
    provider = Provider()
    result = resolve_catalogue_voice('one coke, two bread glove, one mystery', products, provider=provider)
    assert result.lines == () and len(result.retained_lines) == 2 and len(result.pending_items) == 1
    assert result.retained_lines[1].quantity == 2 and result.provider_called is True
    provider.changed = True
    invalid = resolve_catalogue_voice('one coke, two bread glove, one mystery', products, provider=provider)
    assert invalid.lines == () and len(invalid.retained_lines) == 1
    assert invalid.retained_lines[0].product_id == 'coke'
    assert len(invalid.pending_items) == 2


def test_missing_quantity_does_not_call_provider_and_over_limit_is_nonactionable():
    products = [{'product_id': 'coke', 'name': 'Coca-Cola 300ml', 'sku': 'COKE-300'}, {'product_id': 'bread', 'name': 'Bread loaf', 'sku': 'BREAD-700'}]
    class NoCall:
        def complete(self, request):
            raise AssertionError('Missing quantity should be asked locally')
    partial = resolve_catalogue_voice('one coke, bread', products, provider=NoCall())
    assert partial.provider_called is False and len(partial.retained_lines) == 1
    assert partial.pending_items[0].product_id == 'bread'
    oversized = resolve_catalogue_voice(', '.join('one coke' for _ in range(101)), products, provider=None)
    assert not oversized.lines and not oversized.retained_lines


def test_explicit_active_removal_dangling_reply_and_stale_quantity_target(tmp_path, monkeypatch):
    monkeypatch.setenv('STREET_CEO_TRACE_DATABASE', str(tmp_path/'trace.sqlite3'))
    app = build(tmp_path/'shop.sqlite3', resolver)
    route = f'/api/v1/shops/{SHOP}/voice/transcript'
    first = call(app, 'POST', route, 'start', {'transcript': 'one coke, two mystery, three unknown'}).json()
    removed = call(app, 'POST', route, 'remove', {'transcript': 'remove this item', 'clarification_of': first['request_id']}).json()
    assert len(removed['retained_lines']) == 1 and len(removed['pending_items']) == 1
    assert removed['pending_items'][0]['quantity'] == 3
    dangling = call(app, 'POST', route, 'dangling', {'transcript': 'one bread and', 'clarification_of': removed['request_id']}).json()
    assert dangling['status'] == 'needs_clarification' and len(dangling['pending_items']) == 1
    final = call(app, 'POST', route, 'last-remove', {'transcript': 'remove item', 'clarification_of': dangling['request_id']}).json()
    assert final['status'] == 'needs_match_confirmation' and len(final['lines']) == 1
    known = call(app, 'POST', route, 'known', {'transcript': 'one coke, bread'}).json()
    with app.state.store.transaction():
        product = app.state.store.shops[UUID(SHOP)].products[UUID(known['pending_items'][0]['product_id'])]
        product.sku = 'RENAMED-SKU'
    stale = call(app, 'POST', route, 'stale', {'transcript': 'one', 'clarification_of': known['request_id']})
    assert stale.status_code == 409
    app.state.store.close()
