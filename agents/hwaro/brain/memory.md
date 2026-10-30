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
