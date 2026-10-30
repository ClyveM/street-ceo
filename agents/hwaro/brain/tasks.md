# Hwaro — Tasks

## Assigned by Mutungamiri

### W1-HWARO-001 — Backend foundation and transaction contracts — complete 2026-10-30

- Scope: `services/api/` only, plus backend-owned updates to `docs/api-contracts.md` when needed.
- Read `AGENTS.md`, this role, all six brain files, `docs/architecture.md`, `docs/api-contracts.md`, `docs/product-requirements.md`, and `tasks/master-board.md` before coding.
- Build a minimal FastAPI foundation with health/readiness, shop/product/sale domain schemas, deterministic validation, and an idempotent sale boundary suitable for UI, offline, and voice callers.
- Do not implement frontend, offline, voice, AI, finance, or inventory-owned code. Coordinate contract assumptions through the shared API contract file and handoff.
- Acceptance: runnable app/test entry point; tenant/shop scope represented; sale retry returns the original result for the same key and rejects a changed payload; no silent negative stock; tests recorded in handoff.
- Before completion update only this agent's relevant brain files and write a structured handoff. No fabricated test results.

Evidence: `services/api/app.py`, `services/api/test_app.py`,
`services/api/requirements.txt`, and `docs/api-contracts.md`; six tests passed
and compileall completed successfully on 2026-10-30. HTTP transport limitation
is recorded in `current-state.md` and `lessons.md`.

No tasks assigned yet. Initialized 2026-10-29.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.
