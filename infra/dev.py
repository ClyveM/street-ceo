"""Small cross-platform setup and foreground launch commands; no secret copies."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(arguments, cwd=ROOT, env=None):
    subprocess.run([str(value) for value in arguments], cwd=cwd, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "setup", "api", "web"])
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 or newer is required")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if args.command in {"check", "setup", "web"} and not npm:
        parser.error("Install Node.js 22 or newer with npm, then retry")
    if args.command == "check":
        run(["node", "--version"])
        run([npm, "--version"])
        print(f"Python {sys.version.split()[0]}; repository {ROOT}")
        print("Prerequisites found. Run: python infra/dev.py setup")
    elif args.command == "setup":
        if not PYTHON.is_file():
            venv.create(ROOT / ".venv", with_pip=True)
        run([PYTHON, "-m", "pip", "install", "-r", "services/api/requirements.txt"])
        run([npm, "ci", "--no-audit", "--no-fund"], ROOT / "apps/web")
        print("Setup complete. In separate terminals: python infra/dev.py api | python infra/dev.py web")
    elif args.command == "api":
        if not PYTHON.is_file():
            parser.error("Run python infra/dev.py setup first")
        environment = os.environ.copy()
        environment.setdefault("STREET_CEO_STORE", "sqlite")
        environment.setdefault("STREET_CEO_SQLITE_PATH", str(ROOT / "data/demo-mvp.sqlite3"))
        environment.setdefault("STREET_CEO_TRACE_DATABASE", str(ROOT / "data/muse-traces.sqlite3"))
        environment.setdefault("STREET_CEO_LOCAL_TEAM_ENABLED", "0")
        environment.setdefault("STREET_CEO_SEED_DEMO", "1")
        environment.setdefault("STREET_CEO_VOICE_ENABLED", "1")
        environment.setdefault("STREET_CEO_CONSOLE_TRACE", "detail")
        run([PYTHON, "-m", "uvicorn", "services.api.app:app", "--host", "127.0.0.1", "--port", "8001", "--workers", "1"], env=environment)
    else:
        environment = os.environ.copy()
        environment.setdefault("VITE_API_BASE_URL", "http://127.0.0.1:8001")
        environment.setdefault("VITE_SHOP_ID", "00000000-0000-0000-0000-000000000001")
        run([npm, "run", "dev", "--", "--host", "127.0.0.1"], ROOT / "apps/web", env=environment)


if __name__ == "__main__":
    main()
