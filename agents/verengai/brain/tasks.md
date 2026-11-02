# Verengai — Tasks

No tasks assigned yet. Initialized 2026-10-29.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W2-VERENGAI-001 — MVP ledger and cash movement service — active 2026-10-30

- Scope: `services/finance/` only.
- Read AGENTS.md, this role, all six brain files, `docs/accounting-rules.md`, `docs/finance/mvp-accounting-policy-2026-10-30.md`, `docs/api-contracts.md`, and `tasks/master-board.md`.
- Implement balanced, auditable MVP entries for sale, return, cash/bank tender, expense, owner drawing/injection, opening cash and daily close. Keep source IDs, actor/time, reversal semantics, and completeness warnings explicit. Use deterministic pure functions where possible so tests run without PostgreSQL.
- Do not edit other agent brains or implement inventory/API/UI/voice code. Ruzivo's accounting treatment is authoritative.
- Acceptance: worked demo flow and accounting edge cases have tests; handoff records exact commands/results and open integration points.

### Completion evidence — 2026-10-30

- Implemented `services/finance/ledger.py`, `services/finance/__init__.py`, and `services/finance/test_ledger.py`.
- Finance acceptance tests: `python -m pytest services/finance/test_ledger.py -q` → `5 passed`.
- Compile check: `python -m compileall -q services/finance` → passed.
- Integration check: `python tests/run_checks.py` → `5 passed, 1 error` from the existing backend smoke import context (`ModuleNotFoundError: services`); not modified because it is outside finance ownership.
- Status: implementation complete pending Ruzivo review and cross-agent integration.

## W6-DEMO-FINANCE-001 — 2026-10-31
Explicit assignment received: validate demo finance without frontend work. Review complete, 30 focused tests passed; integration blockers remain. See handoffs.md for commands, source findings, limits and next owners.

### W6 expanded completion — 2026-10-31
51 tests passed; documented reproducible highest-impact day-close opening defect and change/profit evidence in handoffs.md. No application edits; Hwaro correction and Ruzivo review needed.

### W6 finance remediation — 2026-10-31
- Scope honored: `services/finance/` and Verengai brain only.
- Completed: change/tender metadata validation, damaged-return reclassification, duplicate reversal guard, ledger-derived profitability report, and full close movement handling for same-day openings/reversals/source warnings.
- Evidence: `python -m pytest services/finance -q -p no:cacheprovider` → 8 passed; `python -m compileall -q services/finance` → passed; `git diff --check` → passed.
- Remaining: API day-close opening/carry-forward, finance journal integration, persistence, invoice payment linkage, WAC/settlement rounding, and API warning propagation remain Hwaro/Dura/Chengetai integration work; Ruzivo re-review required.
