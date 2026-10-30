# Hwaro — Lessons

No lessons recorded yet. Initialized 2026-10-29; no work performed.

## 2026-10-30 — W1-HWARO-001

- The local Python 3.13 host's synchronous `TestClient` and direct HTTPX ASGI
  transport hung before returning a response. Direct endpoint-handler tests
  remain runnable and cover transaction behavior; HTTP smoke coverage should be
  repeated in Chengetai's deployment/test environment.
- Validate all sale lines before mutating any product stock so insufficient
  stock leaves the entire attempted sale unchanged.

## 2026-10-30 — W2-HWARO-001

- Readiness must be a repository capability: local mode reports ready without
  an external dependency, while PostgreSQL mode probes the selected database.
- Configuration tests should assert the absence of credentials in local mode
  and reject incomplete PostgreSQL settings before any connection is created.
- A schema starting point is useful only when constraints encode the existing
  contract; preserve shop scope and idempotency in database uniqueness, not only
  in application memory.

## 2026-10-30 — W3-LIVE-TEAM-001A

- The host pytest temp allocator can fail before test setup; using an explicit
  workspace-local basetemp produced a reproducible 12-test run.
- Markdown board tables vary in column count, so activity parsing should split
  cells generically and only consume the stable ID/task/owner columns.
- A local monitor should be content-free and configuration-only: 404 when
  disabled, structured unavailable state for a missing root, and no request
  path input.
