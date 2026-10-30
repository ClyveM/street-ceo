"""Low-cost repository security checks for every CI run."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".venv", "venv", "node_modules", "__pycache__"}
SCANNED_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml"}
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"(?i)\bAKIA[0-9A-Z]{16}\b"),
)


def _candidate_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        yield path


class RepositorySecurityTests(unittest.TestCase):
    def test_env_files_are_not_present(self) -> None:
        forbidden = [
            path.relative_to(ROOT)
            for path in ROOT.rglob(".env*")
            if path.is_file() and path.name not in {".env.example"}
        ]
        self.assertEqual([], forbidden, f"Remove local secret files from the checkout: {forbidden}")

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


if __name__ == "__main__":
    unittest.main()
