# Verengai — Memory

Initialized 2026-10-29. No prior sessions; no work performed yet.

## Project facts (confirmed)

- Street CEO hackathon MVP; deadline November 4, 2026.
- Finance scope: sales, payments, P&L, cashflow, cash/bank reconciliation.
- No application code exists yet; ledger not yet designed.

## Stable context

- Role: `agents/verengai/role.md`. Activation protocol: `AGENTS.md` section 2.
- Implements `docs/accounting-rules.md`; accounting treatment authority is Ruzivo's.
- Works under Ruzivo's functional review on all significant features.
- Invariants: balanced entries; dated, sourced, reversible; no silent edits/deletes.

## Verified implementation facts (2026-10-30, W2-VERENGAI-001)

- `services/finance/ledger.py` provides an in-memory, persistence-agnostic double-entry journal using exact `Decimal` amounts and deterministic `JE-######` IDs.
- Supported posting flows are opening balance, paid/unpaid stock purchase, sale, resalable/damaged return, paid/unpaid expense, owner injection/drawing, append-only reversal, and locked daily close.
- Every entry stores shop, currency, source type/id, actor, event time, record time, postings, warnings, and optional reversal/source metadata. `balance()` is debit-minus-credit, so credit-normal income/equity accounts are negative.
- Finance tests are in `services/finance/test_ledger.py`; they cover the Ruzivo worked demo, balance invariants, warnings, reversals, and daily-close variance locking.
