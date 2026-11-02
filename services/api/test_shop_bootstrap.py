"""Shop startup must not depend on the optional machine-local team app."""
import builtins
import os
import subprocess
import sys
from pathlib import Path

import pytest

from services.api.app import InMemoryStore, create_app
from services.api.persistence import Settings


def test_default_shop_has_no_local_team_routes_or_store():
    app = create_app(InMemoryStore(), Settings(team_activity_enabled=True))
    paths = {route.path for route in app.routes}
    assert "/shops/{shop_id}/sales" in paths
    assert "/api/v1/shops/{shop_id}/voice/transcript" in paths
    assert not any(path.startswith(("/api/v1/team/", "/api/v1/office/")) for path in paths)
    assert not hasattr(app.state, "project_office")


def test_local_team_flag_requires_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("STREET_CEO_LOCAL_TEAM_ENABLED", raising=False)
    monkeypatch.setenv("STREET_CEO_TEAM_ACTIVITY_ENABLED", "1")
    assert Settings.from_env().local_team_enabled is False
    monkeypatch.setenv("STREET_CEO_LOCAL_TEAM_ENABLED", "1")
    assert Settings.from_env().local_team_enabled is True


def test_explicit_missing_local_team_fails_with_clear_configuration_error(monkeypatch):
    original = builtins.__import__
    def unavailable(name, *args, **kwargs):
        if name == "services.api.local_team":
            raise ModuleNotFoundError("local module unavailable", name=name)
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", unavailable)
    with pytest.raises(RuntimeError, match="optional local modules are missing"):
        create_app(InMemoryStore(), Settings(local_team_enabled=True))


def test_fresh_process_shop_sqlite_and_timezone_without_team_dependencies(tmp_path):
    script = r'''
import importlib.abc, json, sys
class NoTeam(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {"services.api.local_team", "services.api.team_activity", "services.api.project_office"}:
            raise ModuleNotFoundError("optional team modules absent", name=fullname)
sys.meta_path.insert(0, NoTeam())
from zoneinfo import ZoneInfo
from services.api.app import create_app
from services.api.persistence import Settings
app = create_app(settings=Settings(store_backend="sqlite", sqlite_path=sys.argv[1], demo_seed_enabled=True))
paths = set(app.openapi()["paths"])
assert "/shops/{shop_id}/sales" in paths
assert "/api/v1/shops/{shop_id}/voice/transcript" in paths
assert not any(path.startswith(("/api/v1/team/", "/api/v1/office/")) for path in paths)
assert not any(name in sys.modules for name in ("services.api.local_team", "services.api.team_activity", "services.api.project_office"))
assert len(app.state.store.shops) == 1
assert ZoneInfo("Africa/Harare").key == "Africa/Harare"
app.state.store.close()
print("shop-only SQLite bootstrap and Harare timezone passed")
'''
    env = {**os.environ, "STREET_CEO_STORE": "memory", "STREET_CEO_SEED_DEMO": "false", "STREET_CEO_LOCAL_TEAM_ENABLED": "0"}
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path / "shop.sqlite3")], cwd=Path(__file__).resolve().parents[2], env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "shop-only SQLite bootstrap" in result.stdout
