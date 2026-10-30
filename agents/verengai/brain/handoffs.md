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
