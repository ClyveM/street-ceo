# Chengetai — Lessons

## 2026-10-30 — W1-CHENGETAI-001

- Contract tests must assert the semantics currently documented by the backend,
  not exact wording from the earlier conventions-only document. The check now
  accepts the verified `X-Shop-ID`, validation, idempotency, and audit wording.
- The local environment has Python but no `pytest` or FastAPI; CI must install
  the backend requirements before backend tests can provide full evidence.
