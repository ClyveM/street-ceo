"""Low-cost repository security checks for every CI run."""

from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".venv", "venv", "node_modules", "__pycache__"}
SCANNED_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml"}
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"(?i)\bAKIA[0-9A-Z]{16}\b"),
)


def _candidate_files(root: Path = ROOT):
    # Scan tracked source even if ignored, plus nonignored additions. Never
    # open local-only attachments, generated databases or ignored configuration.
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, capture_output=True, check=True,
    )
    for relative in set(result.stdout.decode("utf-8", errors="surrogateescape").split("\0")):
        if not relative:
            continue
        path = root / relative
        if path.is_file() and path.suffix.lower() in SCANNED_SUFFIXES:
            yield path
def _unprotected_env_files(root: Path = ROOT) -> list[str]:
    """Reject tracked or nonignored config; never inspect credential contents.

    Git's combined view includes tracked files even when an ignore rule matches.
    Ignored, untracked local runtime configuration is deliberately not included.
    """
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, capture_output=True, check=True,
    )
    paths = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    return sorted({path for path in paths if path and Path(path).name.startswith(".env")
                   and Path(path).name != ".env.example"})


class RepositorySecurityTests(unittest.TestCase):
    def test_env_files_are_not_tracked_or_exposed(self) -> None:
        forbidden = _unprotected_env_files()
        self.assertEqual([], forbidden, f"Environment files must be untracked and ignored: {forbidden}")

    def test_no_literal_secrets_in_source_like_files(self) -> None:
        findings = []
        for path in _candidate_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                findings.append(str(path.relative_to(ROOT)))
        self.assertEqual(
            [],
            findings,
            "Possible hard-coded secret found; use environment/configured secret storage: "
            + ", ".join(findings),
        )


class EnvironmentPolicyRegressionTests(unittest.TestCase):
    def test_source_scan_skips_ignored_local_files_but_keeps_tracked_ignored_source(self):
        with tempfile.TemporaryDirectory(prefix="street-ceo-source-policy-") as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            (root / ".gitignore").write_text("private/\ntracked.py\n", encoding="utf-8")
            (root / "private").mkdir()
            (root / "private" / "attachment.json").touch()
            (root / "tracked.py").touch()
            (root / "new.py").touch()
            subprocess.run(["git", "add", "-f", "tracked.py"], cwd=root, check=True, capture_output=True)
            self.assertEqual({"tracked.py", "new.py"}, {str(path.relative_to(root)) for path in _candidate_files(root)})

    def test_ignored_local_config_is_allowed_but_tracked_config_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="street-ceo-env-policy-") as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            (root / ".gitignore").write_text(".env\n.env.*\n", encoding="utf-8")
            (root / ".env").touch()
            self.assertEqual([], _unprotected_env_files(root))
            subprocess.run(["git", "add", "-f", ".env"], cwd=root, check=True, capture_output=True)
            self.assertEqual([".env"], _unprotected_env_files(root))

    def test_nonignored_nested_config_is_rejected_and_example_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="street-ceo-env-policy-") as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            (root / "nested").mkdir()
            (root / "nested" / ".env.local").touch()
            (root / ".env.example").touch()
            self.assertEqual(["nested/.env.local"], _unprotected_env_files(root))


if __name__ == "__main__":
    unittest.main()
