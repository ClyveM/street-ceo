# Verengai — Lessons

## 2026-10-30 — W2-VERENGAI-001

- The Ruzivo worked flow requires paid stock receipts even though the assignment headline emphasizes sales and cash movements; purchase postings are necessary to reproduce opening cash/bank and closing tender balances.
- Daily-close opening balances must be timestamped before the shop-local day boundary. A same-day opening entry is a movement in that day, not an opening snapshot.
- Journal account balances need an explicit sign convention in integration docs/tests: income credits are negative under debit-minus-credit.
- Repository-wide checks currently have unrelated import-path failures; finance verification must be reported separately rather than masking them by editing other owners' modules.
