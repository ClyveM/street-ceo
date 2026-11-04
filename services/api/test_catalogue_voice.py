"""HTTP tests for catalogue proposals, explicit approval and durable retries."""
from types import SimpleNamespace
from uuid import UUID

from services.ai.catalogue_voice import resolve_catalogue_voice
from services.ai.tracing import SQLiteTraceStore, traced_call
from services.api.test_sqlite_store import SHOP, build, call


class SyntheticProvider:
    def __init__(self, product_id, incomplete=False):
        self.product_id = product_id
        self.incomplete = incomplete
        self.calls = []

    def complete(self, request):
        self.calls.append(request)
        segments = request.trusted_context["segments"]
        raw = {"segments": [{"segment_id": segment["segment_id"], "product_id": self.product_id, "quantity": segment["quantity"], "resolution": "uncertain"} for segment in segments]}
        if self.incomplete:
            raw["segments"] = raw["segments"][:1]
        return traced_call(operation="catalogue_voice_resolution", model="synthetic-test-provider", request={"task": request.task}, call=lambda: raw)


def test_noisy_match_requires_explicit_approval_before_tender_and_payment(tmp_path, monkeypatch):
    trace_path = tmp_path / "traces.sqlite3"
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(trace_path))
    path = tmp_path / "shop.sqlite3"
    bread_id = "00000000-0000-0000-0000-000000000002"
    provider = SyntheticProvider(bread_id)
    resolver = lambda transcript, products: resolve_catalogue_voice(transcript, products, provider=provider, allow_local_proposals=False)
    app = build(path, resolver)
    route = f"/api/v1/shops/{SHOP}/voice"
    reviewed = call(app, "POST", route + "/transcript", "noisy", {"transcript": "one bread glove number"})
    assert reviewed.status_code == 200, reviewed.text
    proposal = reviewed.json()
    assert proposal["status"] == "needs_match_confirmation"
    assert proposal["requires_match_confirmation"] is True
    assert proposal["intent"]["action"] == "record_sale"
    assert proposal["intent"]["needs_confirmation"] is True
    assert proposal["provider_called"] is True
    assert proposal["resolution_source"] == "muse_catalogue"
    assert "Bread loaf" in proposal["clarification_question"]
    assert len(provider.calls) == 1
    catalogue = provider.calls[0].trusted_context["catalogue"]
    assert any(product["product_id"] == bread_id and product["name"] == "Bread loaf" for product in catalogue)
    assert call(app, "POST", route + "/transcript", "noisy", {"transcript": "one bread glove number"}).json() == proposal
    assert len(provider.calls) == 1
    initial_stock = app.state.store.shops[UUID(SHOP)].products[UUID(bread_id)].stock_qty
    body = {"review_id": proposal["request_id"], "lines": [{"product_id": bread_id, "quantity": 1}], "tender": "cash", "amount_received_cents": 500}
    rejected = call(app, "POST", route + "/commit", "paid", body)
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "match_confirmation_required"
    assert app.state.store.shops[UUID(SHOP)].products[UUID(bread_id)].stock_qty == initial_stock
    assert app.state.store.shops[UUID(SHOP)].idempotent_sales == {}
    app.state.store.close()
    app = build(path, resolver)
    question = call(app, "POST", route + "/commit", "paid", {**body, "tender": None, "amount_received_cents": None, "match_confirmed": False})
    assert question.json()["status"] == "needs_tender"
    paid_body = {**body, "match_confirmed": True}
    paid = call(app, "POST", route + "/commit", "paid", paid_body)
    assert paid.status_code == 200, paid.text
    receipt = paid.json()
    assert receipt["total_cents"] == 180
    assert receipt["change_cents"] == 320
    app.state.store.close()
    app = build(path, resolver)
    assert call(app, "POST", route + "/commit", "paid", paid_body).json() == receipt
    assert call(app, "POST", route + "/commit", "paid", body).status_code == 409
    assert len(app.state.store.shops[UUID(SHOP)].idempotent_sales) == 1
    assert app.state.store.shops[UUID(SHOP)].products[UUID(bread_id)].stock_qty == initial_stock - 1
    original_events = SQLiteTraceStore(trace_path).read(correlation_id=reviewed.headers["x-correlation-id"])
    completed = next(event for event in original_events if event.get("source") == "muse_catalogue" and event.get("phase") == "completed")
    assert completed["provider_called"] is True
    app.state.store.close()


def test_missing_quantity_followup_requires_yes_and_never_invents_quantity(tmp_path, monkeypatch):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.sqlite3"))
    resolver = lambda transcript, products: resolve_catalogue_voice(transcript, products, provider=None)
    app = build(tmp_path / "shop.sqlite3", resolver)
    route = f"/api/v1/shops/{SHOP}/voice"
    missing = call(app, "POST", route + "/transcript", "missing", {"transcript": "coca-cola"}).json()
    assert missing["status"] == "needs_clarification"
    assert missing["clarification_code"] == "missing_quantity"
    assert missing["lines"] == []
    assert missing["clarification_question"]
    assert missing["provider_called"] is False
    supplied = call(app, "POST", route + "/transcript", "quantity", {"transcript": "two", "clarification_of": missing["request_id"]}).json()
    assert supplied["status"] == "needs_match_confirmation"
    assert supplied["resolution_source"] == "local_clarification"
    assert supplied["lines"][0]["quantity"] == 2
    assert supplied["requires_match_confirmation"] is True
    assert supplied["intent"]["action"] == "record_sale"
    assert app.state.store.shops[UUID(SHOP)].idempotent_sales == {}
    assert call(app, "POST", route + "/transcript", "badcontext", {"transcript": "one", "clarification_of": "00000000-0000-0000-0000-999999999999"}).status_code == 409
    app.state.store.close()


def test_mixed_unknown_and_incomplete_model_proposal_never_partially_sells(tmp_path, monkeypatch):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.sqlite3"))
    provider = SyntheticProvider("00000000-0000-0000-0000-000000000001", incomplete=True)
    resolver = lambda transcript, products: resolve_catalogue_voice(transcript, products, provider=provider, allow_local_proposals=False)
    app = build(tmp_path / "shop.sqlite3", resolver)
    result = call(app, "POST", f"/api/v1/shops/{SHOP}/voice/transcript", "mixed", {"transcript": "one Coke and two unicorns"})
    assert result.status_code == 200
    assert result.json()["status"] == "needs_clarification"
    assert result.json()["lines"] == []
    record = app.state.store.shops[UUID(SHOP)]
    assert record.voice_reviews == {}
    assert record.idempotent_sales == {}
    app.state.store.close()


def test_exact_commands_do_not_call_resolver_and_legacy_paid_fingerprint_survives(tmp_path, monkeypatch):
    import hashlib
    import json
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.sqlite3"))
    def forbidden(*args):
        raise AssertionError("exact path called resolver")
    app = build(tmp_path / "shop.sqlite3", forbidden)
    route = f"/api/v1/shops/{SHOP}/voice"
    response = call(app, "POST", route + "/transcript", "exact", {"transcript": "one Coke"}).json()
    assert response["status"] == "needs_confirmation"
    assert response["resolution_source"] == "catalogue_parser"
    assert response["requires_match_confirmation"] is False
    body = {"review_id": response["request_id"], "lines": [{"product_id": response["lines"][0]["product_id"], "quantity": 1}], "tender": "cash", "amount_received_cents": 500}
    receipt = call(app, "POST", route + "/commit", "old-key", body).json()
    legacy_fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with app.state.store.transaction():
        record = app.state.store.shops[UUID(SHOP)]
        key, _, original_sale = record.voice_review_commits[UUID(response["request_id"])]
        record.voice_review_commits[UUID(response["request_id"])] = (key, legacy_fingerprint, original_sale)
    assert call(app, "POST", route + "/commit", "old-key", body).json() == receipt
    assert call(app, "POST", route + "/commit", "old-key", {**body, "match_confirmed": False}).json() == receipt
    app.state.store.close()

def test_unknown_muse_reply_offers_only_a_unique_candidate_and_preserves_quantity(tmp_path, monkeypatch):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "trace.sqlite3"))
    provider = SyntheticProvider(None)
    app = build(
        tmp_path / "shop.sqlite3",
        lambda transcript, products: resolve_catalogue_voice(
            transcript, products, provider=provider, allow_local_proposals=False,
        ),
    )
    route = f"/api/v1/shops/{SHOP}/voice/transcript"

    initial = call(app, "POST", route, "heard-cook", {"transcript": "one cook"}).json()
    assert initial["status"] == "needs_clarification"
    assert initial["lines"] == []
    assert initial["clarification_question"].startswith("Did you mean one Coca-Cola")
    assert initial["pending_items"][0]["quantity"] == 1
    accepted = call(app, "POST", route, "yes-cook", {
        "transcript": "Yes", "clarification_of": initial["request_id"],
    }).json()
    assert accepted["status"] == "needs_match_confirmation"
    assert accepted["lines"][0]["quantity"] == 1
    assert accepted["lines"][0]["product_name"] == "Coca-Cola 300ml"

    unknown = call(app, "POST", route, "heard-unicorn", {"transcript": "two unicorns"}).json()
    assert unknown["pending_items"][0]["product_id"] is None
    assert unknown["pending_items"][0]["quantity"] == 2
    named = call(app, "POST", route, "named-bread", {
        "transcript": "bread", "clarification_of": unknown["request_id"],
    }).json()
    assert named["lines"][0]["quantity"] == 2
    assert named["lines"][0]["product_name"] == "Bread loaf"

    from uuid import uuid4

    from services.api.app import Product

    with app.state.store.transaction():
        cookies = Product(id=uuid4(), shop_id=UUID(SHOP), sku="COOKIE-100",
                          name="Cookies", unit_price_cents=150, stock_qty=10)
        app.state.store.shops[UUID(SHOP)].products[cookies.id] = cookies
    ambiguous = call(app, "POST", route, "heard-cook-again", {"transcript": "one cook"}).json()
    assert ambiguous["clarification_question"] == "I heard one cook. Did you mean Coke or cookies?"
    assert ambiguous["pending_items"][0]["product_id"] is None
    yes = call(app, "POST", route, "ambiguous-yes", {
        "transcript": "Yes", "clarification_of": ambiguous["request_id"],
    }).json()
    assert yes["lines"] == []
    assert yes["pending_items"][0]["quantity"] == 1
    picked = call(app, "POST", route, "picked-cookies", {
        "transcript": "Cookies", "clarification_of": yes["request_id"],
    }).json()
    assert picked["lines"] == [{"product_id": str(cookies.id), "product_name": "Cookies", "quantity": 1}]
