# Street CEO — API Contracts (v0, 2026-10-29)

Status: conventions only. No endpoints implemented; no code exists yet.
Owner in practice: Hwaro, with Mutungamiri.

## Conventions (binding once endpoints are added)

- Base path, versioning, and error envelope to be fixed at backend scaffolding.
- Every endpoint documented here BEFORE any client (UI, offline sync, voice,
  AI) depends on it.
- Every mutating endpoint: authentication, per-shop authorization, request
  validation, and tests.
- Money and stock writes: auditable (actor, timestamp, source); reversible
  through proper reversals.
- Sync endpoints: idempotency keys, replay ordering, deterministic conflict
  responses (agreed with Fambai).

## Planned resource areas (names not final)

- Auth: login, session, per-shop scope.
- Sales: create sale (idempotent), void/reversal, list.
- Inventory: products, purchases, receiving, adjustments, counts, stock levels.
- Finance: payments, expenses, reconciliations, P&L, cashflow reports.
- Sync: offline queue replay, conflict fetch/resolve.
- AI: insight requests with structured responses.

## Change rule

Contract changes require updating this file first, then affected clients in
dependency order, sequenced by Mutungamiri. Breaking changes need Owner
awareness before the demo freeze.
