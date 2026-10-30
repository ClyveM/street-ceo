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
