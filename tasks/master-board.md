# Street CEO — Master Task Board

Updated 2026-10-30. Owner: Mutungamiri. Wave 2 active; persistence and first UI slice are underway.

## In progress

| ID | Task | Owner | Scope | Depends on | Exit condition |
|----|------|-------|-------|------------|----------------|
| W2-HWARO-001 | PostgreSQL persistence adapter | Hwaro | `services/api/` and backend-owned persistence docs | W1-HWARO-001 | Persistence boundary, schema/config, migration-safe repository interface, tests, no behavior regression |
| W2-VERENGAI-001 | MVP ledger and cash movement service | Verengai | `services/finance/` | W1-HWARO-001, W1-RUZIVO-001 | Balanced sale/return/cash/expense/drawing entries and reproducible tests |
| W2-DURA-001 | Inventory movements and weighted-average cost | Dura | `services/inventory/` | W1-HWARO-001, W1-RUZIVO-001 | Receipt, sale, return and adjustment movement rules with cost tests |
| W2-RUNAKO-001 | Mobile-first web shell and manual sale UI | Runako | `apps/web/` excluding offline layer | W1-HWARO-001 | Runnable Today/Sell/Stock shell, manual sale path against API shape, demo branding, responsive preview |
| W2-FAMBAI-001 | Offline queue and sync contract | Fambai | offline layer inside `apps/web/` only | W1-HWARO-001, W2-RUNAKO-001 states | IndexedDB queue, visible sync states, idempotent replay contract, tests |
| W2-INZWI-001 | Apo/Napo voice interaction adapter | Inzwi | `services/voice/` | W1-HWARO-001, W1-UNGWARU-001 | Foreground state machine and provider adapter mapping to sale endpoints, safe fallback tests |
| W3-LIVE-TEAM-001 | Live local team activity feed | Hwaro + Runako | `services/api/` team monitor route and `apps/web/` polling UI | W2 handoffs | Team page polls repository-derived activity; mock fallback is clearly marked only when API unavailable |

## Done

| ID | Task | Owner | Evidence |
|----|------|-------|----------|
| SETUP-001 | Verify workspace + repo config | Mutungamiri | EdenFS/Sapling, no Git, writable, metadata untouched |
| SETUP-002 | Create AGENTS.md | Mutungamiri | `AGENTS.md` |
| SETUP-003 | Create 11 role.md files | Mutungamiri | `agents/*/role.md` |
| SETUP-004 | Create 66 brain files | Mutungamiri | `agents/*/brain/*.md` |
| SETUP-005 | Create shared docs | Mutungamiri | `docs/*.md` (6 files) |
| SETUP-006 | Create master task board | Mutungamiri | `tasks/master-board.md` |
| SETUP-007 | Final verification + report | Mutungamiri | 11/11 OK, 85 files, report to Owner |
| TEST-MEMORY-001 | Runako two-session memory test | Mutungamiri + Runako | PASSED: persisted handoff recovered verbatim by fresh session |
| MIGRATE-001 | Migrate to standard Git repo + worktrees | Mutungamiri | DONE: 85/85 hashes, commit 3c4e244, worktree probe passed |
| W1-RUZIVO-001 | MVP accounting policy memo | Ruzivo | `docs/finance/mvp-accounting-policy-2026-10-30.md`; verified memo and handoff |
| W1-CHENGETAI-001 | Test and quality gate foundation | Chengetai | `tests/run_checks.py`, `infra/security-baseline.md`, `.github/workflows/quality.yml`; 6 passed, 1 intentional skip |
| W1-UNGWARU-001 | Meta/Llama capability spike | Ungwaru | `services/ai/boundary.py`, `services/ai/capability_matrix.py`, `services/ai/test_boundary.py`; 6 tests passed and compilation passed |
| W1-HWARO-001 | Backend foundation and transaction contracts | Hwaro | `services/api/app.py`, `services/api/test_app.py`, `docs/api-contracts.md`; 6 passed, compileall passed, routes verified |

## Backlog — MVP epics (proposed, unscheduled)

| Epic | Candidates | Depends on |
|------|-----------|------------|
| E1 Backend scaffold + auth + contracts | Hwaro, Chengetai (CI) | None (repo ready) |
| E2 Accounting rules v0 + ledger | Ruzivo (policy), Verengai (build) | E1 transaction patterns |
| E3 Inventory model + movements | Dura | E1 |
| E4 Meta stack recommendation | Ungwaru | — (early, gates voice NLU + insights) |
| E5 Web UI shell + sale flow | Runako | E1 contracts |
| E6 Offline queue + sync | Fambai, Hwaro | E1, E5 states |
| E7 Reconciliation + reports | Verengai, Ruzivo (review) | E2 |
| E8 Voice sale (Apo/Napo) | Inzwi, Ungwaru (NLU) | E1 sale endpoint, E4 |
| E9 Insights + forecasts | Chiono, Ungwaru | E2, E3 read contracts |
| E10 Demo hardening + release | Chengetai, all | E1–E9 |

## Owner decisions (2026-10-29)

- Repository: standard Git repo at C:\Users\clyve\source\repos\street-ceo (main); GitHub remote pending separate approval.
- Demo business: Zimbabwean tuckshop selling everyday grocery products.
- Development: local-first; deploy PWA + Python FastAPI backend for the demo.

## Blocked / waiting on Owner

- None. Product defaults used for Wave 1: Zimbabwean tuckshop demo, one shop per account, configured currency/timezone, FastAPI/PostgreSQL, local-first PWA, tender recording without payment settlement, weighted-average cost, and foreground Apo/Napo with touch/text fallback.

## Rules

- Mutungamiri issues task IDs and appends assignments to specialists' `tasks.md`.
- Status changes only with evidence (files, tests, handoff entries).
- No silent brain edits; competing updates reconciled by Mutungamiri.
