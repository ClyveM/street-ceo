"""Foreground commands use project defaults while preserving explicit overrides."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from infra import dev


class BootstrapTests(unittest.TestCase):
    def invoke(self, command, environment):
        with patch.object(sys, "argv", ["dev.py", command]), patch.object(dev, "PYTHON", Path(sys.executable)), patch.object(dev.shutil, "which", return_value="npm"), patch.dict(dev.os.environ, environment, clear=True), patch.object(dev, "run") as run:
            dev.main()
            return run.call_args

    def test_fresh_web_points_at_local_demo_and_explicit_connection_is_preserved(self):
        call = self.invoke("web", {})
        self.assertEqual("http://127.0.0.1:8001", call.kwargs["env"]["VITE_API_BASE_URL"])
        self.assertEqual("00000000-0000-0000-0000-000000000001", call.kwargs["env"]["VITE_SHOP_ID"])
        call = self.invoke("web", {"VITE_API_BASE_URL": "http://example.test", "VITE_SHOP_ID": "custom"})
        self.assertEqual("http://example.test", call.kwargs["env"]["VITE_API_BASE_URL"])
        self.assertEqual("custom", call.kwargs["env"]["VITE_SHOP_ID"])

    def test_api_uses_one_local_worker_and_project_paths_without_overwriting_config(self):
        call = self.invoke("api", {})
        self.assertIn("127.0.0.1", call.args[0])
        self.assertEqual("1", call.args[0][-1])
        self.assertEqual(str(dev.ROOT / "data/demo-mvp.sqlite3"), call.kwargs["env"]["STREET_CEO_SQLITE_PATH"])
        self.assertEqual(str(dev.ROOT / "data/muse-traces.sqlite3"), call.kwargs["env"]["STREET_CEO_TRACE_DATABASE"])
        self.assertEqual("0", call.kwargs["env"]["STREET_CEO_LOCAL_TEAM_ENABLED"])
        call = self.invoke("api", {"STREET_CEO_STORE": "memory", "STREET_CEO_SEED_DEMO": "0"})
        self.assertEqual("memory", call.kwargs["env"]["STREET_CEO_STORE"])
        self.assertEqual("0", call.kwargs["env"]["STREET_CEO_SEED_DEMO"])
