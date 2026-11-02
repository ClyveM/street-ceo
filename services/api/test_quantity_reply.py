"""A scoped quantity reply must reuse one grounded item, never drop a basket."""
from uuid import UUID

import pytest

from services.ai.catalogue_voice import resolve_catalogue_voice
from services.api.test_sqlite_store import SHOP, build, call
from services.api.voice_boundary import parse_quantity_reply


CHIPS = "00000000-0000-0000-0000-000000000005"


class MissingQuantityProvider:
    def __init__(self):
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        return {"segments": [{"segment_id": segment["segment_id"], "product_id": CHIPS, "quantity": segment["quantity"], "resolution": "uncertain"} for segment in request.trusted_context["segments"]]}


@pytest.mark.parametrize("heard", ["Potato chips", "putado chips naples"])
@pytest.mark.parametrize("quantity", ["one", "1"])
def test_scoped_single_item_quantity_reuses_durable_target_without_second_resolution(tmp_path, monkeypatch, heard, quantity):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.sqlite3"))
    provider = MissingQuantityProvider()
    resolver = lambda transcript, products: resolve_catalogue_voice(transcript, products, provider=provider)
    path = tmp_path / "shop.sqlite3"
    app = build(path, resolver)
    route = f"/api/v1/shops/{SHOP}/voice/transcript"
    response = call(app, "POST", route, "missing", {"transcript": heard})
    missing = response.json()
    assert missing["status"] == "needs_clarification", response.text
    assert missing["clarification_product_id"] == CHIPS
    assert missing["clarification_product_name"] == "Potato chips"
    assert "Say just the quantity" in missing["clarification_question"]
    assert missing["lines"] == []
    assert provider.calls == (0 if heard == "Potato chips" else 1)
    app.state.store.close()

    def no_resolution(*args):
        raise AssertionError("quantity reply must not resolve the already grounded product again")
    app = build(path, no_resolution)
    initial_stock = app.state.store.shops[UUID(SHOP)].products[UUID(CHIPS)].stock_qty
    body = {"transcript": quantity, "clarification_of": missing["request_id"]}
    response = call(app, "POST", route, "quantity", body)
    proposal = response.json()
    assert response.status_code == 200, response.text
    assert proposal["status"] == "needs_match_confirmation"
    assert proposal["resolution_source"] == "local_clarification"
    assert proposal["provider_called"] is False
    assert proposal["lines"] == [{"product_id": CHIPS, "product_name": "Potato chips", "quantity": 1}]
    assert proposal["requires_match_confirmation"] is True
    assert call(app, "POST", route, "quantity", body).json() == proposal
    assert call(app, "POST", route, "quantity", {**body, "transcript": "two"}).status_code == 409
    record = app.state.store.shops[UUID(SHOP)]
    assert record.products[UUID(CHIPS)].stock_qty == initial_stock
    assert record.idempotent_sales == {}
    app.state.store.close()


@pytest.mark.parametrize("heard", ["chips unicorn", "putado chips naples unicorn", "putado chips naples and unicorn", "Potato chips and bread"])
def test_unresolved_extra_words_or_items_never_become_actionable_partial_basket(heard):
    catalogue = [
        {"product_id": CHIPS, "name": "Potato chips", "sku": "CHIPS-100"},
        {"product_id": "bread", "name": "Bread loaf", "sku": "BREAD-700"},
    ]
    result = resolve_catalogue_voice(heard, catalogue, provider=MissingQuantityProvider())
    assert result.status == "needs_clarification"
    assert result.lines == ()
    if ' and ' in heard:
        # The new retained-basket flow may ask a focused quantity for the
        # first grounded item, while preserving every other unresolved slot.
        assert result.clarification_product_id == CHIPS
        assert result.retained_lines == ()
        assert len(result.pending_items) == 2
        assert [item.slot_id for item in result.pending_items] == [0, 1]
        assert all(item.quantity is None for item in result.pending_items)
        assert result.pending_items[0].product_id == CHIPS
        assert result.pending_items[1].heard == ('bread' if heard == 'Potato chips and bread' else 'unicorn')
        assert result.pending_items[1].product_id == ('bread' if heard == 'Potato chips and bread' else None)
        assert 'How many Potato chips?' in result.question
    else:
        assert result.clarification_product_id is None


@pytest.mark.parametrize('heard', ['Potato chips and bread', 'putado chips naples and unicorn'])
def test_focused_quantity_keeps_other_pending_item_and_cannot_commit_partial(tmp_path, monkeypatch, heard):
    monkeypatch.setenv('STREET_CEO_TRACE_DATABASE', str(tmp_path / 'traces.sqlite3'))
    provider = MissingQuantityProvider()
    resolver = lambda text, products: resolve_catalogue_voice(text, products, provider=provider)
    app = build(tmp_path / 'shop.sqlite3', resolver)
    route = f'/api/v1/shops/{SHOP}/voice'
    initial = call(app, 'POST', route+'/transcript', 'start', {'transcript': heard}).json()
    assert len(initial['pending_items']) == 2 and initial['lines'] == []
    follow = call(app, 'POST', route+'/transcript', 'quantity', {'transcript': 'one', 'clarification_of': initial['request_id']}).json()
    assert follow['status'] == 'needs_clarification' and follow['lines'] == []
    assert follow['retained_lines'] == [{'product_id': CHIPS, 'product_name': 'Potato chips', 'quantity': 1}]
    assert len(follow['pending_items']) == 1
    assert follow['pending_items'][0]['heard'] == ('bread' if heard == 'Potato chips and bread' else 'unicorn')
    rejected = call(app, 'POST', route+'/commit', 'partial', {'review_id': follow['request_id'], 'lines': [{'product_id': CHIPS, 'quantity': 1}], 'tender': 'cash', 'amount_received_cents': 100, 'match_confirmed': True})
    assert rejected.status_code == 409
    assert app.state.store.shops[UUID(SHOP)].idempotent_sales == {}
    app.state.store.close()


@pytest.mark.parametrize("change", ["delete", "rename", "sku"])
def test_stale_grounded_product_is_not_silently_replaced(tmp_path, monkeypatch, change):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.sqlite3"))
    resolver = lambda transcript, products: resolve_catalogue_voice(transcript, products, provider=None)
    app = build(tmp_path / "shop.sqlite3", resolver)
    route = f"/api/v1/shops/{SHOP}/voice/transcript"
    missing = call(app, "POST", route, "missing", {"transcript": "Potato chips"}).json()
    with app.state.store.transaction():
        products = app.state.store.shops[UUID(SHOP)].products
        if change == "delete":
            products.pop(UUID(CHIPS))
        elif change == "rename":
            products[UUID(CHIPS)].name = "Changed product name"
        else:
            products[UUID(CHIPS)].sku = "CHANGED-SKU"
    response = call(app, "POST", route, "quantity", {"transcript": "one", "clarification_of": missing["request_id"]})
    assert response.status_code == 409
    assert app.state.store.shops[UUID(SHOP)].idempotent_sales == {}
    app.state.store.close()


@pytest.mark.parametrize("heard,expected", [("one", 1), ("1", 1), ("one.", 1), ("twenty", 20), ("0", None), ("zero", None), ("-1", None), ("1.5", None), ("one hundred", None)])
def test_quantity_reply_is_explicit_positive_whole_number(heard, expected):
    assert parse_quantity_reply(heard) == expected
