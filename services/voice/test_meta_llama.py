import json

from services.voice.meta_llama import MetaLlamaInterpreter, MetaLlamaSettings


class Message:
    def __init__(self, content):
        self.content = content


class Response:
    def __init__(self, content):
        self.completion_message = Message(content)


class FakeCompletions:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return Response(self.content)


def test_meta_llama_maps_transcript_to_bounded_sale_intent():
    client = FakeCompletions(json.dumps({
        "action": "record_sale", "item": "bread", "quantity": 2,
        "price_override_minor": None, "needs_confirmation": True,
    }))
    intent = MetaLlamaInterpreter(client, "test-model").interpret("two bread")
    assert intent.action == "record_sale"
    assert intent.item == "bread"
    assert intent.quantity == 2
    assert client.calls[0]["model"] == "test-model"


def test_meta_llama_rejects_non_json_provider_output():
    client = FakeCompletions("not json")
    try:
        MetaLlamaInterpreter(client, "test-model").interpret("bread")
    except ValueError as exc:
        assert "valid JSON" in str(exc)
    else:
        raise AssertionError("invalid provider output should fail closed")


def test_meta_settings_read_local_environment(monkeypatch):
    monkeypatch.setenv("LLAMA_API_KEY", "local-only")
    monkeypatch.setenv("LLAMA_MODEL", "llama-test")
    settings = MetaLlamaSettings.from_env()
    assert settings.api_key == "local-only"
    assert settings.model == "llama-test"
