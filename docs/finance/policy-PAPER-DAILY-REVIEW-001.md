# Reviewed daily-sheet sales — 2 November 2026

Task: PAPER-DAILY-POLICY-001. Ruzivo, internal accounting-policy review.
This is product advisory review, not statutory certification.

**Verdict: approve this architecture for implementation. No implementation or
release approval is given until source and regression evidence are reviewed.**

The Owner described a handwritten list combining the day's product sales, not a
set of individual customer receipts. Represent it as a distinct **daily sales
batch**. Do not fabricate customer transactions, customer receipts, amount
tendered, change or individual sale times from an aggregate image.

## Reviewed evidence before recording

OCR produces a draft only. The seller reviews and corrects the shop-local
business date, each catalogue product, positive whole quantity, actual selling
price or line revenue, notes/source and payment allocation. An unmatched product,
unreadable quantity, disputed amount or missing date cannot silently become a
confirmed value. Current catalogue price is a suggestion requiring seller review,
not proof of what the sheet's sales earned.

Use exact integer cents for revenue and payment amounts:

```text
sum(reviewed line revenue) = batch revenue
cash allocation + bank allocation + other supported allocation + unallocated
    = batch revenue
```

All allocations must be nonnegative; zero is valid when explicitly supplied.
Cash/bank allocations represent recorded payment, not cash received before change
or verified bank settlement. Unknown payment remains **unallocated**, never
silently cash or bank. If unallocated payment is permitted in a recorded batch,
cash closing must be explicitly blocked or otherwise require resolution before
asserting an expected/count comparison. It must not present cash as reconciled
while some of that day's batch proceeds might be cash.

## Demo date and duplication limits

For the first demo implementation accept only **today in the shop's business
timezone**, on an open day without a saved/frozen cash close. Reject future,
backdated and already-closed-day recording before any stock or sales mutation.
This avoids silently rewriting previous cash reconciliation. Historical imports
require a separately reviewed correction/late-activity design.

Show the day's existing individually recorded sales and prior daily sheets before
confirmation. Require an explicit declaration that this batch contains **only
sales not already recorded in the app**, not a replacement full-day total.
Idempotency prevents request replay but cannot by itself detect that a photograph
of the same paper was recropped or uploaded twice. Preserve source reference and
image/content digest and reject or clearly flag an already-recorded source.
Do not auto-subtract prior app sales from an OCR total: uncertain overlap requires
operator review rather than invented allocations.

## Stock and cost controls

Prevalidate every product and required quantity; no partial batch or negative
stock. A fresh review must capture the stock baseline/version. Confirmation must
reject if relevant stock changed since that review, requiring refresh/review.
The seller must know whether the sheet's sales are not yet reflected in recorded
stock. A relevant confirmed stock count may already have incorporated them.

For the minimal demo reject a batch that would double-deduct quantities already
represented by a same-day confirmed count. Supporting an explicit **stock already
reflected** mode would require a separate audited treatment and review; do not
silently skip or duplicate stock adjustment. Saving an OCR draft never changes
stock. Confirmed recording atomically saves batch, stock effects, audit links and
idempotency binding. An exact retry returns the original batch without deducting
stock again; a changed request under the same key conflicts. Uncertain outcomes
must be recovered from the original request/reference before another attempt.

The original day's sold cost is not automatically established by today's
catalogue cost or the weighted-average cost at import, particularly after
intervening purchases or cost corrections. Default historical COGS to unknown
unless supported by confirmed historical evidence under an explicit cost basis.
Any supported estimated valuation must be labelled as such and cannot be promoted
to confirmed historical product gross profit. Retain gross-profit completeness
rules: missing costs are not zero, and no current-cost repricing of older sales.

## Required integration and presentation

Include each confirmed batch exactly once in period sales and product quantities,
Today totals, sales history, Ask Muse evidence and cash-close activity. Keep
individual-customer transaction count separate from batch count. For example,
show **3 individual sales + 1 daily sheet**, not **4 customer transactions**.
Revenue from a batch must not also be inserted as ordinary synthetic receipts.

History identifies the aggregate source, business date, recording time, actor,
reviewed lines, tender allocation, stock treatment and confirmed/unknown cost
basis. Recorded cash contributes once to the open day's cash expectation; bank is
recorded only, and unallocated proceeds preserve reconciliation uncertainty.
Product gross profit remains incomplete where historical cost is unsupported.
Stock-only Undo is not a financial refund and must not silently erase batch
revenue. Any later correction needs an explicit linked reversal/correction design,
not editing or deleting a confirmed source.

The image may contain personal or financial information. Keep raw image/binary
data out of terminal payloads and sanitized trace logs, and exclude local source
images/databases from Git. Model use is an external processing step, not proof of
OCR correctness; follow actual user authorization and access controls for it.
Never bypass an external-call approval rejection or upload real evidence through
a fallback tool.

## Required final review

Inspect draft/confirm/recovery source and all reporting/cash-close integration.
Verify line/total/tender mismatch rejection, unallocated proceeds, closed/future/
past-date rejection, source duplication, stock availability and stale baseline,
all-or-nothing persistence, exact retry and restart durability. Test existing
ordinary sales plus an imported batch without duplicate revenue or a fabricated
customer count. Verify prior stock counts and unsupported historical cost remain
explicit limitations rather than silently assumed values.

This policy checkpoint involved read-only inspection of current saved-sale,
report and cash-close architecture. No new application tests, live requests,
external model calls, image uploads or financial postings were performed by
Ruzivo. Implementation review remains pending.

## Backend implementation checkpoint — 2 November 2026

**Verdict: backend financial treatment approved with conditions.** Final UI,
independent QA, runtime/APK and physical-device gates remain. The implementation
was read in `paper_sales.py`, the mounted routes and shop state, report/Today/
Ask Muse integrations, `cash_close.py`, `sales_answers.py` and SQLite model
registration, together with the owner's paper-sales regression source.

The confirmed model deliberately requires fully reviewed **cash plus bank equals
line revenue**. Unallocated proceeds are not supported for confirmation in this
version; an OCR draft may remain incomplete. This is a valid narrower treatment
than permitting unknown payment and then blocking cash close. It must not be
presented in the UI as permission to guess a tender allocation.

Reviewed lines allow a nullable unit price and an exact actual line total. When a
unit price is supplied, quantity times price must equal that total; when it is
absent, a mixed-price aggregate such as three units sold for 100 cents is possible
without inventing a 33-cent average. There are no amount-tendered/change/customer
receipt fields or synthetic ordinary sales created by confirmation.

Confirmation requires reviewed-version binding and explicit prices/new-only/
stock-not-already-reflected declarations. It rejects a non-today shop-local day,
closed day, relevant same-day confirmed count, missing products, insufficient
stock, changed stock/day activity and previously confirmed source or canonical
reviewed content. It prevalidates all lines before applying mutations. Exact old
idempotent retries return the original batch before current-day/closed guards;
a changed payload under that key conflicts, and another key cannot confirm an
already confirmed item. SQLite transaction persistence covers the batch, stock
adjustments, audits and binding; source/image/model fields are registered for
restart decoding. Exact-once and all-or-nothing durability still need the final
independent failure-path tests.

Reports consume confirmed batches separately and exactly once. Revenue/product
quantities and recorded cash/bank include the batch; ordinary customer receipt
count does not. Summary, daily and monthly output expose a separate sheet count.
Batch historical COGS is unknown, producing null product and summary gross profit
rather than current-cost substitution. Today uses the common report totals, and
Ask Muse evidence explicitly distinguishes daily summaries from customer receipts.
The cash-close event includes the reviewed cash allocation once under the batch
source ID. The legacy bank-sales loop also includes its bank allocation; the prior
limits on legacy bank reconciliation approval remain.

UI review must verify the added `missing_cogs_daily_summary_count` is included in
completeness validation and explanations. A report with zero missing ordinary
receipt costs can still have unknown cost from a daily sheet. Likewise, zero
customer receipts plus one daily sheet is not an empty sales period. History must
identify the saved sheet and its actual line totals/payment allocation, and
uncertain confirmation must recover the original binding without a second stock
deduction.

Hwaro reports 34 affected checks passed in 3.83 seconds using synthetic fixtures.
That result is attributed, not a Ruzivo execution. Ruzivo performed no application
runs, live calls, image uploads, external model calls or financial postings for
this checkpoint. No product code was changed. Final implementation approval is
conditional on the remaining UI and independent QA evidence; the overall ledger
and unrestricted historical import remain outside this approval.

## Export and client boundary review checkpoint — 2 November 2026

The financial content of `reportExport.ts` conforms to the report policy by source
inspection. Revenue uses cents, recorded COGS/profit retain exact micros, and
margin uses percentage units. Typed numeric CSV cells retain genuine negative
losses; untrusted labels are escaped rather than executed as formulas. Both file
representations retain currency, period, timezone, coverage, source timing,
unknown-value explanations, before-expense meaning and separate customer-receipt/
daily-summary counts. The percent-versus-currency regression and four other
independent export tests were inspected. Root reports the multi-page PDF/logo/
page-number visual check; this is attributed, not a Ruzivo render execution.

Final daily-sheet UI review remains pending. A targeted client correction was
requested: accepted confirm responses and confirmed GET recovery must match the
frozen pending `reviewed_version`, not merely the batch ID and confirmed status.
The server already enforces the review binding; the client must independently
verify it before reporting the original review as recorded. This is a client
boundary condition, not a discovered backend double-posting path.

### Explicit recovery to a fresh review

A narrow operator-selected **Review again** action is approved when an original
frozen-key retry has a verified definite noncommit rejection and a subsequent
fresh, same-shop/same-ID GET returns a verified draft/reviewed record. Generic
HTTP failure alone does not establish this. Authentication/scope failures,
idempotency payload mismatch, unverified responses, unavailable GET and confirmed
review-version mismatch must not be treated as proof of a failed original import.

Restart review on the same batch, retain the old key/version as an investigation
reference, safely clear or tombstone the active pending reference, and reset all
acknowledgements. Require a freshly saved review and explicit confirmation before
any new financial request. Do not auto-post or blindly upload the same sales as a
new batch. Immutable confirmed status, transactional version checking and source/
canonical duplicate guards must still handle a late original or other-client
confirmation race without another stock deduction. This policy addresses a
fail-closed usability dead end; it does not weaken uncertain-result controls.

The final UI review also identified a secondary presentation requirement: daily
and monthly tables must label ordinary transaction counts as **Receipts**, showing
any daily-summary count separately. Zero customer receipts with positive aggregate
sheet revenue is not zero sales. Hero/Today/export counts already distinguish
these sources in the inspected implementation.

The agreed first recovery implementation is narrower still: only the backend's
explicit `paper_review_stale` code from the original frozen-key retry may qualify,
followed by the fresh verified nonconfirmed same-batch GET and a separate operator
Review again action. The server must issue this code before any mutation. Other
4xx responses do not qualify. This coded path and the final UI/DOM evidence require
review after the implementation freeze; they were not yet verified at this
checkpoint.

## Final scoped financial implementation review — 2 November 2026

**Verdict: approve with conditions for the reviewed daily-sheet sales workflow
and Sales/Product Gross Profit CSV/PDF exports. No financial-code blocker remains
in the reviewed frozen scope.** Root must still complete the final integrated
regression gate, runtime/native/APK checks and actual-phone acceptance. This is
not approval of unrestricted historical imports, full bank reconciliation, a
complete ledger or statutory/net-profit reporting.

Reviewed the final `DailySheetPage.tsx` (renamed to avoid a Windows filename
collision), `paperSales.ts`, App/Reports/ProductProfit/Transactions integration,
`reportExport.ts` and the backend checkpoint above. The frozen frontend reported
by the implementer is `CvX88Bde` / `8Qthzhh1`; source inspection confirms the
following controls:

- OCR is editable draft evidence. The seller chooses catalogue products, positive
  quantities, actual line amounts, optional consistent unit prices and exact
  cash/bank allocation. Mixed-price daily lines do not require inventing an
  average unit price. Explicit zero payment amounts are entered rather than
  defaulted; no amount-tendered or change is invented.
- The reviewed server record is matched to the submitted date, lines, quantities,
  prices, totals, recorder/reference/notes and allocation. All three declarations
  are reset after edits/review. Saving a review does not record revenue or stock.
- Before confirmation, a frozen key/body is persisted and read back on the device;
  failure prevents sending the financial request. Accepted confirmation must match
  the original reviewed version, same batch and shop. Confirmed GET recovery
  checks that version before filling a success view or clearing the reference.
- Unknown outcomes keep normal navigation/new import/reconfirmation guarded. The
  old recovery offer is cleared before subsequent checks and retries; an
  unavailable or different confirmed review cannot retain a stale unlock offer.
- Only an original-key `paper_review_stale` rejection followed by a fresh verified
  nonconfirmed same-batch GET can offer explicit Review again. Retiring the old
  key/version writes and verifies an investigation tombstone before removing and
  verifying the active marker. The same batch returns to editing with all
  declarations reset; a retired version cannot be confirmed or retried after a
  partial storage failure. A new financial request requires a newly saved review,
  not an automatic new key/post. Backend immutable confirmation, baseline and
  duplicate controls remain authoritative for late-request races.
- Today and report heroes distinguish customer receipts from daily summaries.
  Secondary daily/monthly columns now say Receipts and separately show sheets.
  Customer history has a no-customer-receipts empty state and a separate daily
  summary link; it does not manufacture customer receipt rows. Actual confirmed
  batch records remain in their own saved history.
- Reports propagate `missing_cogs_daily_summary_count` alongside missing ordinary
  receipt costs. Historical sheet COGS and resulting profit remain unknown even
  when every catalogue product currently has a cost. A known ordinary product's
  profit is not erased, and a daily sheet is not counted as an individual sale.
- CSV/PDF financial values retain exact cents/micros and percentage units, signed
  losses, unknown/undefined values, period/currency/timezone/coverage and as-of
  metadata. They preserve customer/sheet count separation and the before-expense,
  illustrative-cost and stock-only reversal limitations. No current-cost
  substitution or arbitrary expense allocation is introduced.

Evidence is attributed to its actual owner: Hwaro's earlier 34 affected backend
checks passed; root reports 162 broader backend checks plus 11 independent paper
cases including disk-failure rollback, restart and exact original retry; Runako
reports 171 frontend checks passed. Root/Chengetai report paper DOM checks passed
in 5.03 seconds, covering allocation/mixed-price review, loss-of-response,
review-version mismatch and stale-offer controls, plus the integrated retained-
basket/manual-guard/photo check in 4.93 seconds. Five export unit cases passed,
and root reports an actual eight-page, 100-product PDF was rendered and visually
checked for logo/page numbering, numeric units, negative/unknown values and
coverage. The broader all-services isolated regression was still running when
this review was recorded and is not claimed as completed here.

Ruzivo executed no application suite, live request, OCR/model request, image
upload or financial posting during the final review. Only this memo and Ruzivo's
own brain files changed. Re-review any change to batch date limits, stock/COGS
basis, allocation, duplicate/retry/recovery semantics, completeness or export
units. Root may activate/package after the remaining quality gates pass.
