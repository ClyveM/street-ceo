# Chengetai — Decisions

## 2026-10-30 — W1-CHENGETAI-001

- Use Python standard-library `unittest` for the repository baseline so a clean
  checkout can run before dependency installation. Backend-specific pytest
  remains a CI step after installing the backend requirements.
- Keep the smoke import dependency-aware locally: missing FastAPI is reported as
  a skip with the install command, while CI installs dependencies and exercises
  the backend suite.
