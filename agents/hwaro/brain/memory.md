# Hwaro — Memory

Initialized 2026-10-29. No prior sessions; no work performed yet.

## Project facts (confirmed)

- Street CEO hackathon MVP; deadline November 4, 2026.
- Backend: Python FastAPI + PostgreSQL; auth; migrations.
- No application code exists yet; backend not yet scaffolded.

## Stable context

- Role: `agents/hwaro/role.md`. Activation protocol: `AGENTS.md` section 2.
- Contract-first: every endpoint documented in `docs/api-contracts.md` before
  clients depend on it. Owns schema, auth model, migration safety.
- Server side of Fambai's sync protocol (idempotency, replay, conflicts).

## 2026-10-30 — W2-HWARO-001 verified facts

- `services/api/persistence.py` defines explicit `memory` and `postgres`
  settings, rejects incomplete PostgreSQL configuration, and never silently
  downgrades a selected PostgreSQL backend.
- `services/api/migrations/0001_initial.sql` is additive and encodes shop/SKU
  scope, non-negative stock, sale-line integrity, and scoped idempotency keys.
- Local mode remains credential-free and the W1 API tests continue to pass.
- Live PostgreSQL migration and domain CRUD adapter wiring are not yet verified.

## 2026-10-30 — W3-LIVE-TEAM-001A verified facts

- `GET /api/v1/team/activity` is implemented in `services/api/app.py` and
  `services/api/team_activity.py`.
- `STREET_CEO_REPOSITORY_ROOT` configures the read-only source; team activity
  defaults on for local memory mode and off for PostgreSQL mode.
- The response exposes only structured summaries and timestamps. Disabled mode
  returns 404; a missing configured root returns `available=false` with a safe
  error string.

## 2026-10-30 — W3-VOICE-INPUT-001C verified facts

- `services/api/voice_boundary.py` defines bounded transcript/audio request and
  response models, strict audio size/decode checks, and normalized intent copy.
- `POST /api/v1/shops/{shop_id}/voice/transcript` calls the existing server-side
  Meta Llama interpreter when available; it never calls the sale handler.
- `POST /api/v1/shops/{shop_id}/voice/audio` accepts bounded base64 audio,
  fingerprints it for replay, and reports `audio_transcription_unavailable`
  without persisting bytes.
- `LLAMA_API_KEY` and `LLAMA_MODEL` are read by the server-side adapter only;
  no credentials are part of API request/response models.

## 2026-10-30 — PostgreSQL runtime slice verified facts

- `build_repository(Settings(store_backend="postgres", ...))` selects
  `PostgresRepository`; invalid non-PostgreSQL URLs fail instead of falling
  back to memory.
- Existing shop/product/sale routes delegate to repository methods. PostgreSQL
  sale writes use one transaction and row locks, with idempotency persisted in
  `sales`.
- `GET /readyz` maps repository runtime failures to `503`; schema absence is
  reported as not ready.

## 2026-11-01 — Current approved demo facts
- Updated AGENTS and docs/demo-mvp-acceptance.md supersede historical PostgreSQL/offline plans: connected Android APK, SQLite single-worker API, catalogue/manual+voice sales/stock/history, sanitized investigations. PostgreSQL/offline deferred.
- SQLite aggregate and asset encoding is explicit/versioned, never pickle; operational traces are separate SQLite file. Runtime identity endpoint exposes basename/hash/PID, no full path.
- Voice commit HTTP200 can mean needs_tender with a question, not a sale. Only a durable Sale receipt binds review/commits stock; missing-tender/amount questions must preserve review without posting. PHONE-RECOVERY-API-001 observed this distinction in read-only stored evidence.

## 2026-11-02 — REPO-SHOP-API-001 delivery boundary
DefaultshopAPIdoesnotrequireteam_activity/project_office/local_team modules. Optionalmachine-localapp mounts onlyexplicit STREET_CEO_LOCAL_TEAM_ENABLED=1 and itsfilesremainlocal, excludedfromdelivery. Coreentrypoint services.api.app:app unchanged; tzdata declaredforWindowsHarare. Keepagentbrains/docs tracked; rootcoordinatesGitindex/publication.
