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
