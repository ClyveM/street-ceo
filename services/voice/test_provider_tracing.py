import json

import httpx
import pytest

from services.ai.tracing import SQLiteTraceStore, trace_context
from services.voice.meta_llama import _MetaModelChatClient
from services.voice.meta_voice import MetaVoiceTranscriber


@pytest.fixture
def trace_store(tmp_path, monkeypatch):
    path = tmp_path / "voice-traces.sqlite3"
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(path))
    return SQLiteTraceStore(path)


def test_voice_intent_traces_request_response_and_context_without_credentials(trace_store):
    payload = {"choices": [{"message": {"content": "two bread"}}]}
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=payload)

    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        client = _MetaModelChatClient("test-provider-secret", http)
        with trace_context("voice-cycle-1", shop_id="demo-shop"):
            result = client.create(model="test-model", messages=[{"role": "user", "content": "two bread test-provider-secret"}])
    assert result == payload
    events = trace_store.read("voice-cycle-1")
    assert {event["phase"] for event in events} == {"started", "completed"}
    assert all(event["shop_id"] == "demo-shop" for event in events)
    started = next(event for event in events if event["phase"] == "started")
    assert started["request"]["messages"][0]["content"] == "two bread [redacted]"
    completed = next(event for event in events if event["phase"] == "completed")
    assert completed["response"] == payload
    assert "test-provider-secret" not in json.dumps(events)
    assert calls[0].headers["Authorization"] == "Bearer test-provider-secret"


def test_voice_http_failure_preserves_exception_and_sanitizes_error_response(trace_store):
    def respond(request):
        return httpx.Response(429, json={"error": {"message": "retry test-provider-secret", "api_key": "hidden"}})

    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        client = _MetaModelChatClient("test-provider-secret", http)
        with trace_context("voice-failure"), pytest.raises(httpx.HTTPStatusError) as error:
            client.create(model="test-model", messages=[{"role": "user", "content": "bread"}])
    assert error.value.response.status_code == 429
    failed = next(event for event in trace_store.read("voice-failure") if event["phase"] == "failed")
    assert failed["http_status"] == 429
    assert failed["response"]["error"]["message"] == "retry [redacted]"
    assert failed["response"]["error"]["api_key"] == "[redacted]"


def test_transcription_logs_metadata_and_response_but_never_audio(trace_store, monkeypatch):
    original_audio, wav = b"PRIVATE_AUDIO_INPUT", b"PRIVATE_WAV_INPUT"
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"transcript": "  two bread  "})

    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        transcriber = MetaVoiceTranscriber("test-provider-secret", http)
        monkeypatch.setattr(transcriber, "_to_wav", lambda audio, media_type: wav)
        with trace_context("voice-transcription"):
            assert transcriber.transcribe(original_audio, "audio/webm") == "two bread"
    events = trace_store.read("voice-transcription")
    started = next(event for event in events if event["phase"] == "started")
    assert started["request"]["size_bytes"] == len(original_audio)
    assert started["request"]["wav_size_bytes"] == len(wav)
    assert started["request"]["media_type"] == "audio/webm"
    assert wav in requests[0].content
    assert "PRIVATE_AUDIO_INPUT" not in json.dumps(events)
    assert "PRIVATE_WAV_INPUT" not in json.dumps(events)
    assert "test-provider-secret" not in json.dumps(events)


def test_unavailable_trace_storage_prevents_voice_provider_call(tmp_path, monkeypatch):
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("blocked")
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(blocker / "traces.sqlite3"))
    calls = []
    with httpx.Client(transport=httpx.MockTransport(lambda request: calls.append(request))) as http:
        with pytest.raises(OSError):
            _MetaModelChatClient("test-provider-secret", http).create(model="test", messages=[])
    assert calls == []
