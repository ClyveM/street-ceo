# Street CEO — Development Plan (v0, 2026-10-29)

Deadline: November 4, 2026 (Meta Global AI Developer Hackathon).
Rule: functioning end-to-end demo before advanced functionality.

## Current scope — supersedes the historical phase status below (2026-11-01)

Owner froze the connected APK MVP around catalogue, manual and hands-free Apo
sales, stock and sales history. SQLite durability and correlated sanitized Muse
request/response investigation are required. Offline sync, invoice/social demo
work, forecasts and full finance expansion are deferred. Implementation tasks:
DEMO-SQLITE-VOICE-001 (Hwaro), DEMO-APK-APO-001 (Runako),
DEMO-MUSE-TRACE-001 (Ungwaru), DEMO-VOICE-TRACE-001 (Inzwi), and
DEMO-APK-SQLITE-QA-001 (Chengetai). See `demo-mvp-acceptance.md` and
`demo-runbook.md`. Completion requires persisted test evidence and an actual
phone rehearsal; packaging alone does not establish voice acceptance.

## Phase 0 — Setup (in progress)

- Team scaffolding: `AGENTS.md`, 11 roles + brains, docs, master board.
- Owner decisions needed: Git-vs-Sapling, demo shop profile, deploy target.

## Phase 1 — Foundation (proposed order)

1. Backend scaffold + auth + first contracts (Hwaro).
2. CI + test standards (Chengetai).
3. Accounting rules v0 memo (Ruzivo) → ledger design (Verengai).
4. Inventory model + movements (Dura).
5. Meta stack recommendation (Ungwaru).

## Phase 2 — Core slice

1. Record sale end to end: UI (Runako) → API → stock + ledger.
2. Offline queue + sync replay (Fambai + Hwaro).
3. Cash/bank reconciliation + P&L/cashflow reports (Verengai, Ruzivo reviews).
4. Voice sale via Apo/Napo on the same endpoints (Inzwi).

## Phase 3 — Intelligence + hardening

1. Insights: run-out warnings, margin highlights (Chiono + Ungwaru).
2. Dashboard polish + accessibility (Runako).
3. Full e2e suite, security checklist, performance budgets (Chengetai).
4. Demo rehearsal incl. airplane-mode and noisy-voice scenarios.

## Phase 4 — Demo freeze

- Freeze scope; fix only demo-blocking bugs; rehearse; deliver.

Sequencing, task IDs, and assignments are tracked in `tasks/master-board.md`
and issued by Mutungamiri. No phase beyond 0 has started.
