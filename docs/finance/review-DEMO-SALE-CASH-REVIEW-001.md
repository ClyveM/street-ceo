# Connected sale and cash-change review — 2026-11-01

Task: DEMO-SALE-CASH-REVIEW-001. Ruzivo. Internal advisory code review, not
statutory certification.

Current addendum: **SPRINT90-CASH-REVIEW-002** below supersedes condition 2 for
the newly implemented manual cash-received flow. The original review is retained
as historical evidence.

**Verdict: approve with conditions for the scoped connected sale demonstration.**
This verdict covers catalogue-priced sales, quantity/stock changes, voice tender,
cash received/change, historical sale cost preservation and retry safety on the
single-worker SQLite demo. It does not approve full accounting, profitability,
day-close, invoices, returns, production security or physical-phone behavior.

## Reviewed treatment

- Server total is catalogue unit price in integer cents multiplied by positive
  quantity. The sale validates every product and available stock before any stock
  decrement. Duplicate product lines are rejected by the request schema.
- Voice commit accepts only the resolved reviewed basket. It asks for missing
  tender or cash amount; insufficient cash cannot commit. Cash change is received
  minus total. Bank records the total with zero change and is not proof of settlement.
- Voice receipt validation checks the reviewed products/quantities, stock values,
  tender, received amount and change identity before reporting success. Mutating
  server failures preserve an uncertain outcome and the original recovery key.
- Sale cost snapshots pre-sale product costs. If any cost is missing, total COGS
  remains unknown rather than treating missing cost as zero. Stored sale totals,
  COGS, receipts, review bindings and retry keys survive explicit SQLite encoding.
- A committed voice review binds to one sale/key. Exact retries return its original
  receipt, including after catalogue changes/reopen; changed payloads or a new key
  against that review conflict. The SQLite request transaction stages state and
  commits before successful receipt delivery. Failed writes roll back stock and sale.
- A postcommit trace failure is correctly treated as an uncertain response; the
  original sale may exist and must be recovered under its original key. It must
  never be described as proof that the sale was rolled back.

## Conditions for the demonstration

1. Use the verified single-worker SQLite runtime and the supported cash/bank UI
   paths with the seeded small integer-cent prices. No concurrent price editing
   is part of the reviewed demonstration.
2. Demonstrate cash received and change through the voice path. The manual-sale
   request does not collect a received amount; its stored received amount is null
   and its change defaults to zero. That manual receipt records sale/tender, not
   verified physical cash received or a manual change calculation.
3. Do not call sales revenue profit or present the sale state store as a fully
   integrated balanced journal. Missing COGS stays unknown. The broader financial
   review in `review-W6-DEMO-FINANCE-REVIEW-001.md` is not cleared by this verdict.
4. Keep bank receipts labelled as recorded tender, and retain the uncertainty and
   original-key recovery behavior on server/trace failure. APK audio/recognition
   acceptance must still be observed on a real phone.

## Evidence and limits

Inspected `services/api/app.py` models, `InMemoryStore.create_sale`, voice commit,
manual sale/history routes; `services/api/sqlite_store.py`; frontend
`quickSale.ts`, `saleRequest.ts` and App receipt refresh; backend real-file tests,
independent `tests/sqlite_demo_acceptance.py`, current acceptance document and QA
report. Arithmetic example in the persisted test: one Coke at 150 cents plus two
sugar at 240 cents totals 630; received 1000 gives change 370.

Parent fresh host evidence: 181 backend/independent acceptance tests passed.
Runako evidence: 114 frontend tests and production build passed. Chengetai report
records focused voice bridge/retry checks. These are attributed results, not test
runs performed by Ruzivo. No live mutation, provider request, database restart,
physical-phone test or new application test was performed during this review.

No product code changed. Next: Mutungamiri verifies exact APK packaging/current
runtime and obtains physical voice sale/repeat evidence; reopen this review if
pricing, tender, sale commit, receipt or persistence semantics change.

## 2026-11-01 addendum — SPRINT90-CASH-REVIEW-002

**Verdict: approve with conditions for both manual and voice sale/change demo.**
The earlier condition restricting received/change demonstration to voice is now
superseded for new manual sales through the current UI.

Inspected the updated `SaleCreate`, `InMemoryStore.create_sale`, payload
fingerprint, SQLite tests, `App.tsx`, `SellCheckout.tsx`, `saleRequest.ts`, exact
cash parser and frontend receipt tests. New manual requests can supply a strict,
nonnegative integer `amount_received_cents`. The server computes catalogue total
first, rejects insufficient cash and non-exact supplied bank amounts before stock
mutation, then records authoritative cash change as received minus total. The
SQLite transaction persists that receipt and stock together.

The UI converts at most two decimal places to integer cents without floating-point
rounding, requires enough cash before confirmation, labels the local change as a
preview, and displays the saved server receipt. Receipt parsing verifies the
requested received amount and the change identity; unverified/5xx outcomes retain
the original configuration, payload and key for recovery while basket/payment
editing is locked. Summary/history refresh failure does not turn an established
receipt into a second sale.

Compatibility is appropriate: `exclude_none=True` preserves the prior omitted-field
fingerprint, including an explicit null retry. Such legacy receipts still have an
unknown received amount and zero default change; they must not be retroactively
described as verified exact cash. Current UI cash sales explicitly supply the
amount. Bank without a supplied amount remains recorded tender with zero change,
not evidence of bank settlement.

Evidence inspected includes tests for 300-cent manual total, 500 received and 200
change, underpayment without mutation, strict rejection of boolean/fractional/
negative/string inputs, bank validation, reopen/exact retry, changed-amount conflict,
legacy omitted/null compatibility and frontend inconsistent-receipt rejection.
Parent reports 188 backend/acceptance passes and 120 frontend passes before a minor
trace-UI fix. These results are attributed, not rerun by Ruzivo. No application test,
live request, source edit or phone test was performed during this addendum review.

Remaining conditions from the original review still apply: single-worker SQLite,
supported modest integer-cent catalogue prices, recorded-only bank tender,
uncertain-outcome recovery, no full ledger/profit/day-close claim, and separately
verified APK runtime/audio. The broad financial review remains separate.
