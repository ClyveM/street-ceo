# Verengai — Decisions

## 2026-10-30 — W2-VERENGAI-001

- Use an append-only in-memory journal as the first implementation boundary. This keeps posting rules deterministic and lets Hwaro replace storage later without changing accounting treatment.
- Use `Decimal` currency units, not floats. API adapters can convert integer minor units at their boundary.
- Use debit-minus-credit for account balances. This preserves normal double-entry signs: assets/expenses are positive and credit-normal income/equity/liabilities are negative.
- Use sequential entry IDs (`JE-######`) for reproducible tests and explicit reversal links. Reversal copies the original postings with debit/credit swapped and never edits or deletes the original.
- Keep incomplete data visible through warnings: missing COGS/price, unlinked or damaged returns, unknown opening source, unpaid supplier/expense state, missing close confirmations, and unexplained variances.

## 2026-10-31 — W6 finance remediation

- Record cash received and calculated change as sale metadata only; post the net sale amount to the tender account. Bank tender must equal the sale total.
- Treat damaged returns as a COGS-to-stock-loss reclassification because the original sale already reduced inventory.
- Derive close tender movement from all journal posting deltas and resolve reversal entries to their original source type. Include same-day opening entries in the opening float exactly once.
- Expose a `ProfitabilityReport` from journal queries; with missing COGS, report the monetary inputs and warnings but no gross/net profit.
