"""Run the repository's dependency-light quality checks."""

from pathlib import Path
import compileall
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    python_roots = [path for path in (ROOT / "services", ROOT / "tests") if path.exists()]
    compile_ok = all(compileall.compile_dir(str(path), quiet=1) for path in python_roots)
    if not compile_ok:
        print("Python bytecode compilation failed.", file=sys.stderr)
        return 1
    print("Quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
