# Street CEO — Product Requirements (v0, 2026-10-29)

Status: draft scope for the hackathon MVP. Deadline: November 4, 2026.

## Users

Street vendors and micro-retailers, primarily on low-cost Android phones,
often with intermittent connectivity and noisy surroundings.

## MVP scope (must demo end to end)

1. Record a sale (UI, offline-capable, and voice via Apo/Napo).
2. Track stock: catalog, purchases, sales decrementing, adjustments, counts.
3. Cash and bank reconciliation usable by non-accountants.
4. Financial reporting: sales, profit and loss, cashflow.
5. Meta-powered business insights (e.g. run-out warnings, margin highlights).
6. Works offline for core flows; syncs on reconnect without data loss.

## Non-goals for the MVP

- Native Android/iOS apps (PWA only).
- Multi-branch, payroll, statutory tax filing.
- Open-ended voice dictation (short commands only).

## Demo bar

A vendor greeting ("Apo"), recording a sale by voice ("Napo"), seeing stock
and cash update, going offline and selling again, reconnecting with clean
reconciliation, and receiving one credible business insight.

## Open questions for the Owner

- Shop profile for demo data (single vendor, product list, currency).
- Deployment target for the demo (local, hosted backend, on-device only).
- Git-vs-Sapling direction for branching and worktrees.
