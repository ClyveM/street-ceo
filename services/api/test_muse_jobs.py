"""Ask Muse jobs through ASGI lifespan with an isolated SQLite file."""
import asyncio
import json
import sqlite3
import threading
from uuid import UUID

import httpx
import pytest

from services.ai.tracing import SQLiteTraceStore
from services.api.app import create_app
from services.api.persistence import Settings
from services.api.test_muse import FakeProvider

SHOP = "00000000-0000-0000-0000-000000000001"
BASE = f"/api/v1/shops/{SHOP}/muse/jobs"
QUESTION = {"question": "What should I focus on? token=private-value"}
HEADERS = {"X-Shop-ID": SHOP, "Idempotency-Key": "job-key"}


class ControlledAI:
    def __init__(self, fail=False):
        self.started = threading.Event()
        self.release = threading.Event()
        self.calls = 0
        self.fail = fail

    def shop_data_plan(self, question, today):
        self.calls += 1
        self.started.set()
        if not self.release.wait(5):
            raise RuntimeError("test gate timed out")
        if self.fail:
            raise RuntimeError("secret=never-return")
        return {}

    def business_insight(self, request):
        from services.ai.boundary import StructuredAI
        return StructuredAI(FakeProvider()).business_insight(request)


def build(path, ai):
    return create_app(
        settings=Settings(store_backend="sqlite", sqlite_path=str(path), demo_seed_enabled=True),
        muse_ai=ai, voice_catalogue_resolver=None,
    )


def client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", headers=HEADERS)


async def terminal(http, url):
    async with asyncio.timeout(5):
        while True:
            response = await http.get(url)
            assert response.status_code == 200, response.text
            if response.json()["status"] in {"succeeded", "failed", "expired"}:
                return response.json()
            await asyncio.sleep(.01)


@pytest.mark.parametrize("provider_seconds", [5, 15, 30, 60])
def test_model_wait_is_outside_shop_transaction(tmp_path, monkeypatch, provider_seconds):
    from services.api.muse_jobs import MuseJobs

    now = [1000]
    init = MuseJobs.__init__

    def with_clock(self, path):
        init(self, path, clock=lambda: now[0])

    monkeypatch.setattr(MuseJobs, "__init__", with_clock)
    trace_path = tmp_path / "traces.db"
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(trace_path))
    ai = ControlledAI()
    app = build(tmp_path / "shop.db", ai)

    async def run():
        async with app.router.lifespan_context(app), client(app) as http:
            try:
                other = await http.post("/shops", json={"name": "Other shop"})
                other_shop_id = other.json()["id"]
                assert (await http.post(BASE, json=QUESTION, headers={"X-Shop-ID": other_shop_id})).status_code == 403
                results = await asyncio.gather(*(http.post(BASE, json=QUESTION) for _ in range(2)))
                submitted, replay = results
                assert submitted.status_code == replay.status_code == 202
                job = submitted.json()
                job_id = job["job_id"]
                assert UUID(job_id).version == 4
                assert job["status"] == "queued"
                assert submitted.headers["X-Correlation-ID"] == job_id == replay.json()["job_id"]
                url = f"{BASE}/{job_id}"
                assert await asyncio.to_thread(ai.started.wait, 2)
                assert (await http.post(BASE, json={"question": "different"})).status_code == 409
                assert (await http.get(url, headers={"X-Shop-ID": other_shop_id})).status_code == 403
                other_url = url.replace(SHOP, other_shop_id)
                assert (await http.get(other_url, headers={"X-Shop-ID": other_shop_id})).status_code == 404
                now[0] += provider_seconds
                assert (await asyncio.wait_for(http.get(url), 2)).json()["status"] == "running"
                assert (await asyncio.wait_for(http.get("/healthz"), 2)).status_code == 200
                ai.release.set()
                completed = await terminal(http, url)
                assert completed["status"] == "succeeded"
                assert completed["result"]["source"] == "meta"
                assert completed["result"]["evidence_ids"] == ["sales-month", "receipts-month"]
                assert (await http.post(BASE, json=QUESTION)).json() == completed
                assert ai.calls == 1
                events = SQLiteTraceStore(trace_path).read(correlation_id=job_id)
                assert {event["phase"] for event in events} == {"started", "completed"}
                assert "private-value" not in json.dumps(events)
                assert "job-key" not in json.dumps(events)
            finally:
                ai.release.set()

    asyncio.run(run())
    app.state.store.close()


def test_restart_recovers_running_job_and_preserves_result(tmp_path, monkeypatch):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.db"))
    path = tmp_path / "shop.db"

    async def run():
        original = ControlledAI()
        app = build(path, original)
        try:
            async with app.router.lifespan_context(app), client(app) as http:
                queued = (await http.post(BASE, json=QUESTION)).json()
                assert await asyncio.to_thread(original.started.wait, 2)
                url = f"{BASE}/{queued['job_id']}"
                assert (await http.get(url)).json()["status"] == "running"
        finally:
            original.release.set()
            app.state.store.close()

        ai = ControlledAI()
        ai.release.set()
        app = build(path, ai)
        async with app.router.lifespan_context(app), client(app) as http:
            completed = await terminal(http, url)
            assert completed["status"] == "succeeded"
        app.state.store.close()

        unused = ControlledAI()
        app = build(path, unused)
        async with app.router.lifespan_context(app), client(app) as http:
            assert (await http.get(url)).json() == completed
            assert (await http.post(BASE, json=QUESTION)).json() == completed
            assert unused.calls == 0
        app.state.store.close()

    asyncio.run(run())


def test_job_failure_is_safe_and_expiry_scrubs_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "traces.db"))
    path = tmp_path / "shop.db"
    ai = ControlledAI(fail=True)
    ai.release.set()
    app = build(path, ai)

    async def run():
        async with app.router.lifespan_context(app), client(app) as http:
            assert (await http.post(BASE, json=QUESTION, headers={"Idempotency-Key": ""})).status_code == 400
            assert (await http.post(BASE, json={"question": "  "})).status_code == 422
            job = (await http.post(BASE, json=QUESTION)).json()
            url = f"{BASE}/{job['job_id']}"
            failed = await terminal(http, url)
            assert failed["status"] == "failed"
            assert failed["result"] is None
            assert "never-return" not in failed["error"]
            with sqlite3.connect(path) as db:
                db.execute("UPDATE muse_jobs SET expires=unixepoch()-1 WHERE id=?", (job["job_id"],))
            expired = (await http.get(url)).json()
            assert expired["status"] == "expired"
            assert (await http.post(BASE, json=QUESTION)).json() == expired
            with sqlite3.connect(path) as db:
                assert db.execute("SELECT body, result FROM muse_jobs").fetchone() == (None, None)
            assert ai.calls == 1

    asyncio.run(run())
    app.state.store.close()
