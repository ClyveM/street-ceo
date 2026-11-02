"""CORS preflight coverage: Android WebView origin and strict rejection."""
import asyncio

from services.api.app import InMemoryStore, create_app


def preflight(origin: str):
    app = create_app(InMemoryStore())
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "scheme": "http", "method": "OPTIONS", "path": "/api/v1/shops/demo/voice/transcript",
        "raw_path": b"/api/v1/shops/demo/voice/transcript", "query_string": b"", "root_path": "",
        "headers": [(b"origin", origin.encode()), (b"access-control-request-method", b"POST"),
                    (b"access-control-request-headers", b"content-type,x-shop-id,idempotency-key")],
        "server": ("test", 80), "client": ("test", 1),
    }
    asyncio.run(app(scope, receive, send))
    return sent[0]["status"], dict(sent[0]["headers"])


def test_capacitor_android_origin_allows_voice_preflight():
    status, headers = preflight("http://localhost")
    assert status == 200
    assert headers[b"access-control-allow-origin"] == b"http://localhost"
    assert b"idempotency-key" in headers[b"access-control-allow-headers"]


def test_untrusted_origin_is_not_allowed():
    status, headers = preflight("https://untrusted.example")
    assert status == 400
    assert b"access-control-allow-origin" not in headers


def test_existing_vite_origin_remains_allowed():
    status, headers = preflight("http://localhost:5173")
    assert status == 200
    assert headers[b"access-control-allow-origin"] == b"http://localhost:5173"
