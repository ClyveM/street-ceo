# Verengai — Lessons

## 2026-10-30 — W2-VERENGAI-001

- The Ruzivo worked flow requires paid stock receipts even though the assignment headline emphasizes sales and cash movements; purchase postings are necessary to reproduce opening cash/bank and closing tender balances.
- Daily-close opening balances must be timestamped before the shop-local day boundary. A same-day opening entry is a movement in that day, not an opening snapshot.
- Journal account balances need an explicit sign convention in integration docs/tests: income credits are negative under debit-minus-credit.
- Repository-wide checks currently have unrelated import-path failures; finance verification must be reported separately rather than masking them by editing other owners' modules.

## 2026-10-31 — W6 finance remediation

- Cash received and change are receipt metadata; only the sale total is posted to cash, so change cannot inflate day-close cash.
- A damaged return of an already-sold item reclassifies the original COGS to stock loss. Crediting inventory again would double-reduce inventory.
- Close calculations must use the full tender posting delta, including reversals, while treating same-day opening entries as opening float.
- Profitability must remain explicitly incomplete when any included sale lacks COGS; revenue alone is not profit.
