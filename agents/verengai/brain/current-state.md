# Verengai — Current State

Updated 2026-10-30 after W2-VERENGAI-001 implementation.

## Status

W2-VERENGAI-001 implemented within the permitted `services/finance/` scope. Ready for Ruzivo functional review and Hwaro integration.

## Work in progress

- Finance journal and deterministic tests are complete.

## Latest verified results

- `python -m pytest services/finance/test_ledger.py -q`: 5 passed.
- `python -m compileall -q services/finance`: passed.
- `python tests/run_checks.py`: 5 passed, 1 pre-existing backend import error (`ModuleNotFoundError: services`) in the repository contract smoke test.
- Full `python -m pytest -q` collection also encounters unrelated AI/voice imports that use local-module imports (`boundary`, `state_machine`).

## Known blockers

- Hwaro must map these append-only entries and Decimal values into PostgreSQL transaction boundaries without changing posting semantics.
- Dura must supply weighted-average COGS and stock movement source references to sale/return calls.
- Ruzivo review remains required before release; this implementation is operational MVP accounting, not statutory accounting.

## Next immediate action

Next: hand off exact finance interfaces and integration points to Mutungamiri/Hwaro/Dura; address repository-wide import-path failures in owner scopes.

## 2026-10-31 — W6-DEMO-FINANCE-001
Review complete: 30 focused tests passed freshly. Finance integration blockers and exact commands recorded in handoffs.md. No live or PostgreSQL validation performed. Await Mutungamiri sequencing of API/persistence fixes and Ruzivo policy review; no application files changed.

### W6 expanded checkpoint — 2026-10-31
51 fresh tests passed (47 finance/inventory/API/voice + 4 Muse). Same-day 2000-cent opening ignored by close preview reproduced in isolated in-memory route probe. Cash change 200 received/150 due/50 change verified by passing test; profit 100 cents before and 75 after confirmed expense verified. API fix belongs to Hwaro; see handoffs.md for exact evidence and remaining rounding/period/carry-forward issues.

### W6 finance remediation checkpoint — 2026-10-31
Implemented the finance-owned remediation in `services/finance/`: sale posting now validates and records cash received/change metadata without inflating tender; bank tender cannot carry change; damaged returns reclassify original COGS to stock loss without a second inventory reduction; duplicate and reversal-of-reversal attempts are rejected; profitability is reproduced from journal postings and returns `None` for profit when COGS is missing; daily close includes same-day opening balances, reversal movements, and source warnings. Fresh `python -m pytest services/finance -q -p no:cacheprovider` passed 8 tests; compileall and `git diff --check` passed. API integration/persistence blockers remain with Hwaro.
