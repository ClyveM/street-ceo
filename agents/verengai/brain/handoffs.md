# Verengai — Handoffs

## Handoff — W2-VERENGAI-001 — 2026-10-30

### Assignment summary

Implemented balanced, auditable MVP finance entries within `services/finance/` under Ruzivo's 2026-10-30 policy memo.

### Files changed

- `services/finance/__init__.py`: public finance exports.
- `services/finance/ledger.py`: Decimal double-entry ledger, source/actor/time metadata, sale/return/purchase/expense/owner/opening postings, warnings, reversals, and locked daily close.
- `services/finance/test_ledger.py`: five deterministic tests for the worked demo, account separation, return warnings, exact reversals, and close variance.

### Tests and results

- `python -m pytest services/finance/test_ledger.py -q` — PASS, 5 passed.
- `python -m compileall -q services/finance` — PASS.
- `python tests/run_checks.py` — 5 passed, 1 error in the existing backend smoke test because `services` cannot be imported from that runner context.
- `python -m pytest -q` — finance tests pass, but collection has unrelated existing AI/voice local-import errors (`boundary`, `state_machine`).

### Integration instructions

- Hwaro should persist `JournalEntry` and `DailyClose` append-only, preserve Decimal precision, source IDs, event/record timestamps, and `reversal_of` links.
- Dura should pass the pre-sale WAC-derived COGS and stock movement source into `Ledger.sale`; returns should pass original sale ID, original COGS, quantity, and resalable status.
- API/UI should surface `warnings` and daily-close variances; do not auto-post corrections or hide missing evidence.
- Account `balance()` uses debit-minus-credit; credit-normal income/equity/liability balances are negative.

### Outstanding issues

- Ruzivo functional review is still required.
- Repository-wide import-path failures remain with the owning agents; no non-finance files were changed.

## 2026-10-31 — W6-DEMO-FINANCE-001 review handoff
- Assignment: review day-close, Cash/Bank sales, WAC, expenses and purchases; no frontend or other-owner implementation changes.
- Fresh tests: `python -m pytest services/finance/test_ledger.py services/api/test_costs.py services/api/test_retail_control.py services/api/test_app.py -q -p no:cacheprovider` — 25 passed in 13.74s. `python -m pytest services/inventory/test_movements.py -q -p no:cacheprovider` — 5 passed in 0.06s.
- Verified coverage: balanced ledger worked flow, cash/bank separation, expense draft/confirmation, purchase WAC, close breakdown/variance/locking/idempotency, inventory movements.
- Code-review blockers: services/api/app.py _day_close_breakdown ignores same-day opening_balance and does not carry prior-day sales/expenses/purchases/refunds/adjustments into opening; purchase tender converts micros to cents by floor division; WAC floors to integer micros without a residual valuation account. services/api/persistence.py sale creation does not select costs or capture sale COGS. No Ledger integration found in API. These are source observations, not live database verification.
- No live HTTP/browser/PostgreSQL validation performed. Ruzivo accounting review remains required in Verengai saved context.
- Files changed: own handoffs.md, current-state.md, tasks.md only. No application fixes.
- Next: Mutungamiri sequence Hwaro corrections and Ruzivo rounding/revaluation review; Chengetai validate integration and live demo. Restrict current evidence to tested in-memory flows.

## 2026-10-31 — W6-DEMO-FINANCE-001 expanded verification
- Fresh command: `python -m pytest services/finance/test_ledger.py services/inventory/test_movements.py services/api/test_costs.py services/api/test_retail_control.py services/api/test_voice_boundary.py services/api/test_app.py -q -p no:cacheprovider` — 47 passed, 8 SSL deprecation warnings, 32.08s.
- Fresh command: `python -m pytest services/api/test_muse.py -q -p no:cacheprovider` — 4 passed in 4.68s.
- Change evidence: voice tender test rejects received 149 cents against 150 due, accepts 200 received with 50 change and idempotent replay. Close sums sale total, not amount received, so change is not double-counted.
- Profit evidence: confirmed sale 150 cents with COGS 500000 micros yields 100 cents profit; draft expense excluded; confirmed 25-cent expense gives 75 cents profit. Missing-cost Muse coverage passed. Source review: recurring expense full amount is counted on any period overlap; period boundaries use UTC. Allocation and shop-local reporting require Ruzivo/Hwaro resolution.
- Highest-impact issue reproduced directly against fresh InMemoryStore route functions (no external data changed): create same-day opening_balance cash movement of 2000 cents, then day-close preview same date -> opening_cash_cents=0, expected_cash_cents=0. This is incorrect for a same-day opening float. Reproduction used CashMovementCreate(kind='opening_balance', occurred_at=datetime.now(timezone.utc), amount_cents=2000, tender='cash', actor='review', reason='same-day opening probe'). POST cash-movements endpoint accepted it; GET day-close/preview ignored it. Owner Hwaro should account for same-day opening and add regression coverage, then validate carry-forward separately.
- Scope decision: document API defect rather than modify Hwaro-owned application code. No frontend changes. No live HTTP/PostgreSQL claim. Ruzivo review remains outstanding in saved context.

## 2026-10-31 — W6 finance remediation handoff

### Assignment summary

Fixed the highest-priority finance-owned demo controls for cash/bank tender, change, expenses/profitability, damaged returns, reversals, and full day-close calculation. Work remained within `services/finance/`.

### Files changed

- `services/finance/ledger.py`: added `ProfitabilityReport`; validated/recorded sale amount received and change metadata; prevented bank change; corrected damaged-return posting; blocked duplicate reversal and reversal-of-reversal; made profitability reversal-aware and missing-COGS-safe; included same-day openings, reversal movements, and source warnings in daily close.
- `services/finance/__init__.py`: exported `ProfitabilityReport`.
- `services/finance/test_ledger.py`: expanded regression coverage to 8 tests for change, damaged-return inventory integrity, duplicate reversals, incomplete profitability, same-day opening, and reversal-aware close.

### Tests and results

- `python -m pytest services/finance -q -p no:cacheprovider` — PASS, 8 passed.
- `python -m compileall -q services/finance` — PASS.
- `git diff --check` — PASS.

### Accounting/control evidence

- Cash sale of 1.50 with 2.00 received records 0.50 change but debits cash by 1.50 only.
- Bank sale rejects received amount above the sale total.
- Sale COGS 6 followed by damaged return leaves inventory at -6, COGS at 0, and stock loss at 6; the original cost is expensed exactly once.
- Same-day opening of 20 plus a sale and its reversal closes at expected cash 20.
- Profitability returns net revenue, COGS, operating expenses, gross/net profit when complete, and explicit missing-COGS warnings with `gross_profit=None`/`net_profit=None` when incomplete.

### Outstanding issues / receiving-agent instructions

- Hwaro still owns API day-close same-day opening/carry-forward, API-to-journal integration, persistence, and warning propagation. This handoff does not claim those are fixed.
- Dura/Hwaro still own WAC residual precision, purchase payment linkage, and invoice atomicity.
- Ruzivo must re-review damaged-return reclassification and report semantics before financial sign-off; Chengetai should run cross-service and selected-backend integration tests.
