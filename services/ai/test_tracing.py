import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    from services.ai.tracing import SQLiteTraceStore, sanitize_trace, trace_context, traced_call
    from services.ai.muse import MetaMuseProvider
    from services.ai.boundary import ProviderRequest, StructuredAI, Evidence, InsightRequest
except ModuleNotFoundError:
    from tracing import SQLiteTraceStore, sanitize_trace, trace_context, traced_call
    from muse import MetaMuseProvider
    from boundary import ProviderRequest, StructuredAI, Evidence, InsightRequest


class TracingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "trace.sqlite3"
        self.env = patch.dict("os.environ", {"STREET_CEO_TRACE_DATABASE": str(self.path)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_real_file_reopen_preserves_request_and_response_with_correlation(self):
        expected = {"action": "record_sale", "item": "Bread", "quantity": 2}
        with trace_context("request-1", "shop-1", "voice"):
            result = traced_call(operation="voice_intent", model="model-1", request={"transcript": "2 Bread"}, call=lambda: expected)
        self.assertIs(result, expected)
        rows = SQLiteTraceStore(self.path).read("request-1")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["phase"], "completed")
        self.assertEqual(rows[0]["response"], expected)
        self.assertEqual(rows[1]["request"]["transcript"], "2 Bread")
        self.assertEqual(rows[0]["shop_id"], "shop-1")
        self.assertEqual(rows[0]["trace_id"], rows[1]["trace_id"])

    def test_redacts_nested_secrets_binary_pii_and_bounded_payloads(self):
        sensitive_assignment = "api_" + "key=" + '"hidden-value"'
        value = {"headers": {"Authorization": "Bearer top-secret"}, "audio_base64": "encoded-audio",
                 "bytes": b"raw-audio", "content": 'Contact demo@example.com +263 771 123 456 ' + sensitive_assignment + ' top-secret',
                 "image": "data:image/png;base64,abc", "large": "x" * 20000}
        safe = json.dumps(sanitize_trace(value, ("top-secret",)))
        for forbidden in ("top-secret", "encoded-audio", "raw-audio", "demo@example.com", "263 771", "hidden-value", "base64,abc"):
            self.assertNotIn(forbidden, safe)
        self.assertIn("truncated", safe)
        huge = sanitize_trace({str(n): "x" * 8000 for n in range(100)})
        self.assertLess(len(json.dumps(huge)), 20000)
        self.assertTrue(huge["truncated"])

    def test_http_failure_persists_sanitized_error_response_and_never_success(self):
        class Response:
            status_code = 429
            def json(self):
                return {"error": {"message": "Bearer private-value", "api_key": "private-value"}}
        class Failure(Exception):
            response = Response()
        def fail():
            raise Failure("Do not log private-value")
        with self.assertRaises(Failure):
            traced_call(operation="voice_intent", model="model", request={}, call=fail, secret_values=("private-value",))
        rows = SQLiteTraceStore(self.path).read()
        self.assertEqual({row["phase"] for row in rows}, {"started", "failed"})
        self.assertEqual(rows[0]["http_status"], 429)
        self.assertNotIn("private-value", json.dumps(rows))

    def test_unavailable_trace_store_prevents_provider_call(self):
        class FailingStore:
            def record(self, trace):
                raise OSError("storage full")
        calls = []
        with self.assertRaises(OSError):
            traced_call(operation="voice", model="model", request={}, call=lambda: calls.append(True), store=FailingStore())
        self.assertEqual(calls, [])

    def test_provider_worker_keeps_api_context_and_raw_json_response(self):
        class Response:
            def raise_for_status(self):
                pass
            def json(self):
                return {"choices": [{"message": {"content": json.dumps({"kind": "sales_trend", "title": "Sales", "summary": "Recorded.", "evidence_ids": ["sales"], "confidence": 0.8, "suggested_action": "Continue."})}}]}
        class Client:
            def post(self, *args, **kwargs):
                return Response()
        with trace_context("api-worker", "shop-2"):
            result = StructuredAI(MetaMuseProvider("credential", "model", Client())).business_insight(
                InsightRequest((Evidence("sales", "sales", 100, "cents", "today"),), "How are sales?"))
        self.assertEqual(result.source, "provider")
        rows = SQLiteTraceStore(self.path).read("api-worker")
        self.assertEqual(len(rows), 2)
        self.assertIn("choices", rows[0]["response"])
        self.assertEqual(rows[0]["shop_id"], "shop-2")
        self.assertNotIn("credential", json.dumps(rows))

    def test_context_does_not_leak_to_next_request(self):
        with trace_context("first"):
            SQLiteTraceStore(self.path).record({"phase": "started"})
        SQLiteTraceStore(self.path).record({"phase": "started"})
        rows = SQLiteTraceStore(self.path).read()
        self.assertNotEqual(rows[0]["correlation_id"], "first")
        self.assertEqual(rows[1]["correlation_id"], "first")

    def test_oversized_event_retains_sanitized_shop_investigation_envelope(self):
        store = SQLiteTraceStore(self.path)
        with trace_context("oversized-request", "shop-investigate", "voice"):
            store.record({"phase": "completed", "operation": "voice_intent", "model": "muse-model",
                          "source": "provider", "provider_called": True,
                          "status_code": 422, "error_type": "ValidationError",
                          "request": {str(n): "a" * 8000 for n in range(100)},
                          "response": {"Authorization": "Bearer hidden-credential"}})
        # Reopen the real file and apply the same shop-scoping filter as the
        # investigation API, independently of correlation lookup.
        rows = [row for row in SQLiteTraceStore(self.path).read() if row.get("shop_id") == "shop-investigate"]
        self.assertEqual(len(rows), 1)
        event = rows[0]
        self.assertEqual(event["correlation_id"], "oversized-request")
        self.assertEqual(event["operation"], "voice_intent")
        self.assertEqual(event["model"], "muse-model")
        self.assertEqual(event["phase"], "completed")
        self.assertEqual(event["source"], "provider")
        self.assertIs(event["provider_called"], True)
        self.assertEqual(event["status_code"], 422)
        self.assertEqual(event["error_type"], "ValidationError")
        self.assertTrue(event["payload"]["truncated"])
        self.assertNotIn("hidden-credential", json.dumps(event))
        self.assertLess(len(json.dumps(event).encode()), 65536)

    def test_oversized_unicode_body_and_metadata_stay_bounded_and_redacted(self):
        store = SQLiteTraceStore(self.path)
        store.record({"correlation_id": "unicode-case", "shop_id": "Bearer hidden-credential",
                      "operation": "x" * 20000, "model": {"password": "hidden-password"},
                      "source": "api_key=hidden-value", "provider_called": False,
                      "response": {str(n): "\U0001f600" * 8000 for n in range(100)}})
        event = store.read("unicode-case")[0]
        self.assertEqual(event["shop_id"], "Bearer [redacted]")
        self.assertLessEqual(len(event["operation"]), 256)
        self.assertEqual(event["model"], "[invalid metadata]")
        self.assertFalse(event["provider_called"])
        encoded = json.dumps(event)
        for secret in ("hidden-credential", "hidden-password", "hidden-value"):
            self.assertNotIn(secret, encoded)
        self.assertLess(len(encoded.encode()), 65536)


if __name__ == "__main__":
    unittest.main()
