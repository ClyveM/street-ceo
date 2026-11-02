# Period reports and counted-cash close — 2026-11-02

Task: REPORTS-CLOSE-REVIEW-001. Ruzivo. Internal product accounting policy and
advisory review; not statutory certification. Owner requested period/product sales
reports, hands-free End my day cash reconciliation and optional month-end stock count.

**Policy approved for implementation; actual implementation approval is pending.**
Historical status above is superseded by the final scoped implementation review
at the end of this document.
The current `_day_close_breakdown` incorrectly sums all older opening balances,
omits same-day opening and ignores intervening trading when carrying cash forward.
That calculation must not be reused unchanged for the new feature.

## Cash opening and activity

An opening balance is a balance anchor, not an additive cash inflow. Choose one
valid latest anchor: a saved prior cash close's **counted** cash, or a later explicit
opening count. Carry forward signed recorded cash activity after that anchor's
cutoff up to the new period's start. Never add all prior opening declarations or
all daily closing counts together.

An explicit daily opening refers to start of that business day in the shop's time
zone, including a same-day opening. Zero is valid if explicitly supplied. Do not
silently replace a trading-day balance with a new opening after trading has begun;
require a reviewed correction/reset with its own source or reject it. If there is
no valid opening/close anchor, opening is unknown: ask for the opening amount,
including explicitly confirmed zero. The closing cash count must not be used to
infer opening and manufacture a zero discrepancy.

A first **missing** opening may be declared retrospectively after that day's
trading, including during End my day. The operator states what they started with,
supplies a reason/source and explicitly confirms it. Store its effective local
day-start separately from its actual creation time and identify it as a late
declaration. This is filling an absent anchor, not replacing a known one. Neither
the end count nor the desired variance may be used to derive that opening. Apply
the known-anchor/closed-date guard consistently across old and new opening routes.

Prior counted cash represents physical carry-forward, but a prior short/over is
not thereby explained: retain the earlier variance and a visible warning. Saved
prior closes are immutable. Opening provenance and the cutoff must be visible.

For a complete period:

```
expected cash = opening cash
              + cash sale totals
              - confirmed paid cash purchases
              - confirmed paid cash expenses
              - explicit cash refunds
              + signed cash adjustments
variance = counted cash - expected cash
```

Use each sale's saved **total**, not the amount tendered: change has already been
returned. Do not subtract change again. Bank sales do not affect cash. Unpaid/draft
purchases and expenses do not affect cash. Opening/injections/drawings/adjustments
are not sales or operating profit; require explicit source/type and correct sign.
A stock-only voice Undo is not an actual refund and must not reduce expected cash.

Use recorded paid currency-minor-unit amounts where available. Inventory valuation
micros are not proof of the tender paid: silently flooring a fractional-cent
purchase value is prohibited. Legacy fractional payment uncertainty must be
flagged and resolved or explicitly disclosed; any estimate using a currency-rounding
rule must be named as such, preserve the source/residual, and not be called a
verified actual payment. Round a payment once at its aggregate amount, not each
valuation component independently.

Examples: opening 20.00 plus a 3.00 cash sale gives 23.00 even if the customer
tendered 5.00 and received 2.00 change. If the saved count is 22.00, variance is
-1.00 (short). Next day's opening may carry 22.00, with the prior -1.00 unresolved
variance retained. A new explicit opening of 22.00 is a replacement anchor, never
20.00 + 22.00. Same-day opening of 20.00 must count once.

## Cash-only closing controls

Ask for the actual cash on hand in exact cents, preview opening/activity/expected/
counted/variance and obtain explicit confirmation before saving. Negative variance
means short; positive means over. Explain discrepancies; never adjust them away.

A cash-only close leaves bank counted balance and bank variance **unknown/null**,
labelled not counted/unverified. Do not submit a fabricated bank zero to satisfy
the older full-close contract. Recorded bank tender is not proof of settlement.

Save a source-linked immutable snapshot with business date/time zone, as-of cutoff,
opening anchor, counted cash, signed components, source IDs or digest, variance,
warnings, actor/confirmation and stable idempotency key. A stale preview must
conflict if intervening financial data changes. Exact retry returns the original
close; changed payload under the same key conflicts. Do not rewrite earlier closes
or create duplicate close movements during replay/restart.

Late/backdated activity after the frozen cutoff must be rejected for the closed
period or appear as explicitly flagged later activity/correction. Never silently
recompute a saved close and call it reconciled. A future carry-forward calculation
includes qualifying movements after the saved cutoff exactly once. If a legacy
source has only a business date and no sufficient cutoff/confirmation evidence,
flag possible late activity rather than claiming an exact ordering.

## Sales and product reports

Custom start/end dates are inclusive shop-local calendar dates, implemented with
the half-open instant range from start-day midnight to midnight after end-day.
Presets mean today (1 day), today plus the prior 19 days (20 days), and today plus
the prior 89 days (90 days), with explicit dates shown. Calendar months use their
calendar boundaries; identify current-month to-date coverage rather than project
future sales. Count unique saved receipts, not retry requests.

Shop gross sales are the sum of saved receipt totals in the period. Product
quantities use saved receipt lines and IDs; current catalogue labels, if shown,
must be identified as current labels. For future receipts persist authoritative
unit selling price/line total and pre-sale unit cost/line COGS snapshots.

Legacy single-line receipt totals are exactly attributable to that product; its
known receipt COGS is attributable too. Legacy multi-line receipts without line
price/cost snapshots have accurate quantities but unallocated product revenue/COGS.
Do not use current prices/costs, pro-rata invented allocations or assume zero for
unknown history. Label known subtotals as partial and expose unknown/unallocated
amounts/counts. Product gross margin is unknown where its revenue or COGS is unknown.

Stock-only Undo remains a separate stock-restoration count/quantity, with a warning
that no financial refund/revenue reversal is verified. Retain the original gross
sale/cash/COGS receipt; do not describe stock restoration alone as net sales or
profit reversal. An actual cash refund needs its own explicit recorded movement.
Gross margin is not net profit; starter costs remain illustrative demo assumptions.

## Optional month-end stock count

Stock count is optional and never a prerequisite for saving a cash close. Accept
nonnegative integer unit counts, compare against a dated/versioned stock snapshot,
and show quantity variance as counted minus expected. Posting stock adjustments
requires its own explicit reviewed confirmation and audit source. Do not invent
sales, purchases, cash flows or supplier evidence to explain a variance.

Historical month-end stock/value requires a saved as-of snapshot or sufficient
audited movements; today's stock is not a historical month-end count. Unknown
valuation remains unknown. A stock count is not a new cash opening/closing anchor.

## Required evidence and handoff

Hwaro implements; Runako presents and speaks the same scoped contract; Chengetai
independently verifies. Required cases include same-day opening, noncumulative
multiple openings, previous count/variance carry-forward, prior/intervening trade,
cash overpayment, expenses/purchases/refunds/adjustments, missing opening/bank,
preview race, frozen/late activity, restart/retry and legacy product price gaps.
Month-end stock omission must not block cash close. Ruzivo must review stable
code before final scoped implementation approval.

This policy review inspected current day-close/movement models and calculation,
existing finance policy, sale/stock-only reversal records and known receipt
snapshot limitations. No application tests, live requests, financial postings or
source edits were performed by Ruzivo. Existing full-ledger/production sign-off
remains separate.

## Actual implementation review checkpoint — 2026-11-02

**Verdict: one confirmed control blocker remains before cash-close approval.**
The new confirmed opening endpoint correctly permits a late first declaration of
a missing start-of-day balance after trading; it refuses an already known anchor.
However, the old generic `POST cash-movements` still accepts new cash
`opening_balance` requests without that guard. This can replace a known anchor
or influence a closed period through a different route. Root agreed to reject
new cash opening requests there and direct them to the confirmed opening endpoint,
while preserving exact historical idempotent replays before the new restriction.
Verify that guard and regression before final cash-close implementation approval.

The rest of the inspected new treatment conforms to the scoped policy:

- `cash_close.py` selects one opening/count anchor, carries qualifying intervening
  cash events, retains prior-variance warnings, uses cash sale totals rather than
  tendered amount, includes signed cash flows and refuses unknown/fractional
  purchase-payment evidence rather than silently flooring it.
- New close models keep bank count/variance null, require strict confirmation and
  exact integer counts, expose short/over, and persist source IDs/version/cutoff.
  Stale preview conflicts and same-key replay/frozen close handling are present;
  later source IDs produce a visible late-activity warning without rewriting amounts.
- The legacy full close now obtains **all cash components** from that corrected
  common engine and refuses missing opening/payment evidence. Its preliminary old
  cash sum/floor is not returned. Legacy bank figures remain recorded-movement
  estimates with an explicit warning; they are not approved bank reconciliation.
- The legacy full close now refuses a date already cash-closed, preventing competing
  saved counts. New cash-only close already refuses either kind of saved close.
- `reports.py` uses inclusive local-date bounds and unique saved receipts; new
  server-generated receipt line price/cost snapshots survive current catalogue
  changes. Legacy single-line amounts are attributable; multi-line missing evidence
  remains unknown/unallocated. Missing COGS and stock-only Undo are disclosed.
- Month-end stock count remains a separate optional inventory workflow and does not
  block cash close or establish a financial refund/revenue adjustment.

Inspected models/routes in `app.py` and `retail_control.py`, `reports.py`,
`cash_close.py`, `REPORTS_CASH_CLOSE_CONTRACT.md`, owner/backend tests and independent
`tests/reports_close_acceptance.py`. Chengetai reports root's 329 Python passes plus
12 independent pure-policy and 5 client cases; these are attributed results, not
Ruzivo executions. UI physical voice/reconciliation behavior is not established by
this review. No application tests, live requests or financial postings were
performed by Ruzivo. Final approval awaits the agreed generic-route guard and
its regression evidence. Full balanced-ledger/production approval remains separate.

## Final scoped implementation review — 2026-11-02

**Verdict: approve with conditions for the new period/product reports and
cash-only counted close. The confirmed opening-route blocker is cleared.**

Inspected the final generic cash-movement route: it checks historical idempotency
first and returns the original exact replay, then rejects every **new cash opening**
with 409 directing the explicitly confirmed opening endpoint. It also rejects new
future-effective actual cash movements with 422. This prevents bypassing the
missing-only/known-anchor/frozen-date controls while retaining old receipts and
bindings. The confirmed opening endpoint still permits a first missing opening
declared late after trading, with actor/reason/effective day-start and actual
creation timestamp; it cannot derive that amount from the end count or replace
an existing anchor.

The final cash preview excludes legacy future-effective cash activity until its
effective time, emits an explicit warning, and does not add it to applied source
IDs before that time. Once effective, it participates in the next preview/version;
a saved close remains frozen with later activity disclosed. Owner regressions and
the independent future-effective case cover these semantics, alongside known/frozen
opening rejection, exact old replay and unchanged legacy bank request behavior.

The scoped controls and reporting treatment from the preceding review remain
approved: one balance anchor, counted carry-forward with prior variance warnings,
saved cash sale total rather than tendered amount, unknown opening/payment guards,
null uncounted bank, explicit confirmed count/variance, stale-preview conflict,
immutable receipt/retry recovery, historical line price/cost evidence, unknown
legacy allocation and stock-only Undo disclosure. Optional stock count is separate
and does not gate cash closing.

Conditions: root/Chengetai complete the final integrated regression run and exact
runtime/APK verification, preserve warnings and uncertainty handling in the UI,
and obtain actual-phone voice/report/count acceptance. Legacy bank figures remain
explicit recorded-movement estimates and are not approved bank reconciliation.
No complete balanced-ledger, net-profit, statutory period lock or production
accounting approval is inferred.

Parent reports 15 owner reports/retail regression passes including the final guard;
the earlier 329-Python run predates this last guard and is not misrepresented as
the final integrated run. Independent guard tests were inspected in source. No
application tests, live calls or financial postings were performed by Ruzivo.
Only this finance memo and own brain checkpoints changed. Re-review if opening,
cutoff, cash movements, price/cost evidence, close or retry semantics change.
