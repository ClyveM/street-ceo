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

## 2026-10-30 — W3-VOICE-INPUT-001C

- FastAPI dependency functions must be defined before route decorators execute;
  adding routes earlier in `create_app` caused import-time failure and was
  caught by the focused suite.
- Keep provider integration lazy and injectable: local tests stay credential-
  free, while production reads Meta settings only inside the server process.
- Idempotency applies to interpretation requests too: replay the bounded
  response for an exact payload and reject changed payloads with `409`.

## 2026-10-30 — PostgreSQL runtime slice

- Keeping API-facing record objects while refreshing them from PostgreSQL makes
  the migration incremental, but every mutating route must delegate explicitly
  or it will accidentally mutate only a cache.
- `FOR UPDATE` must cover every product row before any sale stock check; the
  transaction then keeps validation and decrement atomic under concurrent sales.
- Readiness should check the migration marker/table as well as `SELECT 1`; a
  reachable but uninitialized database is not ready for traffic.

## 2026-10-31 — W6-DEMO-BACKEND-001

- Transaction idempotency alone is insufficient for one reviewed voice basket: a different request key bypassed replay and created another sale. Bind the review to its successful key/receipt, and replay before re-reading mutable catalogue prices. This process-local fix does not establish multi-worker or restart safety.

## 2026-10-31 — W6-PERSISTENCE-COGS-001

- A database column alone does not make a financial value durable: the
  PostgreSQL sale path had `sales.cogs_micros` in the schema but neither read
  product cost during the locked sale transaction nor selected COGS during
  reload. Test both write parameters and reconstruction.
- LAN route audits should compare OpenAPI paths with the actual client
  contract; sales intentionally remains the legacy `/shops/.../sales` path
  while newer operational routes use `/api/v1/...`.

2026-10-31 W6-APK-VOICE-CORS-001: health GET from native shell does not prove WebView POST works; test CORS preflight with exact bundled origin and custom headers. localhost:5173 differs from Capacitor http://localhost.
