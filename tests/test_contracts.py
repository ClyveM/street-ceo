"""Executable checks for the agreed Street CEO backend conventions.

These checks intentionally use the standard library so they can run from a
fresh checkout before the application dependency lockfile exists.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProjectContractTests(unittest.TestCase):
    def test_required_architecture_and_api_contracts_exist(self) -> None:
        for relative in ("docs/architecture.md", "docs/api-contracts.md"):
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file(), f"Missing {relative}")

    def test_mutations_have_the_required_safety_conventions(self) -> None:
        contract = (ROOT / "docs/api-contracts.md").read_text(encoding="utf-8")
        required_phrases = (
            ("validation", "request validation is documented"),
            ("x-shop-id", "shop authorization boundary is documented"),
            ("idempotency-key", "idempotency keys are documented"),
            ("auditable", "audit data is preserved"),
        )
        for phrase, failure in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, contract.lower(), failure)
        self.assertTrue(
            "reversal" in contract.lower() or "idempotency" in contract.lower(),
            "Mutation safety must document reversal or an equivalent idempotent recovery path.",
        )

    def test_architecture_keeps_ai_and_voice_boundaries_safe(self) -> None:
        architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8").lower()
        self.assertIn("schema-validated", architecture)
        self.assertIn("voice never posts an unconfirmed sale", architecture)


class BackendSmokeTests(unittest.TestCase):
    @unittest.skipUnless(
        (ROOT / "services/api").is_dir(),
        "Backend foundation is not present yet; smoke tests activate when services/api exists.",
    )
    def test_backend_package_has_a_health_entrypoint(self) -> None:
        """Provide an actionable failure once Hwaro's backend is scaffolded."""
        import importlib
        import importlib.util

        if importlib.util.find_spec("fastapi") is None:
            self.skipTest("Backend dependencies are not installed; install services/api/requirements.txt.")

        candidates = ("services.api.main", "services.api.app")
        loaded = None
        for module_name in candidates:
            try:
                loaded = importlib.import_module(module_name)
                break
            except ModuleNotFoundError as error:
                if error.name not in candidates:
                    raise
                continue
        self.assertIsNotNone(
            loaded,
            "Expected services.api.main or services.api.app after backend scaffolding.",
        )
        self.assertTrue(
            hasattr(loaded, "app"),
            "Backend entrypoint must expose an ASGI application as `app`.",
        )


if __name__ == "__main__":
    unittest.main()
