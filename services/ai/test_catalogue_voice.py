import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

try:
    from services.ai.catalogue_voice import resolve_catalogue_voice
    from services.ai.muse import MetaMuseProvider
    from services.ai.tracing import SQLiteTraceStore, trace_context
except ModuleNotFoundError:
    from catalogue_voice import resolve_catalogue_voice
    from muse import MetaMuseProvider
    from tracing import SQLiteTraceStore, trace_context


def resolve_provider_voice(*args, **kwargs):
    return resolve_catalogue_voice(*args, allow_local_proposals=False, **kwargs)

CATALOGUE = [
    {"product_id": "bread-id", "name": "Bread loaf", "sku": "BREAD-700", "unit_price_cents": 180},
    {"product_id": "coke-id", "name": "Coca-Cola 300ml", "sku": "COKE-300", "unit_price_cents": 150},
]


def proposal(product_id="bread-id", quantity=1, segment_id=0, resolution="uncertain"):
    return {"segment_id": segment_id, "product_id": product_id, "quantity": quantity, "resolution": resolution}


class Provider:
    def __init__(self, segments):
        self.segments = segments
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        return {"segments": self.segments}


class CatalogueVoiceTests(unittest.TestCase):
    def test_common_asr_tail_proposals_are_immediate_local_and_require_yes(self):
        class MustNotCall:
            def complete(self, request):
                raise AssertionError("local proposal must not call Muse")
        for transcript, product_id in (("1 bread glove number", "bread-id"), ("1 coca-cola nabo marble", "coke-id")):
            result = resolve_catalogue_voice(transcript, CATALOGUE, provider=MustNotCall())
            self.assertEqual(result.status, "proposed")
            self.assertEqual(result.lines[0].product_id, product_id)
            self.assertEqual(result.lines[0].quantity, 1)
            self.assertEqual(result.source, "local_catalogue_proposal")
            self.assertFalse(result.provider_called)
            self.assertTrue(result.requires_confirmation)
            self.assertIn("Say yes or no", result.question)

    def test_local_missing_quantity_is_immediate_specific_question(self):
        with patch(resolve_catalogue_voice.__module__ + "._get_provider") as build:
            result = resolve_catalogue_voice("coca-cola", CATALOGUE)
        build.assert_not_called()
        self.assertEqual(result.status, "needs_clarification")
        self.assertEqual(result.question, "How many Coca-Cola 300ml?")
        self.assertEqual(result.lines, ())
        self.assertEqual(result.source, "local_clarification")
        self.assertFalse(result.provider_called)

    def test_local_tails_never_discard_tokens_that_reference_catalogue_products(self):
        for label in ("Glove", "Number biscuits", "Nabo", "Marble"):
            catalogue = CATALOGUE + [{"product_id": "custom-id", "name": label, "sku": "CUSTOM"}]
            phrase = "1 bread glove number" if label in {"Glove", "Number biscuits"} else "1 coca-cola nabo marble"
            result = resolve_catalogue_voice(phrase, catalogue, provider=None)
            self.assertNotEqual(result.status, "proposed")
            self.assertEqual(result.lines, ())

    def test_local_unknowns_typos_apple_partial_and_ambiguous_aliases_do_not_propose(self):
        for transcript in ("1 bread unicorn", "1 coke 1 unicorn", "1 bread and unicorn", "1 bread and", "1 bread plus", "apple one coke apple", "1 bread apple", "1 bred", "1 bread 2"):
            result = resolve_catalogue_voice(transcript, CATALOGUE, provider=None)
            self.assertNotEqual(result.status, "proposed")
            self.assertEqual(result.lines, ())
        duplicate = CATALOGUE + [{"product_id": "brown-id", "name": "Bread brown", "sku": "BROWN-700"}]
        result = resolve_catalogue_voice("1 bread glove number", duplicate, provider=None)
        self.assertNotEqual(result.status, "proposed")
        self.assertEqual(result.lines, ())

    def test_catalogue_provider_connections_reused_for_same_settings(self):
        import importlib
        module = importlib.import_module(resolve_catalogue_voice.__module__)
        settings = module.MuseSettings("model", "private-test-key")
        module._cached_provider.cache_clear()
        self.addCleanup(module._cached_provider.cache_clear)
        provider = Provider([])
        with patch.object(module.MuseSettings, "from_env", return_value=settings), patch.object(module, "build_muse_ai") as build:
            build.return_value.provider = provider
            self.assertIs(module._get_provider(), provider)
            self.assertIs(module._get_provider(), provider)
        build.assert_called_once_with(settings, http_timeout_seconds=25.0)

    def test_bread_asr_noise_is_proposal_only_and_contains_catalogue_context(self):
        provider = Provider([proposal()])
        result = resolve_provider_voice("1 bread glove number", CATALOGUE, provider=provider)
        self.assertEqual(result.status, "proposed")
        self.assertEqual((result.lines[0].product_id, result.lines[0].quantity), ("bread-id", 1))
        self.assertTrue(result.requires_confirmation)
        self.assertIn("1 Bread loaf", result.question)
        self.assertNotIn("180", result.question)
        self.assertEqual(provider.requests[0].trusted_context["catalogue"][0]["product_id"], "bread-id")
        self.assertNotIn("unit_price_cents", provider.requests[0].trusted_context["catalogue"][0])
        self.assertEqual(result.source, "muse_catalogue")

    def test_coke_trailing_wake_noise_requires_confirmation(self):
        result = resolve_provider_voice("1 coca-cola nabo marble", CATALOGUE, provider=Provider([proposal("coke-id")]))
        self.assertEqual(result.status, "proposed")
        self.assertIn("1 Coca-Cola 300ml", result.question)
        self.assertTrue(result.requires_confirmation)

    def test_missing_quantity_remains_question_even_if_model_guesses_one(self):
        for quantity in (None, 1):
            result = resolve_provider_voice("coca-cola", CATALOGUE, provider=Provider([proposal("coke-id", quantity)]))
            self.assertEqual(result.status, "needs_clarification")
            self.assertEqual(result.reason, "missing_quantity")
            self.assertIn("How many Coca-Cola", result.question)
            self.assertEqual(result.lines, ())

    def test_changed_explicit_quantity_rejected(self):
        result = resolve_provider_voice("2 bread", CATALOGUE, provider=Provider([proposal(quantity=3)]))
        self.assertNotEqual(result.status, "proposed")
        self.assertEqual(result.lines, ())

    def test_unknown_item_omission_substitution_and_invented_id_never_partial(self):
        for response in ([proposal("coke-id")],
                         [proposal("coke-id"), proposal(None, 1, 1, "unknown")],
                         [proposal("coke-id"), proposal("bread-id", 1, 1)],
                         [proposal("invented-id"), proposal("bread-id", 1, 1)]):
            result = resolve_provider_voice("1 coke 1 unicorn", CATALOGUE, provider=Provider(response))
            self.assertNotEqual(result.status, "proposed")
            self.assertEqual(result.lines, ())

    def test_conjoined_item_without_quantity_is_not_dropped(self):
        result = resolve_provider_voice("1 bread and unicorn", CATALOGUE, provider=Provider([proposal()]))
        self.assertNotEqual(result.status, "proposed")
        self.assertEqual(result.lines, ())

    def test_unfinished_second_quantity_is_not_dropped(self):
        provider = Provider([proposal()])
        result = resolve_provider_voice("1 bread 2", CATALOGUE, provider=provider)
        self.assertNotEqual(result.status, "proposed")
        self.assertEqual(result.lines, ())
        self.assertEqual(result.reason, "missing_product")
        self.assertEqual(provider.requests, [])

    def test_ambiguity_boolean_quantities_extra_fields_and_duplicates_fail_closed(self):
        responses = [[proposal(resolution="ambiguous")], [proposal(quantity=True)],
                     [{**proposal(), "price": 1}], [proposal(), proposal()]]
        for response in responses:
            result = resolve_provider_voice("1 bread", CATALOGUE, provider=Provider(response))
            self.assertNotEqual(result.status, "proposed")
            self.assertEqual(result.lines, ())

    def test_provider_cannot_choose_between_equally_supported_catalogue_products(self):
        catalogue = CATALOGUE + [{"product_id": "brown-id", "name": "Bread brown", "sku": "BROWN-700"}]
        result = resolve_provider_voice("1 bread", catalogue, provider=Provider([proposal()]))
        self.assertEqual(result.status, "needs_clarification")
        self.assertEqual(result.reason, "ambiguous_product")
        self.assertEqual(result.lines, ())
        explicit = resolve_provider_voice("1 bread loaf", catalogue, provider=Provider([proposal()]))
        self.assertEqual(explicit.status, "proposed")

    def test_unconfigured_local_match_clarifies_without_claiming_muse(self):
        result = resolve_provider_voice("coca-cola", CATALOGUE, provider=None)
        self.assertEqual(result.status, "needs_clarification")
        self.assertIn("How many", result.question)
        self.assertFalse(result.provider_called)
        self.assertEqual(result.source, "local_clarification")
        self.assertEqual(result.lines, ())

    def test_provider_failure_and_timeout_are_bounded_and_nonactionable(self):
        class Broken:
            def complete(self, request):
                raise RuntimeError("private provider details")
        class Slow:
            def complete(self, request):
                time.sleep(0.1)
                return {"segments": [proposal()]}
        failed = resolve_provider_voice("1 bread", CATALOGUE, provider=Broken())
        self.assertEqual(failed.status, "unavailable")
        self.assertNotIn("private provider details", failed.question)
        started = time.monotonic()
        timed_out = resolve_provider_voice("1 bread", CATALOGUE, provider=Slow(), timeout_seconds=0.01)
        self.assertEqual(timed_out.reason, "timeout")
        self.assertIn("took too long", timed_out.question)
        self.assertIn("No sale was recorded", timed_out.question)
        self.assertNotIn("is unavailable", timed_out.question)
        self.assertLess(time.monotonic() - started, 0.08)
        self.assertEqual(timed_out.lines, ())
        time.sleep(0.11)  # let bounded worker finish before other test cases

    def test_default_demo_wait_budget_is_24_seconds_without_waiting_in_test(self):
        budgets = []
        class CompletedFuture:
            def add_done_callback(self, callback):
                callback(self)
            def result(self, timeout):
                budgets.append(timeout)
                return {"segments": [proposal()]}
        module = resolve_catalogue_voice.__module__
        with patch(module + "._EXECUTOR.submit", return_value=CompletedFuture()) as submit:
            result = resolve_provider_voice("1 bread", CATALOGUE, provider=Provider([proposal()]))
        self.assertEqual(budgets, [24.0])
        self.assertEqual(submit.call_count, 1)
        self.assertEqual(result.status, "proposed")
        self.assertTrue(result.requires_confirmation)
        with self.assertRaises(ValueError):
            resolve_provider_voice("1 bread", CATALOGUE, provider=None, timeout_seconds=24.1)

    def test_saturated_pool_returns_honest_busy_without_submitting_or_retrying(self):
        module = resolve_catalogue_voice.__module__
        with patch(module + "._CAPACITY") as capacity, patch(module + "._EXECUTOR.submit") as submit:
            capacity.acquire.return_value = False
            result = resolve_provider_voice("1 bread", CATALOGUE, provider=Provider([proposal()]))
        submit.assert_not_called()
        self.assertEqual(result.reason, "provider_busy")
        self.assertFalse(result.provider_called)
        self.assertEqual(result.source, "unavailable")
        self.assertEqual(result.lines, ())
        self.assertIn("still checking earlier requests", result.question)
        self.assertIn("No sale was recorded", result.question)

    def test_unconfigured_and_provider_error_do_not_claim_provider_outage(self):
        result = resolve_provider_voice("1 bread", CATALOGUE, provider=None)
        self.assertIn("not configured", result.question)
        self.assertFalse(result.provider_called)
        class Broken:
            def complete(self, request):
                raise RuntimeError("private provider details")
        result = resolve_provider_voice("1 bread", CATALOGUE, provider=Broken())
        self.assertEqual(result.reason, "RuntimeError")
        self.assertIn("could not complete", result.question)
        self.assertNotIn("is unavailable", result.question)
        self.assertNotIn("private provider details", result.question)

    def test_apple_framed_unknown_stays_unresolved_even_with_longer_deadline(self):
        response = [proposal(None, None, 0, "unknown"), proposal("coke-id", 1, 1, "ambiguous")]
        result = resolve_provider_voice("apple one coke apple", CATALOGUE, provider=Provider(response))
        self.assertEqual(result.status, "needs_clarification")
        self.assertEqual(result.lines, ())
        self.assertEqual(result.reason, "product_not_found")

    def test_real_adapter_traces_context_request_and_response_redacted(self):
        class Response:
            def raise_for_status(self):
                pass
            def json(self):
                return {"choices": [{"message": {"content": json.dumps({"segments": [proposal()]})}}]}
        class Client:
            def post(self, *args, **kwargs):
                return Response()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "traces.sqlite3"
            with patch.dict("os.environ", {"STREET_CEO_TRACE_DATABASE": str(path)}), trace_context("catalogue-smoke", "shop-1"):
                result = resolve_provider_voice("1 bread glove number", CATALOGUE, provider=MetaMuseProvider("private-key", "muse-model", Client()))
            self.assertEqual(result.status, "proposed")
            rows = SQLiteTraceStore(path).read("catalogue-smoke")
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["operation"] == "catalogue_voice_resolution" and row["model"] == "muse-model" for row in rows))
            self.assertIn("response", rows[0])
            self.assertIn("request", rows[1])
            self.assertNotIn("private-key", json.dumps(rows))


if __name__ == "__main__":
    unittest.main()

