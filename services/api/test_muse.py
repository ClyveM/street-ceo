from services.ai.boundary import StructuredAI
from services.api.app import InMemoryStore, MuseAskRequest, ShopCreate, create_app
from services.api.persistence import Settings


def endpoint(app, path):
    return next(route.endpoint for route in app.routes if route.path == path)


class FakeProvider:
    def complete(self, request):
        return {
            "kind": "general",
            "title": "Sales recorded",
            "summary": "No sales were recorded in the available period.",
            "evidence_ids": ["sales-available", "transactions-available"],
            "confidence": 1,
            "suggested_action": "Keep recording sales.",
        }


def test_profit_question_never_returns_revenue_as_profit():
    app = create_app(InMemoryStore())
    shop = endpoint(app, "/shops")(ShopCreate(name="Test shop"))
    record = app.state.store.shops[shop.id]
    result = endpoint(app, "/api/v1/shops/{shop_id}/muse")(
        type("Request", (), {"question": "What profit did I make in the last 30 days?"})(), record
    )
    assert result.status == "needs_data"
    assert "cannot calculate profit" in result.answer
    assert "COGS" in result.missing_data[0]


def test_non_financial_question_uses_validated_meta_result():
    app = create_app(InMemoryStore(), muse_ai=StructuredAI(FakeProvider()))
    shop = endpoint(app, "/shops")(ShopCreate(name="Test shop"))
    record = app.state.store.shops[shop.id]
    result = endpoint(app, "/api/v1/shops/{shop_id}/muse")(
        type("Request", (), {"question": "What should I focus on?"})(), record
    )
    assert result.status == "answered"
    assert result.source == "meta"
    assert result.evidence_ids == ["sales-available", "transactions-available"]


def test_local_demo_seed_matches_frontend_shop_id_without_sales():
    app = create_app(InMemoryStore(), Settings(demo_seed_enabled=True))

    demo_shop_id = "00000000-0000-0000-0000-000000000001"
    assert app.state.demo_shop_id == demo_shop_id
    record = app.state.store.shops[next(iter(app.state.store.shops))]
    assert str(record.shop.id) == demo_shop_id
    assert record.idempotent_sales == {}
    assert len(record.products) == 6

    result = endpoint(app, "/api/v1/shops/{shop_id}/muse")(
        type("Request", (), {"question": "What profit did I make in the last 30 days?"})(), record
    )
    assert result.status == "needs_data"
    assert result.evidence_ids == ["sales-last_30_days", "transactions-last_30_days"]


def test_default_local_app_seeds_the_frontend_shop_id(monkeypatch):
    monkeypatch.delenv("STREET_CEO_STORE", raising=False)
    monkeypatch.delenv("STREET_CEO_SEED_DEMO", raising=False)
    app = create_app()

    demo_shop_id = "00000000-0000-0000-0000-000000000001"
    assert app.state.demo_shop_id == demo_shop_id
    record = app.state.store.shops[next(iter(app.state.store.shops))]
    result = endpoint(app, "/api/v1/shops/{shop_id}/muse")(
        MuseAskRequest(question="What profit did I make in the last 30 days?"), record
    )

    assert str(record.shop.id) == demo_shop_id
    assert result.status == "needs_data"
    assert "cannot calculate profit" in result.answer

