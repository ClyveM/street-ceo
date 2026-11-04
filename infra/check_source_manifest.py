"""Audit staged path names only; never read local databases or credentials."""
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    ".env.example", "services/api/demo_catalogue.json", "services/api/requirements.txt",
    "apps/web/package-lock.json", "apps/android/package-lock.json",
    "apps/android/android/gradlew", "apps/android/android/gradlew.bat",
    "apps/android/android/gradle/wrapper/gradle-wrapper.jar",
    "apps/android/android/gradle/wrapper/gradle-wrapper.properties",
    "apps/web/public/street-ceo-logo.png", "infra/dev.py",
    "services/api/demo_product_images/coke-300.png",
    "services/api/demo_product_images/bread-700.png",
    "services/api/demo_product_images/sugar-1kg.png",
    "services/api/demo_product_images/milk-500.png",
    "services/api/demo_product_images/chips-100.png",
    "services/api/demo_product_images/soap-175.png",
}


def forbidden(path):
    if path == "releases/street-ceo-demo-2026-11-04.apk":
        return False
    value = PurePosixPath(path)
    name = value.name.lower()
    parts = value.parts
    return (name.startswith(".env") and name != ".env.example"
            or name.endswith((".log", ".sqlite3", ".sqlite3-wal", ".sqlite3-shm", ".db", ".apk", ".aab", ".jks", ".keystore", ".pem", ".key", ".tsbuildinfo"))
            or name == "local.properties"
            or any(part in {"node_modules", ".venv", "__pycache__", ".gradle", ".codex-remote-attachments", "local-office"} or part.startswith(".pytest-") for part in parts)
            or "build" in parts or "dist" in parts
            or path.startswith("data/")
            or path in {"services/api/local_team.py", "services/api/team_activity.py", "services/api/project_office.py", "services/api/test_team_activity.py", "services/api/test_project_office.py"}
            or path.startswith("apps/android/web-assets/")
            or path.startswith("apps/android/android/app/src/main/assets/public/"))


def main():
    data = subprocess.check_output(["git", "ls-files", "--cached", "-z"], cwd=ROOT)
    paths = set(filter(None, data.decode("utf-8", errors="surrogateescape").split("\0")))
    failures = ["Forbidden staged artifact: " + path for path in sorted(paths) if forbidden(path)]
    failures += ["Missing staged source dependency: " + path for path in sorted(REQUIRED - paths)]
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Staged source manifest passed ({len(paths)} paths; wrapper, locks and shop assets included).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
