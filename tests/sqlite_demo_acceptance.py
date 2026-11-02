"""Independent connected-demo acceptance; isolated files, no provider/network calls.

Run: python -m pytest tests/sqlite_demo_acceptance.py -q
"""
import asyncio
from uuid import UUID

import httpx
import pytest

from services.api.app import create_app
from services.api.persistence import Settings
from services.ai.tracing import SQLiteTraceStore


SHOP = "00000000-0000-0000-0000-000000000001"
PRODUCT = "00000000-0000-0000-0000-000000000001"
SALES = f"/shops/{SHOP}/sales"
VOICE = f"/api/v1/shops/{SHOP}/voice"


@pytest.fixture
def demo(tmp_path, monkeypatch):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.sqlite3"))
    apps = []

    def build(resolver=None):
        app = create_app(settings=Settings(
            store_backend="sqlite", sqlite_path=str(tmp_path / "shop.sqlite3"),
            demo_seed_enabled=True, voice_enabled=True,
        ), voice_catalogue_resolver=resolver)
        apps.append(app)
        return app

    yield build
    for app in apps:
        app.state.store.close()


def request(app, method, path, body=None, key="sale"):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as client:
            return await client.request(method, path, json=body,
                                        headers={"X-Shop-ID": SHOP, "Idempotency-Key": key})
    return asyncio.run(run())


def stock(app):
    response = request(app, "GET", f"/shops/{SHOP}/products")
    assert response.status_code == 200, response.text
    return next(product["stock_qty"] for product in response.json() if product["id"] == PRODUCT)


def basket(quantity=1):
    return {"lines": [{"product_id": PRODUCT, "quantity": quantity}], "tender": "cash"}


def review(app):
    result = request(app, "POST", VOICE + "/transcript", {"transcript": "one Coke"}, "review")
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["status"] == "needs_confirmation"
    return {"review_id": data["request_id"],
            "lines": [{"product_id": PRODUCT, "quantity": 1}],
            "tender": "cash", "amount_received_cents": 500}


def test_manual_http_receipt_retry_and_changed_payload_after_reopen(demo):
    app = demo()
    sale = request(app, "POST", SALES, basket(2))
    assert sale.status_code == 201, sale.text
    assert stock(app) == 16
    reopened = demo()
    retry = request(reopened, "POST", SALES, basket(2))
    assert retry.status_code == 201, retry.text
    assert retry.json() == sale.json()
    assert request(reopened, "POST", SALES, basket(3)).status_code == 409
    assert stock(reopened) == 16
    assert request(reopened, "GET", SALES).json() == [sale.json()]


def test_concurrent_last_unit_has_one_receipt_and_no_negative_stock(demo):
    app = demo()
    with app.state.store.transaction():
        app.state.store.shops[UUID(SHOP)].products[UUID(PRODUCT)].stock_qty = 1

    async def race():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await asyncio.gather(*[
                client.post(SALES, json=basket(), headers={"X-Shop-ID": SHOP, "Idempotency-Key": key})
                for key in ("last-one", "last-two")
            ])

    responses = asyncio.run(race())
    assert sorted(response.status_code for response in responses) == [201, 409]
    reopened = demo()
    assert stock(reopened) == 0
    assert len(request(reopened, "GET", SALES).json()) == 1


def test_write_failure_cannot_return_receipt_or_leave_partial_sale(demo, monkeypatch):
    app = demo()
    original = app.state.store._save

    def fail():
        app.state.store.connection.execute("DELETE FROM shop_state")
        raise OSError("injected storage failure")

    monkeypatch.setattr(app.state.store, "_save", fail)
    response = request(app, "POST", SALES, basket())
    assert response.status_code == 503, response.text
    assert "id" not in response.json()
    monkeypatch.setattr(app.state.store, "_save", original)
    reopened = demo()
    assert stock(reopened) == 18
    assert request(reopened, "GET", SALES).json() == []


def test_invalid_later_line_leaves_valid_product_and_history_unchanged(demo):
    app = demo()
    body = basket()
    body["lines"].append({"product_id": str(UUID(int=99999)), "quantity": 1})
    response = request(app, "POST", SALES, body)
    assert response.status_code == 404, response.text
    reopened = demo()
    assert stock(reopened) == 18
    assert request(reopened, "GET", SALES).json() == []


def test_voice_precommit_trace_failure_rolls_back_stock_and_binding(demo, monkeypatch):
    app = demo()
    body = review(app)
    original = SQLiteTraceStore.record

    def fail_prepared(self, trace):
        if trace.get("phase") == "response_prepared":
            raise OSError("injected trace failure")
        return original(self, trace)

    monkeypatch.setattr(SQLiteTraceStore, "record", fail_prepared)
    response = request(app, "POST", VOICE + "/commit", body, "commit")
    assert response.status_code == 503, response.text
    monkeypatch.setattr(SQLiteTraceStore, "record", original)
    reopened = demo()
    assert stock(reopened) == 18
    assert request(reopened, "GET", SALES).json() == []
    recovered = request(reopened, "POST", VOICE + "/commit", body, "commit")
    assert recovered.status_code == 200, recovered.text
    assert stock(reopened) == 17


def test_postcommit_trace_failure_requires_same_key_recovery_without_duplicate(demo, monkeypatch):
    app = demo()
    body = review(app)
    original = SQLiteTraceStore.record

    def fail_completed(self, trace):
        if trace.get("phase") == "completed" and trace.get("operation") == "commit":
            raise OSError("injected receipt trace failure")
        return original(self, trace)

    monkeypatch.setattr(SQLiteTraceStore, "record", fail_completed)
    response = request(app, "POST", VOICE + "/commit", body, "commit")
    assert response.status_code == 503, response.text
    monkeypatch.setattr(SQLiteTraceStore, "record", original)
    reopened = demo()
    assert stock(reopened) == 17
    history = request(reopened, "GET", SALES).json()
    assert len(history) == 1
    recovered = request(reopened, "POST", VOICE + "/commit", body, "commit")
    assert recovered.status_code == 200, recovered.text
    assert recovered.json() == history[0]
    assert stock(reopened) == 17


def test_missing_trace_disk_prevents_voice_mutation_with_controlled_response(demo, monkeypatch):
    app = demo()
    body = review(app)
    original = SQLiteTraceStore.record

    def fail(self, trace):
        raise OSError("injected unavailable trace store")

    monkeypatch.setattr(SQLiteTraceStore, "record", fail)
    response = request(app, "POST", VOICE + "/commit", body, "commit")
    assert response.status_code == 503, response.text
    monkeypatch.setattr(SQLiteTraceStore, "record", original)
    reopened = demo()
    assert stock(reopened) == 18
    assert request(reopened, "GET", SALES).json() == []


def test_explicit_manual_cash_is_exact_strict_and_durable(demo):
    app = demo()
    for amount in (True, 500.0, "500", -1):
        response = request(app, "POST", SALES, {**basket(2), "amount_received_cents": amount}, str(amount))
        assert response.status_code == 422, response.text
    short = request(app, "POST", SALES, {**basket(2), "amount_received_cents": 299}, "cash-exact")
    assert short.status_code == 409, short.text
    assert short.json()["detail"]["code"] == "insufficient_cash"
    assert stock(app) == 18
    assert request(app, "GET", SALES).json() == []
    body = {**basket(2), "amount_received_cents": 500}
    receipt = request(app, "POST", SALES, body, "cash-exact")
    assert receipt.status_code == 201, receipt.text
    assert (receipt.json()["total_cents"], receipt.json()["amount_received_cents"], receipt.json()["change_cents"]) == (300, 500, 200)
    reopened = demo()
    with reopened.state.store.transaction():
        reopened.state.store.shops[UUID(SHOP)].products[UUID(PRODUCT)].unit_price_cents = 1000
    assert request(reopened, "POST", SALES, body, "cash-exact").json() == receipt.json()
    assert request(reopened, "POST", SALES, {**body, "amount_received_cents": 600}, "cash-exact").status_code == 409
    assert stock(reopened) == 16
    with reopened.state.store.transaction():
        reopened.state.store.shops[UUID(SHOP)].products[UUID(PRODUCT)].unit_price_cents = 150
    bad_bank = request(reopened, "POST", SALES, {**basket(), "tender": "bank", "amount_received_cents": 500}, "bank-exact")
    assert bad_bank.status_code == 409, bad_bank.text
    bank = request(reopened, "POST", SALES, {**basket(), "tender": "bank", "amount_received_cents": 150}, "bank-exact")
    assert bank.status_code == 201, bank.text
    assert bank.json()["change_cents"] == 0


def test_legacy_omitted_and_null_amounts_share_retry_identity(demo):
    app = demo()
    original = request(app, "POST", SALES, basket(), "legacy-null")
    assert original.status_code == 201, original.text
    assert original.json()["amount_received_cents"] is None
    reopened = demo()
    replay = request(reopened, "POST", SALES, {**basket(), "amount_received_cents": None}, "legacy-null")
    assert replay.json() == original.json()
    assert stock(reopened) == 17


def test_shop_investigation_filter_redaction_bounds_and_unavailable_file(demo, monkeypatch, tmp_path):
    app = demo()
    trace_file = tmp_path / "isolated-read.sqlite3"
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(trace_file))
    path = f"/api/v1/shops/{SHOP}/investigations/requests"
    missing = request(app, "GET", path)
    assert missing.status_code == 200, missing.text
    assert missing.json() == {"shop_id": SHOP, "events": []}
    assert not trace_file.exists(), "Reading absent investigations must not create a trace database"
    trace_store = SQLiteTraceStore()
    trace_store.record({"shop_id": SHOP, "correlation_id": "allowed", "phase": "completed",
                        "response": {"authorization": "synthetic", "audio_base64": "never show this"}})
    for index in range(3):
        trace_store.record({"shop_id": str(UUID(int=9876)), "correlation_id": f"other-{index}", "phase": "completed"})
    trace_store.record({"correlation_id": "unscoped", "phase": "completed"})
    filtered = request(app, "GET", path + "?limit=1")
    assert filtered.status_code == 200, filtered.text
    events = filtered.json()["events"]
    assert len(events) == 1 and events[0]["correlation_id"] == "allowed"
    assert events[0]["response"] == {"authorization": "[redacted]", "audio_base64": "[redacted]"}
    assert request(app, "GET", path + "?correlation_id=other-0").json()["events"] == []
    assert request(app, "GET", path + "?limit=101").status_code == 422
    assert request(app, "GET", path + "?correlation_id=" + "x" * 121).status_code == 422
    corrupt = tmp_path / "corrupt-traces.sqlite3"
    corrupt.write_bytes(b"not a sqlite database")
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(corrupt))
    unavailable = request(app, "GET", path)
    assert unavailable.status_code == 503, unavailable.text
    assert "unavailable" in unavailable.text.lower()


def test_http_payment_questions_are_not_receipts_and_do_not_mutate_stock(demo):
    app = demo()
    reviewed = review(app)
    unpaid = {"review_id": reviewed["review_id"], "lines": reviewed["lines"]}
    question = request(app, "POST", VOICE + "/commit", unpaid, "unpaid-question")
    assert question.status_code == 200, question.text
    data = question.json()
    assert data["status"] == "needs_tender"
    assert data["review_id"] == reviewed["review_id"]
    assert data["amount_due_cents"] == 150
    assert data["allowed_tenders"] == ["cash", "bank"]
    assert data["missing"] == ["tender"]
    assert isinstance(data["question"], str) and data["question"]
    assert "id" not in data and "stock_after" not in data
    assert stock(app) == 18
    assert request(app, "GET", SALES).json() == []
    reopened = demo()
    replay = request(reopened, "POST", VOICE + "/commit", unpaid, "unpaid-question")
    assert replay.status_code == 200 and replay.json() == data
    cash_question = request(reopened, "POST", VOICE + "/commit", {**unpaid, "tender": "cash"}, "unpaid-question")
    assert cash_question.status_code == 200, cash_question.text
    assert cash_question.json()["status"] == "needs_tender"
    assert cash_question.json()["missing"] == ["amount_received_cents"]
    final = demo()
    assert stock(final) == 18
    assert request(final, "GET", SALES).json() == []
    assert final.state.store.shops[UUID(SHOP)].voice_review_commits == {}
    events = SQLiteTraceStore().read(limit=100)
    completed = [event for event in events if event.get("operation") == "commit" and event.get("phase") == "completed"]
    assert completed and all(event["response"]["status"] == "needs_tender" for event in completed)
    assert all("id" not in event["response"] for event in completed)


def catalogue_resolver(mode="complete"):
    """Real grounding validator around a synthetic, traced provider; no network."""
    from services.ai.catalogue_voice import resolve_catalogue_voice
    from services.ai.tracing import traced_call
    calls = []

    def resolve(transcript, catalogue):
        class Provider:
            def complete(self, query):
                calls.append(query)
                products = query.trusted_context["catalogue"]
                result = []
                for segment in query.trusted_context["segments"]:
                    heard = segment["heard"].lower()
                    prefix = "Bread" if "bread" in heard else "Coca-Cola" if "coke" in heard or "coca" in heard else None
                    product = next((item for item in products if prefix and item["name"].startswith(prefix)), None)
                    result.append({"segment_id": segment["segment_id"], "product_id": product["product_id"] if product else None,
                                   "quantity": segment["quantity"], "resolution": "uncertain" if product else "unknown"})
                if mode == "omit":
                    result = result[:1]
                elif mode == "invent_quantity":
                    result[0]["quantity"] = 99
                elif mode == "invent_id":
                    result[0]["product_id"] = str(UUID(int=99999))
                elif mode == "extra_price":
                    result[0]["price_cents"] = 1
                return traced_call(operation="catalogue_voice_resolution", model="qa-synthetic-catalogue",
                                   request={"transcript": query.untrusted_input}, call=lambda: {"segments": result})
        return resolve_catalogue_voice(transcript, catalogue, provider=Provider(), allow_local_proposals=False)

    resolve.calls = calls
    return resolve


def test_grounded_proposal_requires_explicit_confirmation_then_durable_exact_receipt(demo):
    resolver = catalogue_resolver()
    app = demo(resolver)
    response = request(app, "POST", VOICE + "/transcript", {"transcript": "one bread glove number and two coca-cola nabo marble"}, "noisy-review")
    assert response.status_code == 200, response.text
    proposed = response.json()
    assert proposed["status"] == "needs_match_confirmation"
    assert proposed["requires_match_confirmation"] is True
    assert proposed["intent"]["action"] == "record_sale" and proposed["intent"]["needs_confirmation"] is True
    assert [(line["product_name"], line["quantity"]) for line in proposed["lines"]] == [("Bread loaf", 1), ("Coca-Cola 300ml", 2)]
    assert "180" not in proposed["clarification_question"]
    assert len(resolver.calls) == 1
    assert stock(app) == 18 and request(app, "GET", SALES).json() == []
    body = {"review_id": proposed["request_id"], "lines": [{"product_id": line["product_id"], "quantity": line["quantity"]} for line in proposed["lines"]], "tender": "cash", "amount_received_cents": 1000}
    blocked = request(app, "POST", VOICE + "/commit", body, "confirmed-sale")
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["detail"]["code"] == "match_confirmation_required"
    assert request(app, "POST", VOICE + "/commit", {**body, "match_confirmed": 1}, "confirmed-sale").status_code == 422
    assert stock(app) == 18 and request(app, "GET", SALES).json() == []
    reopened = demo()
    paid_body = {**body, "match_confirmed": True}
    receipt = request(reopened, "POST", VOICE + "/commit", paid_body, "confirmed-sale")
    assert receipt.status_code == 200, receipt.text
    assert (receipt.json()["total_cents"], receipt.json()["change_cents"]) == (480, 520)
    final = demo()
    assert request(final, "POST", VOICE + "/commit", paid_body, "confirmed-sale").json() == receipt.json()
    assert request(final, "POST", VOICE + "/commit", body, "confirmed-sale").status_code == 409
    assert request(final, "POST", VOICE + "/commit", paid_body, "different-key").status_code == 409
    assert stock(final) == 16 and len(request(final, "GET", SALES).json()) == 1
    events = SQLiteTraceStore().read(response.headers["x-correlation-id"])
    completed = next(event for event in events if event.get("source") == "muse_catalogue" and event.get("phase") == "completed")
    assert completed["provider_called"] is True
    assert any(event.get("model") == "qa-synthetic-catalogue" for event in events)


@pytest.mark.parametrize("mode", ["omit", "invent_quantity", "invent_id", "extra_price"])
def test_provider_cannot_drop_items_invent_quantities_ids_or_prices(demo, mode):
    resolver = catalogue_resolver(mode)
    app = demo(resolver)
    response = request(app, "POST", VOICE + "/transcript", {"transcript": "one bread glove number and two coca-cola marble"}, "invalid-model")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "needs_clarification"
    assert response.json()["lines"] == []
    assert stock(app) == 18 and request(app, "GET", SALES).json() == []
    assert app.state.store.shops[UUID(SHOP)].voice_reviews == {}


def test_missing_quantity_context_reopens_then_requires_match_without_guessing(demo):
    resolver = catalogue_resolver()
    app = demo(resolver)
    first = request(app, "POST", VOICE + "/transcript", {"transcript": "Coca-Cola"}, "missing-quantity")
    assert first.status_code == 200, first.text
    missing = first.json()
    assert missing["status"] == "needs_clarification" and missing["clarification_code"] == "missing_quantity"
    assert missing["lines"] == []
    reopened = demo()
    body = {"transcript": "two", "clarification_of": missing["request_id"]}
    answer = request(reopened, "POST", VOICE + "/transcript", body, "quantity-answer")
    assert answer.status_code == 200, answer.text
    proposal = answer.json()
    assert proposal["status"] == "needs_match_confirmation" and proposal["requires_match_confirmation"] is True
    assert [(line["product_id"], line["quantity"]) for line in proposal["lines"]] == [(PRODUCT, 2)]
    assert proposal["resolution_source"] == "local_clarification"
    assert request(reopened, "POST", VOICE + "/transcript", body, "quantity-answer").json() == proposal
    assert request(reopened, "POST", VOICE + "/transcript", {**body, "transcript": "three"}, "quantity-answer").status_code == 409
    assert request(reopened, "POST", VOICE + "/transcript", {"transcript": "two", "clarification_of": str(UUID(int=999))}, "unknown-context").status_code == 409
    assert stock(reopened) == 18 and request(reopened, "GET", SALES).json() == []


def test_unknown_second_item_never_becomes_partial_first_item_sale(demo):
    app = demo(catalogue_resolver())
    result = request(app, "POST", VOICE + "/transcript", {"transcript": "one coke and one unicorn"}, "partial-basket")
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "needs_clarification" and result.json()["lines"] == []
    assert stock(app) == 18 and request(app, "GET", SALES).json() == []
    assert app.state.store.shops[UUID(SHOP)].voice_reviews == {}


def test_fast_local_proposal_requires_yes_has_no_mutation_and_replays_after_reopen(demo):
    from services.ai.catalogue_voice import resolve_catalogue_voice

    def local_only(transcript, products):
        return resolve_catalogue_voice(transcript, products, provider=None)

    app = demo(local_only)
    transcript = {"transcript": "one coca-cola nabo marble"}
    response = request(app, "POST", VOICE + "/transcript", transcript, "local-review")
    assert response.status_code == 200, response.text
    proposal = response.json()
    assert proposal["status"] == "needs_match_confirmation"
    assert proposal["requires_match_confirmation"] is True
    assert proposal["provider_called"] is False
    assert proposal["resolution_source"] == "local_catalogue_proposal"
    assert [(line["product_id"], line["quantity"]) for line in proposal["lines"]] == [(PRODUCT, 1)]
    assert stock(app) == 18 and request(app, "GET", SALES).json() == []
    body = {"review_id": proposal["request_id"], "lines": [{"product_id": PRODUCT, "quantity": 1}], "tender": "cash", "amount_received_cents": 500}
    rejected = request(app, "POST", VOICE + "/commit", body, "local-payment")
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "match_confirmation_required"
    assert stock(app) == 18 and request(app, "GET", SALES).json() == []
    reopened = demo(local_only)
    assert request(reopened, "POST", VOICE + "/transcript", transcript, "local-review").json() == proposal
    question = request(reopened, "POST", VOICE + "/commit", {"review_id": proposal["request_id"], "lines": body["lines"], "match_confirmed": True}, "local-payment")
    assert question.status_code == 200 and question.json()["status"] == "needs_tender"
    assert stock(reopened) == 18 and request(reopened, "GET", SALES).json() == []
    paid = request(reopened, "POST", VOICE + "/commit", {**body, "match_confirmed": True}, "local-payment")
    assert paid.status_code == 200, paid.text
    final = demo(local_only)
    assert request(final, "POST", VOICE + "/commit", {**body, "match_confirmed": True}, "local-payment").json() == paid.json()
    assert stock(final) == 17 and len(request(final, "GET", SALES).json()) == 1
    events = SQLiteTraceStore().read(response.headers["x-correlation-id"])
    local_event = next(event for event in events if event.get("source") == "local_catalogue_proposal")
    assert local_event["provider_called"] is False
