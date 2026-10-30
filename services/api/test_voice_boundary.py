import base64
from uuid import UUID

import pytest
from fastapi import HTTPException

from services.api.app import InMemoryStore, ShopCreate, create_app
from services.api.persistence import Settings
from services.api.voice_boundary import VoiceAudioRequest, VoiceTranscriptRequest


class FakeInterpreter:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def interpret(self, text):
        self.calls += 1
        return self.result


class Intent:
    action = "record_sale"
    item = "Bread"
    quantity = 2
    price_override_minor = None
    needs_confirmation = False


def setup_voice(interpreter=None):
    app = create_app(InMemoryStore(), Settings(voice_enabled=True), voice_interpreter=interpreter)
    create_shop = next(route.endpoint for route in app.routes if route.path == "/shops")
    shop = create_shop(ShopCreate(name="Voice Shop"))
    record = app.state.store.shops[shop.id]
    transcript = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/transcript")
    audio = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/audio")
    return app, shop, record, transcript, audio


def test_transcript_returns_bounded_intent_and_never_posts_sale():
    interpreter = FakeInterpreter(Intent())
    _, shop, record, endpoint, _ = setup_voice(interpreter)
    response = endpoint(VoiceTranscriptRequest(transcript="sell two bread"), record, "voice-1")
    assert response.shop_id == shop.id
    assert response.status == "needs_confirmation"
    assert response.intent.action == "record_sale"
    assert response.intent.needs_confirmation is True
    assert record.idempotent_sales == {}
    assert interpreter.calls == 1


def test_transcript_replay_is_idempotent_and_changed_payload_conflicts():
    interpreter = FakeInterpreter(Intent())
    _, _, record, endpoint, _ = setup_voice(interpreter)
    request = VoiceTranscriptRequest(transcript="sell two bread")
    first = endpoint(request, record, "voice-1")
    replay = endpoint(request, record, "voice-1")
    assert replay == first
    assert interpreter.calls == 1
    with pytest.raises(HTTPException, match="payload mismatch"):
        endpoint(VoiceTranscriptRequest(transcript="sell three bread"), record, "voice-1")


def test_audio_boundary_validates_and_returns_safe_unavailable_status():
    _, shop, record, _, endpoint = setup_voice()
    audio = base64.b64encode(b"fixture-audio").decode()
    response = endpoint(VoiceAudioRequest(audio_base64=audio), record, "audio-1")
    assert response.shop_id == shop.id
    assert response.status == "unavailable"
    assert response.error == "audio_transcription_unavailable"
    assert response.transcript is None


def test_audio_replay_and_invalid_payload_are_safe():
    _, _, record, _, endpoint = setup_voice()
    request = VoiceAudioRequest(audio_base64=base64.b64encode(b"fixture-audio").decode())
    first = endpoint(request, record, "audio-1")
    assert endpoint(request, record, "audio-1") == first
    with pytest.raises(HTTPException, match="payload mismatch"):
        endpoint(VoiceAudioRequest(audio_base64=base64.b64encode(b"different").decode()), record, "audio-1")


def test_voice_disabled_returns_not_found():
    app = create_app(InMemoryStore(), Settings(voice_enabled=False))
    shop_endpoint = next(route.endpoint for route in app.routes if route.path == "/shops")
    shop = shop_endpoint(ShopCreate(name="Disabled Voice Shop"))
    record = app.state.store.shops[shop.id]
    endpoint = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/transcript")
    with pytest.raises(HTTPException) as error:
        endpoint(VoiceTranscriptRequest(transcript="sell bread"), record, "voice-1")
    assert error.value.status_code == 404
