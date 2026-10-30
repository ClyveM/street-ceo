"""Safe, read-only local repository activity snapshot for the Team page."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field


class TeamActivityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TeamTask(TeamActivityModel):
    id: str
    task: str
    owner: str
    status: str


class ChangedFile(TeamActivityModel):
    path: str
    status: str


class CommitSummary(TeamActivityModel):
    count: int = Field(ge=0)
    latest_hash: str | None = None
    latest_subject: str | None = None


class AgentActivity(TeamActivityModel):
    agent: str
    current_state_at: datetime | None = None
    handoff_at: datetime | None = None
    last_activity_at: datetime | None = None


class TestEvidence(TeamActivityModel):
    agent: str
    passed: int = Field(ge=0)
    source: str
    observed_at: datetime


class TeamActivity(TeamActivityModel):
    enabled: bool
    available: bool
    generated_at: datetime
    tasks: list[TeamTask] = Field(default_factory=list)
    commits: CommitSummary = Field(default_factory=lambda: CommitSummary(count=0))
    changed_files: list[ChangedFile] = Field(default_factory=list)
    agents: list[AgentActivity] = Field(default_factory=list)
    test_evidence: list[TestEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


_TEST_RESULT = re.compile(r"(?P<count>\d+)\s+passed(?:\s+in\s+(?P<duration>[0-9.]+)s)?", re.IGNORECASE)
_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")
_PRIVATE_MARKERS = {".aws", ".codex", ".git", ".env", "prompt", "secret", "credential", "token", "key"}


def _utc_timestamp(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _safe_relative_path(value: str) -> str | None:
    normalized = value.replace("\\", "/").strip()
    if not normalized or normalized.startswith(("/", "../")) or "/../" in f"/{normalized}/":
        return None
    parts = normalized.split("/")
    lowered = {part.lower() for part in parts}
    if lowered & _PRIVATE_MARKERS or any("secret" in part.lower() or "credential" in part.lower() for part in parts):
        return None
    if not all(_SAFE_COMPONENT.match(part) for part in parts):
        return None
    return "/".join(parts)


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )


def _git_snapshot(root: Path) -> tuple[CommitSummary, list[ChangedFile], list[str]]:
    warnings: list[str] = []
    try:
        count_result = _run_git(root, "rev-list", "--count", "--max-count=20", "HEAD")
        latest_result = _run_git(root, "log", "-1", "--format=%h%x09%s")
        status_result = _run_git(root, "status", "--short", "--untracked-files=all")
    except (OSError, subprocess.TimeoutExpired):
        return CommitSummary(count=0), [], ["git activity unavailable"]

    if count_result.returncode != 0:
        return CommitSummary(count=0), [], ["git activity unavailable"]
    try:
        count = int(count_result.stdout.strip() or "0")
    except ValueError:
        count = 0
        warnings.append("git commit count unavailable")

    latest_hash: str | None = None
    latest_subject: str | None = None
    latest = latest_result.stdout.strip().split("\t", 1)
    if latest_result.returncode == 0 and len(latest) == 2:
        latest_hash = latest[0][:12]
        latest_subject = " ".join(latest[1].split())[:160]

    changed: list[ChangedFile] = []
    for line in status_result.stdout.splitlines()[:100]:
        if len(line) < 4:
            continue
        status = line[:2].strip() or "changed"
        path = line[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[-1]
        safe_path = _safe_relative_path(path)
        if safe_path:
            changed.append(ChangedFile(path=safe_path, status=status))
    if status_result.returncode != 0:
        warnings.append("changed-file summary unavailable")
    return CommitSummary(count=count, latest_hash=latest_hash, latest_subject=latest_subject), changed, warnings


def _parse_tasks(root: Path) -> list[TeamTask]:
    board = root / "tasks" / "master-board.md"
    if not board.is_file():
        return []
    tasks: list[TeamTask] = []
    status = "unknown"
    for line in board.read_text(encoding="utf-8", errors="replace").splitlines():
        heading = line.lower()
        if heading.startswith("## in progress"):
            status = "active"
        elif heading.startswith("## done"):
            status = "done"
        elif heading.startswith("## "):
            status = "unknown"
        if not line.strip().startswith("|"):
            continue
        cells = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in {"id", "epic"}:
            continue
        task_id, task, owner = cells[:3]
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9-]{3,64}", task_id):
            continue
        tasks.append(TeamTask(id=task_id, task=task[:160], owner=owner[:80], status=status))
    return tasks


def _agent_snapshot(root: Path) -> tuple[list[AgentActivity], list[TestEvidence]]:
    agents_root = root / "agents"
    agents: list[AgentActivity] = []
    evidence: list[TestEvidence] = []
    if not agents_root.is_dir():
        return agents, evidence
    for agent_dir in sorted(agents_root.iterdir(), key=lambda item: item.name):
        if not agent_dir.is_dir() or not _SAFE_COMPONENT.match(agent_dir.name):
            continue
        brain = agent_dir / "brain"
        current = brain / "current-state.md"
        handoffs = brain / "handoffs.md"
        current_at = _utc_timestamp(current) if current.is_file() else None
        handoff_at = _utc_timestamp(handoffs) if handoffs.is_file() else None
        last = max((stamp for stamp in (current_at, handoff_at) if stamp), default=None)
        if current_at or handoff_at:
            agents.append(AgentActivity(agent=agent_dir.name, current_state_at=current_at, handoff_at=handoff_at, last_activity_at=last))
        if handoffs.is_file():
            text = handoffs.read_text(encoding="utf-8", errors="replace")
            matches = _TEST_RESULT.findall(text)
            if matches:
                passed = sum(int(match[0]) for match in matches)
                evidence.append(TestEvidence(agent=agent_dir.name, passed=passed, source=f"agents/{agent_dir.name}/brain/handoffs.md", observed_at=handoff_at or _utc_timestamp(handoffs)))
    return agents, evidence


def build_team_activity(root: Path, enabled: bool) -> TeamActivity:
    generated_at = datetime.now(timezone.utc)
    if not enabled:
        return TeamActivity(enabled=False, available=False, generated_at=generated_at, error="team activity is disabled")
    if not root.is_dir():
        return TeamActivity(enabled=True, available=False, generated_at=generated_at, error="repository root unavailable")
    try:
        tasks = _parse_tasks(root)
        commits, changed, warnings = _git_snapshot(root)
        agents, evidence = _agent_snapshot(root)
    except (OSError, UnicodeError):
        return TeamActivity(enabled=True, available=False, generated_at=generated_at, error="repository activity unavailable")
    return TeamActivity(
        enabled=True,
        available=True,
        generated_at=generated_at,
        tasks=tasks,
        commits=commits,
        changed_files=changed,
        agents=agents,
        test_evidence=evidence,
        warnings=warnings,
    )
