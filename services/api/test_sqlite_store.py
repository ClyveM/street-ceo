"""Real-file persistence/retry/rollback tests for the connected demo."""
import asyncio
from uuid import UUID

import httpx
import pytest

from services.api.app import ProductCreate, SaleCreate, SaleLine, create_app
from services.api.persistence import Settings
from services.api.sqlite_store import SQLiteStore
from services.api.voice_boundary import parse_catalogue_sale

SHOP = "00000000-0000-0000-0000-000000000001"


def build(path, resolver=None):
    return create_app(settings=Settings(store_backend="sqlite", sqlite_path=str(path), demo_seed_enabled=True, voice_enabled=True), voice_catalogue_resolver=resolver)


def call(app, method, path, key="request", body=None, shop_header=SHOP, extra_headers=None):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.request(method, path, json=body, headers={"X-Shop-ID": shop_header, "Idempotency-Key": key, **(extra_headers or {})})
    return asyncio.run(run())


def test_real_file_voice_review_commit_and_retry_survive_reopen(tmp_path, monkeypatch):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.sqlite3"))
    path = tmp_path / "shop.sqlite3"
    app = build(path)
    base = f"/api/v1/shops/{SHOP}/voice"
    review = call(app, "POST", base + "/transcript", "review", {"transcript": "one Coke and two sugar"})
    assert review.status_code == 200, review.text
    data = review.json()
    assert data["status"] == "needs_confirmation"
    assert len(data["lines"]) == 2
    app.state.store.close()
    app = build(path)
    body = {"review_id": data["request_id"], "lines": [{"product_id": item["product_id"], "quantity": item["quantity"]} for item in data["lines"]], "tender": "cash", "amount_received_cents": 1000}
    sale = call(app, "POST", base + "/commit", "commit", body)
    assert sale.status_code == 200, sale.text
    receipt = sale.json()
    assert receipt["total_cents"] == 630
    assert receipt["change_cents"] == 370
    assert receipt["amount_received_cents"] == 1000
    assert receipt["stock_after"][data["lines"][0]["product_id"]] == 17
    app.state.store.close()
    app = build(path)
    replay = call(app, "POST", base + "/commit", "commit", body)
    assert replay.json() == receipt
    assert call(app, "POST", base + "/commit", "other-key", body).status_code == 409
    assert call(app, "POST", base + "/commit", "commit", {**body, "amount_received_cents": 1100}).status_code == 409
    history = call(app, "GET", f"/shops/{SHOP}/sales").json()
    assert history == [receipt]
    from services.ai.tracing import SQLiteTraceStore
    traces = SQLiteTraceStore(str(tmp_path / "traces.sqlite3")).read(limit=100)
    assert any(item.get("response", {}).get("id") == receipt["id"] for item in traces)
    app.state.store.close()


def test_manual_sale_cogs_seed_preservation_and_binary_round_trip(tmp_path):
    path = tmp_path / "shop.sqlite3"
    store = SQLiteStore(str(path))
    with store.transaction():
        store.seed_demo_shop()
        record = store.get_shop_record(UUID(SHOP))
        product = next(iter(record.products.values()))
        product.unit_cost_micros = 1000000
        record.invoice_bytes[UUID(int=999)] = b"\xff\x00pdf"
        sale = store.create_sale(record, SaleCreate(lines=[SaleLine(product_id=product.id, quantity=2)], tender="cash"), "fingerprint", "manual")
    store.close()
    reopened = SQLiteStore(str(path))
    with reopened.transaction():
        reopened.seed_demo_shop()
        record = reopened.get_shop_record(UUID(SHOP))
        assert record.products[product.id].stock_qty == 16
        assert record.invoice_bytes[UUID(int=999)] == b"\xff\x00pdf"
        assert record.idempotent_sales["manual"][1].cogs_micros == 2000000
        assert reopened.create_sale(record, SaleCreate(lines=[SaleLine(product_id=product.id, quantity=2)], tender="cash"), "fingerprint", "manual").id == sale.id
    reopened.close()


def test_commit_failure_rolls_back_memory_and_file(tmp_path, monkeypatch):
    store = SQLiteStore(str(tmp_path / "shop.sqlite3"))
    with store.transaction():
        store.seed_demo_shop()
    product = next(iter(store.shops[UUID(SHOP)].products.values()))
    original_stock = product.stock_qty
    def fail():
        store.connection.execute("DELETE FROM shop_state")
        raise RuntimeError("injected disk write failure")
    monkeypatch.setattr(store, "_save", fail)
    with pytest.raises(RuntimeError):
        with store.transaction():
            store.shops[UUID(SHOP)].products[product.id].stock_qty = 0
    assert store.shops[UUID(SHOP)].products[product.id].stock_qty == original_stock
    reopened = SQLiteStore(str(store.path))
    assert reopened.shops[UUID(SHOP)].products[product.id].stock_qty == original_stock
    store.close()
    reopened.close()


def test_unknown_and_trailing_words_reject_whole_basket(tmp_path, monkeypatch):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.sqlite3"))
    app = build(tmp_path / "shop.sqlite3")
    for index, command in enumerate(("one Coke and two unicorns", "2 coke garbage", "1 coke 2 unknown", "zero Coke")):
        result = call(app, "POST", f"/api/v1/shops/{SHOP}/voice/transcript", str(index), {"transcript": command})
        assert result.json()["error_code"] == "product_not_found"
        assert result.json()["lines"] == []
    assert call(app, "GET", f"/shops/{SHOP}/sales").json() == []
    app.state.store.close()


def test_trace_start_failure_returns_503_without_review_or_mutation(tmp_path, monkeypatch):
    app = build(tmp_path / "shop.sqlite3")
    from services.ai.tracing import SQLiteTraceStore
    def fail(*args, **kwargs):
        raise OSError("injected trace device failure")
    monkeypatch.setattr(SQLiteTraceStore, "record", fail)
    result = call(app, "POST", f"/api/v1/shops/{SHOP}/voice/transcript", "review", {"transcript": "one Coke"})
    assert result.status_code == 503
    assert app.state.store.shops[UUID(SHOP)].voice_reviews == {}
    app.state.store.close()


def test_parallel_sale_requests_serialize_and_cannot_oversell(tmp_path):
    app = build(tmp_path / "shop.sqlite3")
    product = next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    with app.state.store.transaction():
        app.state.store.shops[UUID(SHOP)].products[product.id].stock_qty = 1
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            async def sell(key):
                return await client.post(f"/shops/{SHOP}/sales", json={"lines": [{"product_id": str(product.id), "quantity": 1}], "tender": "cash"}, headers={"X-Shop-ID": SHOP, "Idempotency-Key": key})
            return await asyncio.gather(sell("first"), sell("second"))
    responses = asyncio.run(run())
    assert sorted(response.status_code for response in responses) == [201, 409]
    record = app.state.store.shops[UUID(SHOP)]
    assert record.products[product.id].stock_qty == 0
    assert len(record.idempotent_sales) == 1
    app.state.store.close()


def test_manual_cash_change_underpayment_and_reopen_retry(tmp_path):
    path = tmp_path / "manual.sqlite3"
    app = build(path)
    product = next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    body = {"lines": [{"product_id": str(product.id), "quantity": 2}], "tender": "cash", "amount_received_cents": 500}
    route = f"/shops/{SHOP}/sales"
    insufficient = call(app, "POST", route, "cash", {**body, "amount_received_cents": 100})
    assert insufficient.status_code == 409
    assert insufficient.json()["detail"]["code"] == "insufficient_cash"
    receipt = call(app, "POST", route, "cash", body)
    assert receipt.status_code == 201, receipt.text
    assert receipt.json()["total_cents"] == 300
    assert receipt.json()["amount_received_cents"] == 500
    assert receipt.json()["change_cents"] == 200
    app.state.store.close()
    app = build(path)
    assert call(app, "POST", route, "cash", body).json() == receipt.json()
    assert call(app, "POST", route, "cash", {**body, "amount_received_cents": 600}).status_code == 409
    assert app.state.store.shops[UUID(SHOP)].products[product.id].stock_qty == 16
    app.state.store.close()


def test_manual_legacy_omission_fingerprint_and_amount_validation(tmp_path):
    import hashlib
    import json
    app = build(tmp_path / "legacy.sqlite3")
    product = next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    body = {"lines": [{"product_id": str(product.id), "quantity": 1}], "tender": "cash"}
    legacy_fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with app.state.store.transaction():
        record = app.state.store.shops[UUID(SHOP)]
        legacy_sale = app.state.store.create_sale(record, SaleCreate(**body), legacy_fingerprint, "legacy")
    route = f"/shops/{SHOP}/sales"
    assert call(app, "POST", route, "legacy", body).json()["id"] == str(legacy_sale.id)
    assert call(app, "POST", route, "legacy", {**body, "amount_received_cents": None}).json()["id"] == str(legacy_sale.id)
    for amount in (True, 1.5, -1, "500"):
        assert call(app, "POST", route, str(amount), {**body, "amount_received_cents": amount}).status_code == 422
    assert call(app, "POST", route, "bankbad", {**body, "tender": "bank", "amount_received_cents": 500}).status_code == 409
    bank = call(app, "POST", route, "bank", {**body, "tender": "bank", "amount_received_cents": 150})
    assert bank.status_code == 201
    assert bank.json()["change_cents"] == 0
    app.state.store.close()


def test_shop_traces_filter_before_limit_and_correlation(tmp_path, monkeypatch):
    from services.ai.tracing import SQLiteTraceStore
    from services.api.app import ShopCreate
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "trace.sqlite3"))
    app = build(tmp_path / "shop.sqlite3")
    with app.state.store.transaction():
        other = app.state.store.create_shop(ShopCreate(name="Other synthetic shop"))
    traces = SQLiteTraceStore()
    traces.record({"shop_id": SHOP, "correlation_id": "own-correlation", "operation": "transcript", "request": {"authorization": "secret", "transcript": "one Coke"}})
    for _ in range(110):
        traces.record({"shop_id": str(other.id), "correlation_id": "other-correlation", "operation": "transcript"})
    traces.record({"correlation_id": "global-correlation", "operation": "global"})
    route = f"/api/v1/shops/{SHOP}/investigations/requests"
    response = call(app, "GET", route + "?limit=1")
    assert response.status_code == 200, response.text
    events = response.json()["events"]
    assert len(events) == 1
    assert events[0]["correlation_id"] == "own-correlation"
    assert events[0]["request"]["authorization"] == "[redacted]"
    assert call(app, "GET", route + "?correlation_id=other-correlation").json()["events"] == []
    assert call(app, "GET", route, shop_header=str(other.id)).status_code == 403
    assert call(app, "GET", route + "?limit=101").status_code == 422
    app.state.store.close()


def test_runtime_identity_omits_full_path(tmp_path):
    import hashlib
    path = tmp_path / "shop.sqlite3"
    app = build(path)
    response = call(app, "GET", "/api/v1/demo/runtime")
    data = response.json()
    assert data["store_backend"] == "sqlite"
    assert data["database_name"] == "shop.sqlite3"
    assert data["database_identity"] == hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()
    assert str(tmp_path) not in response.text
    assert data["single_worker_demo"] is True
    app.state.store.close()


def test_http_voice_tender_followups_keep_review_and_stock_until_paid(tmp_path, monkeypatch):
    """Phone recovery: 200 tender questions are not uncertain sale outcomes."""
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.sqlite3"))
    path = tmp_path / "phone-followup.sqlite3"
    app = build(path)
    base = f"/api/v1/shops/{SHOP}/voice"
    origin = {"Origin": "http://localhost"}
    preflight = call(app, "OPTIONS", base + "/commit", extra_headers={**origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type,x-shop-id,idempotency-key"})
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://localhost"
    assert "idempotency-key" in preflight.headers["access-control-allow-headers"]
    review = call(app, "POST", base + "/transcript", "review", {"transcript": "one Coke"}, extra_headers=origin)
    assert review.status_code == 200
    data = review.json()
    assert data["status"] == "needs_confirmation"
    body = {"review_id": data["request_id"], "lines": [{"product_id": line["product_id"], "quantity": line["quantity"]} for line in data["lines"]]}
    initial_stock = {key: product.stock_qty for key, product in app.state.store.shops[UUID(SHOP)].products.items()}

    def assert_unposted():
        record = app.state.store.shops[UUID(SHOP)]
        assert {key: product.stock_qty for key, product in record.products.items()} == initial_stock
        assert UUID(data["request_id"]) in record.voice_reviews
        assert record.voice_review_commits == {}
        assert record.idempotent_sales == {}

    for _ in range(2):
        question = call(app, "POST", base + "/commit", "followup", body, extra_headers=origin)
        assert question.status_code == 200, question.text
        assert question.headers["content-type"].startswith("application/json")
        assert question.headers["access-control-allow-origin"] == "http://localhost"
        assert question.json()["status"] == "needs_tender"
        assert question.json()["missing"] == ["tender"]
        assert question.json()["question"]
        assert question.json()["review_id"] == data["request_id"]
        assert_unposted()
    app.state.store.close()
    app = build(path)
    for _ in range(3):
        question = call(app, "POST", base + "/commit", "followup", {**body, "tender": "cash"}, extra_headers=origin)
        assert question.status_code == 200, question.text
        assert question.headers["content-type"].startswith("application/json")
        assert question.headers["access-control-allow-origin"] == "http://localhost"
        assert question.json()["status"] == "needs_tender"
        assert question.json()["missing"] == ["amount_received_cents"]
        assert question.json()["question"]
        assert_unposted()
    shortage = call(app, "POST", base + "/commit", "followup", {**body, "tender": "cash", "amount_received_cents": 100}, extra_headers=origin)
    assert shortage.status_code == 409
    assert shortage.json()["detail"]["code"] == "insufficient_cash"
    assert_unposted()
    paid_body = {**body, "tender": "cash", "amount_received_cents": 1000}
    paid = call(app, "POST", base + "/commit", "followup", paid_body, extra_headers=origin)
    assert paid.status_code == 200, paid.text
    assert paid.headers["content-type"].startswith("application/json")
    assert paid.headers["access-control-allow-origin"] == "http://localhost"
    receipt = paid.json()
    assert receipt["total_cents"] == 150
    assert receipt["amount_received_cents"] == 1000
    assert receipt["change_cents"] == 850
    app.state.store.close()
    app = build(path)
    assert call(app, "POST", base + "/commit", "followup", paid_body, extra_headers=origin).json() == receipt
    assert len(app.state.store.shops[UUID(SHOP)].idempotent_sales) == 1
    for product_id, stock in receipt["stock_after"].items():
        assert app.state.store.shops[UUID(SHOP)].products[UUID(product_id)].stock_qty == stock == initial_stock[UUID(product_id)] - 1
    app.state.store.close()
