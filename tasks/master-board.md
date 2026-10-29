# Street CEO — Master Task Board

Updated 2026-10-29. Owner: Mutungamiri. No agents currently active; no code exists.

## In progress

None. Migration plan presented; awaiting Owner approval. Wave 1 queued behind it.

## Pending approval

| ID | Task | Owner | Notes |
|----|------|-------|-------|
| MIGRATE-001 | Migrate to standard Git repo + worktrees | Mutungamiri | Plan + exact commands presented 2026-10-29; awaiting Owner approval |

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

## Backlog — MVP epics (proposed, unscheduled)

| Epic | Candidates | Depends on |
|------|-----------|------------|
| E1 Backend scaffold + auth + contracts | Hwaro, Chengetai (CI) | Owner: Git-vs-Sapling, deploy target |
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

- Repository: standard GitHub repository with Git worktrees (migration pending approval).
- Demo business: Zimbabwean tuckshop selling everyday grocery products.
- Development: local-first; deploy PWA + Python FastAPI backend for the demo.

## Blocked / waiting on Owner

- MIGRATE-001 approval (plan presented below). Wave 1 activation follows the migration.

## Rules

- Mutungamiri issues task IDs and appends assignments to specialists' `tasks.md`.
- Status changes only with evidence (files, tests, handoff entries).
- No silent brain edits; competing updates reconciled by Mutungamiri.
