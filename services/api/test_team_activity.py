from pathlib import Path

import pytest
from fastapi import HTTPException

from services.api.app import InMemoryStore, create_app
from services.api.persistence import Settings
from services.api.team_activity import build_team_activity


def test_team_activity_parses_fixture_without_exposing_contents(tmp_path: Path) -> None:
    (tmp_path / "tasks").mkdir()
    (tmp_path / "agents" / "hwaro" / "brain").mkdir(parents=True)
    (tmp_path / "tasks" / "master-board.md").write_text(
        "## In progress\n| ID | Task | Owner | Depends on | Exit condition |\n|----|------|-------|------------|----------------|\n| W3-LIVE-TEAM-001A | Local team activity API | Hwaro | W2 | tests |\n",
        encoding="utf-8",
    )
    (tmp_path / "agents" / "hwaro" / "brain" / "current-state.md").write_text("private prompt must not appear", encoding="utf-8")
    (tmp_path / "agents" / "hwaro" / "brain" / "handoffs.md").write_text("python -m pytest -q — 4 passed in 0.2s", encoding="utf-8")

    snapshot = build_team_activity(tmp_path, enabled=True)

    assert snapshot.available is True
    assert snapshot.tasks[0].id == "W3-LIVE-TEAM-001A"
    assert snapshot.tasks[0].status == "active"
    assert snapshot.agents[0].agent == "hwaro"
    assert snapshot.test_evidence[0].passed == 4
    assert "private prompt" not in snapshot.model_dump_json()


def test_team_activity_reports_unavailable_root(tmp_path: Path) -> None:
    snapshot = build_team_activity(tmp_path / "missing", enabled=True)
    assert snapshot.available is False
    assert snapshot.error == "repository root unavailable"


def test_disabled_route_preserves_production_behavior(tmp_path: Path) -> None:
    app = create_app(InMemoryStore(), Settings(repository_root=tmp_path, team_activity_enabled=False))
    endpoint = next(route.endpoint for route in app.routes if route.path == "/api/v1/team/activity")
    with pytest.raises(HTTPException, match="disabled") as error:
        endpoint()
    assert error.value.status_code == 404
