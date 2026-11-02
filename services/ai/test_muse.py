import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

try:
    from services.ai.muse import MetaMuseProvider, MuseSettings, ask_muse, build_muse_ai
    from services.ai.boundary import Evidence, ProviderRequest, StructuredAI
except ModuleNotFoundError:  # unittest discovery from services/ai
    from muse import MetaMuseProvider, MuseSettings, ask_muse, build_muse_ai
    from boundary import Evidence, ProviderRequest, StructuredAI


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeHttp:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return FakeResponse(self.payload)


class FakeProvider:
    def __init__(self, value):
        self.value = value

    def complete(self, request):
        return self.value


class MuseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        env = patch.dict("os.environ", {"STREET_CEO_TRACE_DATABASE": str(Path(temporary.name) / "traces.sqlite3")})
        env.start()
        self.addCleanup(env.stop)
        self.evidence = (Evidence("sales-30d", "sales", 4280, "cents", "last_30_days"),)

    def test_meta_provider_sends_server_key_and_structured_request(self):
        response = {"choices": [{"message": {"content": json.dumps({
            "kind": "sales_trend", "title": "Sales", "summary": "Sales are recorded.",
            "evidence_ids": ["sales-30d"], "confidence": 0.8, "suggested_action": "Keep recording sales."
        })}}]}
        http = FakeHttp(response)
        provider = MetaMuseProvider("secret", "model", http)
        result = ask_muse("What were my sales?", self.evidence, ai=StructuredAI(provider))
        self.assertEqual(result.kind, "sales_trend")
        self.assertEqual(http.calls[0][1]["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(http.calls[0][1]["json"]["response_format"], {"type": "json_object"})
        system = http.calls[0][1]["json"]["messages"][0]["content"]
        schema = json.loads(system.split("with every required field and no extra fields:\n", 1)[1])
        self.assertEqual(set(schema["required"]), {
            "kind", "title", "summary", "evidence_ids", "confidence", "suggested_action"})
        self.assertFalse(schema["additionalProperties"])
        properties = schema["properties"]
        self.assertEqual(properties["kind"]["enum"], ["cash", "general", "margin", "run_out", "sales_trend"])
        self.assertEqual(properties["evidence_ids"]["items"]["enum"], ["sales-30d"])
        self.assertEqual(properties["suggested_action"]["type"], "string")
        self.assertEqual(properties["confidence"], {"type": "number", "minimum": 0, "maximum": 1})
        self.assertIn("never null", system)

    def test_captured_partial_insight_and_invalid_full_shapes_remain_rejected(self):
        full = {"kind": "sales_trend", "title": "Sales", "summary": "Recorded sales are available.",
                "evidence_ids": ["sales-30d"], "confidence": 0.8, "suggested_action": "Review recorded sales."}
        invalid = [
            # The production incident's shape must not silently become accepted.
            {"insight": "sales_total is available", "evidence_ids": ["sales-30d"]},
            {**full, "suggested_action": None},
            {**full, "insight": "extra provider field"},
            {**full, "evidence_ids": ["invented-evidence"]},
            {**full, "kind": "sales_total"},
            {**full, "confidence": "0.8"},
        ]
        for value in invalid:
            with self.subTest(value=value):
                response = {"choices": [{"message": {"content": json.dumps(value)}}]}
                provider = MetaMuseProvider("secret", "model", FakeHttp(response))
                result = ask_muse("What were my sales?", self.evidence, ai=StructuredAI(provider))
                self.assertEqual(result.kind, "unavailable")
                self.assertIn("invalid provider response", result.summary)

    def test_missing_provider_is_explicit_not_fabricated(self):
        result = ask_muse("What was my profit?", self.evidence, ai=StructuredAI(None))
        self.assertEqual(result.kind, "unavailable")
        self.assertIn("provider", result.summary.lower())

    def test_settings_without_credentials_are_unconfigured(self):
        self.assertEqual(MuseSettings("", None), MuseSettings("", None))

    def test_catalogue_http_override_does_not_change_other_muse_budgets(self):
        settings = MuseSettings("synthetic-test-model", "private-test-key")
        with patch("httpx.Client") as client, patch("truststore.SSLContext", return_value="verified-context"):
            default = build_muse_ai(settings)
            client.assert_called_once_with(verify="verified-context", timeout=20.0)
            self.assertEqual(default.timeout_seconds, 20.0)
            client.reset_mock()
            catalogue = build_muse_ai(settings, http_timeout_seconds=25.0)
            client.assert_called_once_with(verify="verified-context", timeout=25.0)
            # Catalogue calls provider directly under its own 24s resolver;
            # the shared business-insight boundary retains its default budget.
            self.assertEqual(catalogue.timeout_seconds, 20.0)

    def test_meta_provider_includes_trusted_context_for_social_catalogue_facts(self):
        response = {"choices": [{"message": {"content": json.dumps({"ok": True})}}]}
        http = FakeHttp(response)
        provider = MetaMuseProvider("secret", "muse-spark-1.3", http)
        provider.complete(ProviderRequest(
            task="social_draft",
            system_instruction="Use only supplied products.",
            untrusted_input="Create a draft.",
            trusted_context={"products": [{"product_id": "p1", "name": "Coke"}]},
            output_schema={"type": "object"},
        ))
        system = http.calls[0][1]["json"]["messages"][0]["content"]
        self.assertIn('"product_id":"p1"', system)
        self.assertIn("Trusted application context", system)

    def test_meta_provider_unwraps_text_json_envelope(self):
        nested = {"kind": "sales_trend", "title": "Sales", "summary": "Recorded.", "evidence_ids": [], "confidence": 0.5, "suggested_action": "Review."}
        response = {"choices": [{"message": {"content": json.dumps({"text": json.dumps(nested)})}}]}
        provider = MetaMuseProvider("secret", "muse-spark-1.3", FakeHttp(response))
        result = provider.complete(ProviderRequest("business_insight", "Return JSON.", "Question", {}, {}))
        self.assertEqual(result, nested)


if __name__ == "__main__":
    unittest.main()
