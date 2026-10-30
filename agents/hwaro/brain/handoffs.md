# Hwaro — Handoffs

No handoffs recorded yet. Initialized 2026-10-29; no work performed.

## 2026-10-30 — Handoff: W1-HWARO-001

### Assignment summary

Built the minimal FastAPI foundation with health/readiness, shop/product/sale
schemas, deterministic validation, shop scope, idempotent sales, and no silent
negative stock.

### Files changed

- `services/api/__init__.py`
- `services/api/app.py`
- `services/api/requirements.txt`
- `services/api/test_app.py`
- `docs/api-contracts.md`

### Tests and results

- `python -m pytest services/api/test_app.py -q` — **6 passed in 0.58s**.
- `python -m compileall -q services/api` — **exit 0**.
- Import route check confirmed `/healthz`, `/readyz`, shop, product, and sale
  routes are registered.

### Outstanding issues

- Current host's TestClient/HTTPX ASGI request path hangs before returning;
  tests cover actual endpoint handlers and store transactions directly. Run an
  HTTP-level smoke test in Chengetai's environment.
- Repository is in-memory until PostgreSQL schema/migrations are assigned.

### Next-session instructions

Chengetai should run HTTP-level and security checks. Dura/Verengai/Fambai can
consume the documented contracts; any breaking changes must update
`docs/api-contracts.md` first and preserve idempotency and atomic stock rules.

## 2026-10-30 — Handoff: W2-HWARO-001

### Assignment summary

Replaced the documented in-memory-only limitation with an explicit persistence
configuration/repository boundary, PostgreSQL readiness adapter, additive
schema/migration starting point, and regression tests while preserving the W1
local API behavior.

### Files changed

- `services/api/persistence.py`
- `services/api/migrations/0001_initial.sql`
- `services/api/test_persistence.py`
- `services/api/app.py`
- `services/api/requirements.txt`
- `docs/api-contracts.md`

### Tests and results

- `python -m pytest services/api -q` — **9 passed**.
- `python -m compileall -q services/api` — **exit 0**.
- Existing replay, changed-payload rejection, shop scope representation, and
  no-negative-stock tests remain passing.

### Outstanding issues

- No live PostgreSQL instance or credentials were available, so migration
  application and real connection readiness were not run.
- The adapter currently owns configuration/connection/readiness and schema
  boundary; full domain CRUD wiring is the next backend slice. It must not
  silently fall back to memory.

### Next-session instructions

Chengetai should run the HTTP-level smoke/security checks and a live PostgreSQL
startup/migration check. Hwaro should then wire CRUD and transactional sale
operations through the repository seam, preserving the documented W1 contract.

## 2026-10-30 — Handoff: W3-LIVE-TEAM-001A

### Assignment summary

Added the local-development-only Team activity API route. It reads a configured
repository root and returns safe structured summaries for the Team page: board
statuses, bounded recent Git activity, changed-file summaries, agent brain-file
timestamps, and numeric test evidence.

### Files changed

- `services/api/team_activity.py`
- `services/api/test_team_activity.py`
- `services/api/app.py`
- `services/api/persistence.py`
- `docs/api-contracts.md`

### Tests and results

- `python -m pytest services/api -q --basetemp .pytest-basetemp` — **12 passed**.
- `python -m compileall -q services/api` — **exit 0**.
- `git diff --check` — no whitespace errors.

### Safety and behavior

- No request-supplied paths, file contents, private prompts, secrets, or
  credentials are returned.
- Local memory mode enables the monitor by default; PostgreSQL mode disables it
  by default. Disabled requests return `404`.
- Missing configured roots return a structured unavailable response.

### Outstanding issues

- The default pytest temp allocator failed before setup on this host; the
  repository-local basetemp run passed all 12 tests.
- HTTP-level smoke testing remains for Chengetai because of the existing host
  ASGI transport limitation.

### Next-session instructions

Run the API in local mode with `STREET_CEO_REPOSITORY_ROOT` pointed at the
workspace and have Runako poll `/api/v1/team/activity`. Keep any UI fallback
clearly labeled when the endpoint is disabled or unavailable.
