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

### W3-VOICE-INPUT-001C — Voice transport endpoint — assigned 2026-10-30

- Define a backend-local voice transcript/audio request boundary for the web
  microphone flow. Keep credentials server-side and return bounded status/error
  shapes only.
- Integrate the existing Meta Llama interpreter without allowing model output to
  post a sale directly. Preserve shop scope and idempotency.
- Scope: `services/api/` only, with API contract updates and tests.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W2-HWARO-001 — PostgreSQL persistence adapter — active 2026-10-30

- Scope: `services/api/` and backend-owned persistence documentation only.
- Read the latest W1 handoff, `docs/api-contracts.md`, and Ruzivo's accounting memo before changing persistence.
- Replace the in-memory-only limitation with a clear PostgreSQL-ready repository boundary, environment configuration, schema/migration starting point, and tests. Preserve API behavior and idempotency. Keep local development runnable without credentials through an explicit test store or local mode.
- Do not implement finance, inventory, UI, offline, or voice-owned code.
- Acceptance: persistence boundary explicit, no secrets committed, tests cover replay and shop scope, and handoff states what still requires a live PostgreSQL service.

### W3-LIVE-TEAM-001A — Local team activity API — active 2026-10-30

- Scope: `services/api/` only.
- Add a local-development-only `GET /api/v1/team/activity` route that derives a safe activity snapshot from the configured repository root: master-board task statuses, recent Git commit count, changed-file summaries, agent current-state/handoff timestamps, and available test evidence. Keep the route read-only and never expose secrets, file contents, private prompts, or arbitrary filesystem paths.
- Make the repository root configurable and test with a temporary fixture; return a clear unavailable/error state when the local root is absent. Preserve production behavior when the monitor is disabled.
- Acceptance: response schema is documented, tests cover parsing and unavailable state, and the frontend can poll it without authentication in local mode only.

#### Evidence checkpoint — 2026-10-30

- Added `services/api/persistence.py`, `services/api/migrations/0001_initial.sql`,
  and `services/api/test_persistence.py`.
- Updated `services/api/app.py`, `services/api/requirements.txt`, and
  `docs/api-contracts.md` within backend ownership.
- `python -m pytest services/api -q` — **9 passed**.
- `python -m compileall -q services/api` — **exit 0**.
- No secrets committed. Live PostgreSQL execution remains outstanding.

### W3-LIVE-TEAM-001A evidence — 2026-10-30

- Added `services/api/team_activity.py` and `services/api/test_team_activity.py`.
- Updated `services/api/app.py`, `services/api/persistence.py`, and
  `docs/api-contracts.md` within scope.
- `python -m pytest services/api -q --basetemp .pytest-basetemp` — **12 passed**.
- `python -m compileall -q services/api` — **exit 0**.
- Fixture tests cover board parsing, timestamps/test evidence, safe content
  omission, missing-root unavailable state, and disabled production behavior.

### W3-VOICE-INPUT-001C evidence — 2026-10-30

- Added `services/api/voice_boundary.py`, `services/api/VOICE_API_CONTRACT.md`,
  and `services/api/test_voice_boundary.py`.
- Updated `services/api/app.py` and `services/api/persistence.py` only within
  backend ownership.
- `python -m pytest services/api -q --basetemp .pytest-basetemp` — **18 passed**.
- `python -m compileall -q services/api` — **exit 0**.
- Tests cover bounded transcript intent, confirmation, no sale mutation,
  transcript replay/conflict, audio validation/unavailable response, audio
  replay/conflict, and disabled behavior.

### PostgreSQL runtime priority slice evidence — 2026-10-30

- Expanded `services/api/persistence.py` with transactional PostgreSQL shop,
  product, and sale operations; updated `services/api/app.py` to delegate all
  existing mutating/read routes through the repository boundary.
- Added `services/api/PERSISTENCE_RUNTIME.md` and no-service readiness tests in
  `services/api/test_persistence.py`.
- `python -m pytest services/api -q --basetemp .pytest-basetemp` — **20 passed**.
- `python -m compileall -q services/api` — **exit 0**.
- No PostgreSQL credentials or live service were present; no live migration
  claim is made.
