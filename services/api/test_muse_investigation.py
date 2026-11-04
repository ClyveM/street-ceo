"""Deterministic Muse investigation fixtures, no live Meta calls."""
import json

from services.ai.boundary import StructuredAI
from services.ai.investigation import investigate
from services.ai.muse import MetaMuseProvider
from services.api.app import InMemoryStore
from services.api.muse_tools import toolset


def demo_tools():
    store = InMemoryStore()
    return toolset(store.shops[store.seed_demo_shop()])


class FixtureProvider:
    def __init__(self):
        self.steps = 0

    def complete(self, request):
        self.steps += 1
        results = request.trusted_context["tool_results"]
        if self.steps == 1:
            return {"calls": [{"tool": "discover_business_data", "arguments": {}}]}
        if self.steps == 2:
            assert results[0]["data"]["sales"]["record_count"] == 0
            return {"calls": [
                {"tool": "assess_financing", "arguments": {
                    "monthly_budget_cents": 34071, "annual_interest_percent": 10,
                    "terms_months": [3, 10, 12, 24], "upfront_fees_cents": 0,
                }},
                {"tool": "query_inventory", "arguments": {"limit": 2}},
            ]}
        assert [row["illustrative_principal_cents"] for row in results[1]["data"]["scenarios"]] == [
            100532, 325600, 387540, 738347,
        ]
        assert len(results[2]["data"]["rows"]) == 2
        return {"calls": [], "title": "Financing plan", "answer": "Here is the plan.",
                "sections": [{"title": "Repayment", "body": "Compare all four terms.",
                              "evidence_ids": ["evidence-2", "invented"]}]}


def test_iterative_discovery_financing_and_document():
    provider = FixtureProvider()
    result = investigate(StructuredAI(provider), "Draft a business plan", demo_tools(), {})
    assert provider.steps == 3
    assert result["sections"][0]["evidence_ids"] == ["evidence-2"]
    assert not result["partial"]


class InvalidProvider:
    def complete(self, request):
        return {"calls": [{"tool": "query_inventory", "arguments": {"shop_id": "other"}},
                          {"tool": "execute_sql", "arguments": {}}]}


def test_invalid_tool_calls_are_bounded_and_cannot_switch_shop():
    result = investigate(StructuredAI(InvalidProvider()), "Run anything", demo_tools(), {})
    assert result["partial"]
    assert result["evidence_ids"] == []


class NativeClient:
    def __init__(self):
        self.requests = []

    def post(self, _url, *, headers, json):
        self.requests.append(json)
        assert any(tool["function"]["name"] == "discover_business_data" for tool in json["tools"])
        return self

    def raise_for_status(self):
        pass

    def json(self):
        if len(self.requests) == 1:
            message = {"content": None, "tool_calls": [{"id": "call_x", "type": "function",
                       "function": {"name": "discover_business_data", "arguments": "{}"}}]}
        else:
            history = self.requests[-1]["messages"]
            assert history[-2]["tool_calls"][0]["id"] == history[-1]["tool_call_id"] == "call_x"
            assert json.loads(history[-1]["content"])["data"]["sales"]["record_count"] == 0
            message = {"content": json.dumps({"calls": [], "title": "Coverage",
                       "answer": "No recorded receipts yet.", "sections": []})}
        return {"choices": [{"message": message}]}


def test_native_tool_protocol_replays_matching_assistant_and_tool_results(monkeypatch):
    monkeypatch.setattr("services.ai.muse.traced_call", lambda **kwargs: kwargs["call"]())
    client = NativeClient()
    ai = StructuredAI(MetaMuseProvider("fixture", "muse-spark-1.3", client))
    result = investigate(ai, "What coverage do we have?", demo_tools(), {})
    assert result["evidence_ids"] == ["evidence-1"]
    assert not result["partial"]

def test_sample_and_connected_jobs_use_separate_records_and_label_document(tmp_path, monkeypatch):
    import asyncio
    from datetime import datetime
    from zoneinfo import ZoneInfo

    import httpx

    from services.api.app import create_app
    from services.api.persistence import Settings
    from services.api.seed_sample_history import SAMPLE_SHOP_ID, add_sample_receipts, sample_catalogue

    class ScopedProvider:
        def complete(self, request):
            context = request.trusted_context
            results = context["tool_results"]
            if not results:
                return {"calls": [{"tool": "discover_business_data", "arguments": {}}]}
            receipts = results[0]["data"]["sales"]["receipts"]
            if context["data_scope"] == "sample":
                assert receipts == 2
            else:
                assert context["data_scope"] == "connected_shop" and receipts == 0
            return {"calls": [], "title": "Financing plan", "answer": f"Receipt count: {receipts}.",
                    "document_type": "business_plan", "sections": [{"title": "Sales evidence",
                        "body": f"{receipts} receipts.", "evidence_ids": ["evidence-1"]}]}

    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.db"))
    store = InMemoryStore()
    live = store.seed_demo_shop()
    sample = sample_catalogue()
    today = datetime.now(ZoneInfo(sample.shop.timezone)).date()
    add_sample_receipts(store, sample, today, today, daily_target=2)
    store.shops[SAMPLE_SHOP_ID] = sample
    app = create_app(store, Settings(demo_seed_enabled=True), muse_ai=StructuredAI(ScopedProvider()))

    async def exercise():
        async with app.router.lifespan_context(app), httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test",
        ) as client:
            async def run(shop):
                base = f"/api/v1/shops/{shop}/muse/jobs"
                headers = {"X-Shop-ID": str(shop), "Idempotency-Key": "scope-test"}
                queued = await client.post(base, headers=headers, json={"question": "Write a business plan"})
                assert queued.status_code == 202
                async with asyncio.timeout(3):
                    while True:
                        payload = (await client.get(f"{base}/{queued.json()['job_id']}", headers=headers)).json()
                        if payload["status"] == "succeeded":
                            return payload["result"]
                        assert payload["status"] in {"running", "queued"}, payload
                        await asyncio.sleep(.01)
            sample_result = await run(SAMPLE_SHOP_ID)
            live_result = await run(live)
            assert sample_result["answer"].startswith("Sample shop")
            assert "Receipt count: 2" in sample_result["answer"]
            assert sample_result["document"]["sections"][0]["title"] == "Data provenance"
            assert live_result["answer"] == "Receipt count: 0."
            assert live_result["document"]["sections"][0]["title"] == "Sales evidence"

    asyncio.run(exercise())
