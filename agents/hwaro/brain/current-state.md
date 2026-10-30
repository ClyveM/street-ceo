# Hwaro — Current State

Updated 2026-10-30 after W1-HWARO-001.

## Status

W1-HWARO-001 implementation complete within the assigned backend/API scope.

## Work in progress

- FastAPI app, schemas, shop-scoped product/sale handlers, and in-memory
  repository are implemented under `services/api/`.
- API contract is documented in `docs/api-contracts.md`.

## Latest verified results

- `python -m pytest services/api/test_app.py -q`: 6 passed in 0.58s.
- `python -m compileall -q services/api`: exit 0.
- App route registration verified by importing `services.api.app`.

## Known blockers

- HTTP client transport in this host blocked/hung before response; acceptance
  tests therefore exercise the actual endpoint handlers and store boundary
  directly. A normal deployed HTTP smoke test remains for Chengetai.

## W2-HWARO-001 checkpoint — 2026-10-30

- Added `services/api/persistence.py` with explicit `memory`/`postgres` settings,
  a repository readiness seam, and a PostgreSQL adapter connection boundary.
- Added additive schema starting point at
  `services/api/migrations/0001_initial.sql` with shop scope, product SKU
  uniqueness, non-negative stock, sale lines, and scoped idempotency keys.
- Updated API contract documentation and kept local mode credential-free.
- Verified `python -m pytest services/api -q`: 9 passed.
- Verified `python -m compileall -q services/api`: exit 0.

## Known W2 limitations

- No live PostgreSQL service or credentials were available; connection probing
  and migration execution remain for Chengetai/deployment verification.
- The W2 adapter currently establishes the PostgreSQL boundary and readiness
  check; domain CRUD wiring remains a follow-up slice and must not silently
  fall back to memory.

## Next immediate action

Chengetai should run HTTP-level smoke/security checks and a live PostgreSQL
migration/readiness check before production wiring. The next Hwaro slice should
wire domain CRUD through the repository protocol while preserving W1 replay,
shop scope, and atomic stock behavior.

## W3-LIVE-TEAM-001A checkpoint — 2026-10-30

- Added local-only `GET /api/v1/team/activity` with configurable repository
  root and production-safe disabled behavior.
- Snapshot derives task statuses, recent Git commit count, safe changed-file
  summaries, agent brain timestamps, and numeric test evidence without exposing
  file contents, secrets, prompts, or arbitrary request paths.
- Verified `python -m pytest services/api -q --basetemp .pytest-basetemp`:
  12 passed.
- Verified `python -m compileall -q services/api`: exit 0.

## W3 known limitations

- This host's default pytest temporary allocator failed before fixture setup;
  the same suite passed using the repository-local `.pytest-basetemp` base.
- No HTTP transport smoke test was added because the existing host limitation
  affects synchronous ASGI transport; route handler and fixture coverage pass.

## W3-VOICE-INPUT-001C checkpoint — 2026-10-30

- Added backend-local transcript and audio request boundaries under
  `services/api/` with shop scope and required `Idempotency-Key` handling.
- Transcript requests use the existing server-side Meta Llama interpreter when
  configured, return only normalized bounded intent/status data, and never post
  a sale. Audio requests validate/fingerprint bounded base64 bytes and return a
  safe unavailable status until STT is supplied.
- Verified `python -m pytest services/api -q --basetemp .pytest-basetemp`:
  18 passed.
- Verified `python -m compileall -q services/api`: exit 0.

## W3 voice limitations

- No Meta credentials or live provider request were used; provider-unavailable
  behavior is tested through the injected/no-credential path.
- Audio transcription remains the Inzwi-owned provider boundary; the backend
  accepts and fingerprints audio without storing it or posting a sale.
- HTTP-level smoke testing remains for Chengetai because of the existing host
  ASGI transport limitation.
