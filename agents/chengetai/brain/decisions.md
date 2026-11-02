# Chengetai — Decisions

## 2026-10-30 — W1-CHENGETAI-001

- Use Python standard-library `unittest` for the repository baseline so a clean
  checkout can run before dependency installation. Backend-specific pytest
  remains a CI step after installing the backend requirements.
- Keep the smoke import dependency-aware locally: missing FastAPI is reported as
  a skip with the install command, while CI installs dependencies and exercises
  the backend suite.

## 2026-11-01 — DEMO-APK-SQLITE-QA-001 / SPRINT90-QA-002
- Root-authorized env gate repair permits ignored untracked local configuration without inspecting it, rejects tracked even if ignored and nonignored files, retains template exception and source secret scanning. This reconciles runtime configuration with committed-secret protection; two real-Git regressions verify boundary.
- Demo launcher reuses only matching PID/uvicorn command, ready SQLite backend and database identity. It never stops unknown listeners or changes firewall rules. Optional download service serves exactly one APK and public artifact hash metadata. Real listener inventory denial fails closed; CheckOnly changes nothing.

## 2026-11-02 — REPO-CLEAN-QA-001
Security scan uses Git tracked plus nonignored source paths, retaining trackedignored secret coverage without opening ignored local attachments/config/data. Source manifest requires wrapper/locks/assets and rejects generated/localteam/data. Clean export verification uses its own Git index to prevent accidentally validating the parent checkout. Parent freshexport tests passed; remoteCI remains separate.

