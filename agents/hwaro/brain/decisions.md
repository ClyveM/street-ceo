# Hwaro — Decisions

No decisions recorded yet. Initialized 2026-10-29; no work performed.

## 2026-10-30 — W1-HWARO-001

- Use an in-memory repository for the runnable Wave 1 foundation, with a clear
  persistence boundary for PostgreSQL. This keeps the API contract testable
  before database migrations exist.
- Use integer minor units for money and positive whole-unit quantities for the
  packaged-goods MVP.
- Require `X-Shop-ID` to match `{shop_id}` on every shop-scoped route.
- Require `Idempotency-Key` for sales; store a canonical request fingerprint and
  return the original sale on exact replay, rejecting changed payloads.
- Pin FastAPI to `<0.116` in requirements after the newest available release
  blocked the local synchronous/ASGI test transport. This is a verified local
  compatibility constraint, not an API behavior decision.

## 2026-10-30 — W2-HWARO-001

- Keep `memory` as an explicit local/test backend and select PostgreSQL only
  with `STREET_CEO_STORE=postgres` plus `STREET_CEO_DATABASE_URL`; never
  silently downgrade a configured PostgreSQL deployment.
- Use an additive SQL starting point with PostgreSQL-enforced shop/SKU scope,
  non-negative stock, and scoped idempotency uniqueness. Destructive migration
  work remains approval-gated.
- Keep PostgreSQL connection/readiness wiring separate from the W1 endpoint
  handler contract until the full domain repository adapter is implemented.

## 2026-10-30 — W3-LIVE-TEAM-001A

- Enable team activity by default only for the credential-free local memory
  mode; PostgreSQL mode defaults it off unless explicitly enabled. Disabled
  production requests return `404`.
- Accept repository root only through server configuration, never through a
  request parameter. Summaries are allowlisted and content-free; private path
  markers and unsafe relative paths are omitted.
- Use a bounded recent Git count (20 commits) and numeric test evidence parsed
  from handoff records rather than exposing raw repository documents.

## 2026-10-30 — W3-VOICE-INPUT-001C

- Split browser voice input into transcript and audio endpoints. Both are
  shop-scoped and require an idempotency key; neither endpoint has permission
  to create a sale.
- Normalize provider output into a small API-owned intent model and force
  `needs_confirmation=true` for every response. Provider failures collapse to
  bounded error codes; raw model output and credentials never cross the API.
- Keep audio intake JSON/base64 and bounded to 5 MiB until the voice-owned
  speech-to-text adapter selects a provider. Do not store audio in the API.

## 2026-10-30 — PostgreSQL runtime slice

- Preserve the existing API record view as a per-request compatibility object,
  but make PostgreSQL repository methods the source of truth when
  `STREET_CEO_STORE=postgres`.
- Use database uniqueness plus a transaction/row locks for sale idempotency
  and stock safety. Repository/database failures surface as safe `503` errors;
  no memory fallback is permitted.
- Readiness checks both connectivity and the presence of the migrated
  `public.shops` table so an unmigrated deployment cannot appear ready.
