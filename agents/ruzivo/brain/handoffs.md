# Ruzivo — Handoffs

## 2026-10-30 — W1-RUZIVO-001 — Completed

### Assignment summary

Prepared a concise dated MVP accounting policy memo for Verengai, covering sales,
returns, WAC, purchases, cash/bank tender, expenses, owner drawings/injections,
opening balances, daily close, warnings, assumptions, and production/tax questions.

### Files changed

- Added `docs/finance/mvp-accounting-policy-2026-10-30.md`.
- Updated Ruzivo brain records: `current-state.md`, `decisions.md`, and `tasks.md`.
- No code, shared documentation, or another agent's brain was changed.

### Tests and results

- Repository verification on 2026-10-30: PASS. Confirmed the memo exists and contains
  all 10 required policy sections, the internal-advisory disclaimer, and WAC treatment.
- No application tests were run because no finance implementation exists yet.

### Outstanding issues

- Zimbabwe tax/VAT, invoice, settlement, landed-cost, supplier-credit, retention,
  approval, and other production questions are intentionally unresolved and listed
  in the memo.
- Verengai and Dura must implement and expose source-linked ledger/stock movements;
  Ruzivo must review their actual code before approving financially significant work.

### Next-session instructions

- Mutungamiri should review the memo and pass it to Verengai and Dura as the MVP
  accounting baseline.
- On implementation review, verify reversals, tender separation, WAC precision,
  returns, daily close, and visible incomplete-data warnings against code and tests.
