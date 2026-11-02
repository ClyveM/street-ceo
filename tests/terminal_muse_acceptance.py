"""Independent console/investigation acceptance; only temporary shops and fake HTTP."""
import json

from services.ai.catalogue_voice import resolve_catalogue_voice
from services.ai.console_trace import emit_console_trace
from services.ai.muse import MetaMuseProvider
from services.ai.tracing import SQLiteTraceStore, traced_call
from services.api.test_sqlite_store import SHOP, build, call


def test_real_local_review_logs_named_basket_and_no_provider(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "normal")
    trace = tmp_path / "trace.sqlite3"
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(trace))
    app = build(tmp_path / "shop.sqlite3")
    response = call(app, "POST", f"/api/v1/shops/{SHOP}/voice/transcript",
                    "local", {"transcript": "one bread loaf"})
    assert response.status_code == 200
    log = capsys.readouterr().out
    assert "one bread loaf" in log and "Bread loaf" in log
    assert "Muse not called" in log and "MUSE REQUEST" not in log
    assert "duration_ms" in log and response.headers["x-correlation-id"] in log
    assert "needs_confirmation" in log
    rows = SQLiteTraceStore(trace).read(response.headers["x-correlation-id"])
    assert any(e.get("phase") == "completed" and e.get("provider_called") is False for e in rows)
    assert len(app.state.store.shops[next(iter(app.state.store.shops))].idempotent_sales) == 0
    app.state.store.close()


def test_real_provider_adapter_shows_misheard_input_actual_json_and_proposal(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "detail")
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "trace.sqlite3"))
    bread = "00000000-0000-0000-0000-000000000002"
    requests = []

    class Http:
        def post(self, url, **kwargs):
            requests.append((url, kwargs))

            class Response:
                def raise_for_status(self):
                    pass

                def json(self):
                    return {"choices": [{"message": {"content": json.dumps({"segments": [
                        {"segment_id": 0, "product_id": bread, "quantity": 1, "resolution": "uncertain"}
                    ]})}}]}
            return Response()

    provider = MetaMuseProvider("synthetic-private-key", "synthetic-model", Http())
    resolver = lambda transcript, products: resolve_catalogue_voice(
        transcript, products, provider=provider, allow_local_proposals=False)
    app = build(tmp_path / "shop.sqlite3", resolver)
    response = call(app, "POST", f"/api/v1/shops/{SHOP}/voice/transcript",
                    "noisy", {"transcript": "one bread glove"})
    assert response.status_code == 200 and response.json()["status"] == "needs_match_confirmation"
    log = capsys.readouterr().out
    assert "one bread glove" in log and "Bread loaf" in log
    assert "MUSE REQUEST" in log and "MUSE RESPONSE" in log and "MUSE USED" in log
    assert "synthetic-model" in log and "choices" in log and "segments" in log
    assert "synthetic-private-key" not in log
    assert response.headers["x-correlation-id"] in log and "duration_ms" in log
    assert "validation/confirmation still required" in log
    assert len(requests) == 1 and requests[0][0].endswith("/chat/completions")
    assert "catalogue" in requests[0][1]["json"]["messages"][0]["content"]
    assert all(not record.idempotent_sales for record in app.state.store.shops.values())
    app.state.store.close()


def test_console_controls_redaction_bounds_and_off_does_not_disable_persistence(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "detail")
    store = SQLiteTraceStore(tmp_path / "trace.sqlite3")
    value = {"text": "bad\x1b[2J\r\nforged", "password": "private-password", "email": "person@example.test",
             "Authorization": "Bearer private-token", "long": "x" * 20000}
    traced_call(operation="test", model="fake", request=value, call=lambda: value, store=store)
    log = capsys.readouterr().out
    assert "\x1b" not in log and "\r" not in log and "\\u001b" in log
    assert "private-password" not in log and "private-token" not in log and "person@example.test" not in log
    assert "[truncated]" in log and len(log) < 25000
    before = len(store.read())
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "off")
    traced_call(operation="test", model="fake", request={}, call=lambda: {}, store=store)
    assert capsys.readouterr().out == ""
    assert len(store.read()) == before + 2


def test_broken_terminal_never_changes_provider_result(tmp_path, monkeypatch):
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "detail")
    store = SQLiteTraceStore(tmp_path / "trace.sqlite3")

    def fail(*args, **kwargs):
        raise BrokenPipeError()

    monkeypatch.setattr("builtins.print", fail)
    assert traced_call(operation="test", model="fake", request={}, call=lambda: {"ok": True}, store=store) == {"ok": True}
    assert len(store.read()) == 2


def test_oversized_provider_payload_is_marked_truncated_in_terminal(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "detail")
    store = SQLiteTraceStore(tmp_path / "trace.sqlite3")
    store.record({"phase": "started", "model": "fake", "operation": "large",
                  "request": {str(n): "x" * 8000 for n in range(100)}})
    log = capsys.readouterr().out
    assert "MUSE REQUEST" in log
    assert '"truncated": true' in log
    assert len(log) < 35000
