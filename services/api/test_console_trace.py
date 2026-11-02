"""Console provenance without a live provider or the owner's database."""
import json
from types import SimpleNamespace

import pytest

from services.ai.console_trace import emit_console_trace
from services.ai.muse import MetaMuseProvider
from services.ai.catalogue_voice import resolve_catalogue_voice
from services.ai.tracing import SQLiteTraceStore, traced_call
from services.api.test_sqlite_store import SHOP, build, call


def test_local_named_basket_and_failed_request_timing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "normal")
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "trace.sqlite3"))
    app = build(tmp_path / "shop.sqlite3")
    route = f"/api/v1/shops/{SHOP}/voice/transcript"
    response = call(app, "POST", route, "local", {"transcript": "one bread loaf"})
    assert response.status_code == 200
    output = capsys.readouterr().out
    assert 'one bread loaf' in output and 'Bread loaf' in output
    assert 'LOCAL - Muse not called' in output and 'duration_ms' in output
    assert response.headers['x-correlation-id'] in output
    bad = call(app, "POST", route, "bad", {"transcript": ""})
    assert bad.status_code == 422
    assert '"phase": "failed"' in capsys.readouterr().out
    app.state.store.close()


def test_actual_provider_payload_response_and_validated_proposal(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "detail")
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "trace.sqlite3"))
    bread = "00000000-0000-0000-0000-000000000002"
    result = {"segments": [{"segment_id": 0, "product_id": bread, "quantity": 1, "resolution": "uncertain"}]}
    calls = []
    def post(url, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"choices": [{"message": {"content": json.dumps(result)}}]})
    provider = MetaMuseProvider("private-test-key", "synthetic-test-model", SimpleNamespace(post=post))
    resolver = lambda text, products: resolve_catalogue_voice(text, products, provider=provider, allow_local_proposals=False)
    app = build(tmp_path / "shop.sqlite3", resolver)
    response = call(app, "POST", f"/api/v1/shops/{SHOP}/voice/transcript", "noisy", {"transcript": "one bread glove"})
    assert response.json()['status'] == 'needs_match_confirmation'
    output = capsys.readouterr().out
    assert 'one bread glove' in output and 'Bread loaf' in output
    assert 'MUSE REQUEST' in output and 'MUSE RESPONSE' in output and 'MUSE USED' in output
    assert 'confirmation still required' in output and 'duration_ms' in output
    assert 'private-test-key' not in output
    assert calls[0][0] == 'https://api.meta.ai/v1/chat/completions'
    assert app.state.store.shops[next(iter(app.state.store.shops))].idempotent_sales == {}
    app.state.store.close()


def test_controls_secrets_modes_and_terminal_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "detail")
    store = SQLiteTraceStore(tmp_path / "trace.sqlite3")
    payload = {"authorization": "private", "heard": "bad\x1b[2J\nFORGED", "text": "Bearer private-key"}
    traced_call(operation="test", model="fake", request=payload, call=lambda: {"ok": True}, store=store)
    output = capsys.readouterr().out
    assert '\x1b' not in output and '\\u001b' in output
    assert 'private' not in output and '\\nFORGED' in output
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "off")
    traced_call(operation="test", model="fake", request={}, call=lambda: {}, store=store)
    assert capsys.readouterr().out == ''
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "normal")
    traced_call(operation="test", model="fake", request={'secret_payload': 'hidden-detail'}, call=lambda: {}, store=store)
    assert 'hidden-detail' not in capsys.readouterr().out
    monkeypatch.setattr('builtins.print', lambda *a, **k: (_ for _ in ()).throw(OSError('closed terminal')))
    assert traced_call(operation="test", model="fake", request={}, call=lambda: 42, store=store) == 42


def test_provider_failure_never_claims_returned_or_success(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "normal")
    store = SQLiteTraceStore(tmp_path / "trace.sqlite3")
    with pytest.raises(TimeoutError):
        traced_call(operation="test", model="fake", request={}, call=lambda: (_ for _ in ()).throw(TimeoutError()), store=store)
    output = capsys.readouterr().out
    assert 'MUSE FAILED' in output and 'TimeoutError' in output
    assert 'MUSE RESPONSE' not in output


def test_oversized_payload_explicitly_shows_truncation(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "detail")
    store = SQLiteTraceStore(tmp_path / "trace.sqlite3")
    store.record({"model": "fake", "phase": "started", "request": {str(i): 'x' * 8000 for i in range(20)}})
    output = capsys.readouterr().out
    assert 'truncated' in output and 'sanitized_prefix' in output
    assert len(output) < 70000
