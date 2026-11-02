# Product gross-profit reporting — 2 November 2026

Task: PRODUCT-PROFIT-POLICY-001. Ruzivo, internal accounting-policy review.
This is product advisory review, not statutory certification.

**Verdict: policy approved for implementation. Final implementation approval
requires review of frozen source and regression evidence.**

## Meaning and evidence

Report **gross profit before shop operating expenses**. It is not net profit,
cash generated, bank settlement or a complete financial statement. Do not
allocate rent, wages or other common expenses arbitrarily to products.

Use the selected shop-local report period and saved receipt values. Revenue is
recorded sale value; COGS is the cost saved for that sale. A later catalogue price
or cost change cannot reprice an earlier receipt. Existing exact single-product
legacy attribution may be used; multi-product legacy amounts that cannot be
allocated reliably remain unknown. A missing cost is not a zero cost. An explicit
saved zero cost is valid and may produce a 100% margin.

Starter costs remain illustrative demo inputs rather than verified supplier
invoices. This limitation carries through to the resulting gross profit.

## Arithmetic and precision

One currency unit is 100 cents or 1,000,000 micros. For each product and the
summary independently, where revenue and cost are complete:

```text
revenue_micros = revenue_cents × 10,000
gross_profit_micros = revenue_micros − cogs_micros
margin_bps = ROUND_HALF_UP(gross_profit_micros × 10,000 / revenue_micros)
```

Return `gross_profit_micros = null` when revenue or COGS is unknown. Return
`margin_bps = null` when revenue or COGS is unknown **or revenue is zero**.
A known zero-revenue sale can still have a known gross loss; its percentage
margin remains undefined. Empty periods have zero sales, zero recorded COGS,
zero gross profit and an undefined margin.

Basis points are hundredths of one percent: 3,333 basis points means 33.33%.
Use exact integer/Decimal arithmetic. HALF_UP ties round away from zero, so a
negative half-basis-point becomes minus one basis point. Negative profit and
negative margins are legitimate; never clamp them to zero or minus 100%.

Aggregate original exact revenue and cost before deriving summary profit and
margin. Do not average product margins or sum rounded product display amounts.
If currency is displayed to two decimal places, round exact micros HALF_UP for
display only. Keep exact stored/report values unchanged and preserve loss context
for a negative amount that rounds to zero at display precision.

## Completeness, ranking and reversals

A known overall receipt total/cost may support overall gross profit while an old
mixed receipt cannot support product profit. Show that distinction rather than
fabricating line allocations. Known partial subtotals must be labelled partial;
they are not complete COGS or gross profit.

Product ranking may order complete gross profits, including zero and losses.
Unknown product profit cannot be ranked as if it were zero. Disclose incomplete
products separately or mark them visibly as unranked/incomplete. Preserve ties
honestly and do not describe a loss-leading product as profitable merely because
it is the highest known result.

The existing stock-only Undo does not establish a financial refund. Continue to
show gross recorded receipts/COGS/profit consistently and disclose stock-only
reversals separately; do not silently reduce revenue, COGS or gross profit.

## Required implementation review evidence

Inspect API arithmetic and nullable fields, historical snapshot use, frontend
validation/formatting and labels. Test ordinary profit, loss, zero cost, zero
revenue, no sales, missing cost, mixed legacy allocation, changing catalogue
costs, exact aggregation and positive/negative rounding ties. Preserve existing
date bounds, receipt deduplication, future exclusion and reversal disclosure.

No application tests or live financial requests were performed for this policy
checkpoint. The existing `services/api/reports.py` and prior reports/cash-close
policy were inspected to establish current evidence and completeness semantics.

## Backend source review checkpoint — 2 November 2026

The frozen `services/api/reports.py` implementation and
`services/api/test_product_profit.py` were inspected. **Backend calculation
approved with conditions:** final frontend display/validation and Chengetai's
integrated regression evidence remain outstanding.

`_gross_profit` uses integer multiplication/divmod, rounds signed basis-point ties
away from zero, returns undefined margin at zero revenue, and preserves null
incomplete inputs. Product fields are derived only after their historical revenue
and cost completeness checks; the summary uses complete aggregate saved receipt
COGS independently. No expense allocation, net-profit claim or mutation was
introduced. The existing report period, deduplication, legacy allocation and
stock-only reversal treatment remain in place.

The five inspected owner tests cover historical cost/price changes, duplicate
receipt aliases, signed half-basis-point ties, zero costs, zero revenue, losses,
unknown-cost propagation, mixed legacy product allocation versus known summary,
and no-sales zero profit. Hwaro reports 18 affected tests passed in 1.79 seconds;
that result is attributed, not a Ruzivo application-test execution. Ruzivo's own
six isolated Decimal policy-arithmetic assertions passed. Final release approval
awaits the UI and independent QA review; no live financial requests were made.

## Final scoped source review — 2 November 2026

**Verdict: approve with conditions for product gross-profit reporting.** The API
and frozen frontend accounting treatment conform to this policy. Release still
requires Chengetai's final built-app checks, root runtime/APK verification and
actual-phone acceptance; no full-ledger or net-profit approval is inferred.

Read `ProductProfit.tsx`, `reportPresentation.ts`, `reportsClose.ts`, `Reports.tsx`
and `productProfit.test.mjs` after the frontend freeze. The client independently
verifies exact gross profit and rounded signed basis points using BigInt. A
reported missing-cost count now forces summary COGS to remain null even when an
optional known subtotal field is absent; the regression rejects a falsely complete
profit in that case. Product unknown-cost/revenue evidence likewise cannot be
presented as complete profit. Old Sales responses without additive profit fields
remain readable, while Profit explicitly remains incomplete rather than zero.

UI labels distinguish gross profit/loss and state that shop expenses are not
included. Zero revenue produces an undefined margin; losses remain signed;
unknown products are visibly incomplete and placed after known values without a
false numeric profit rank. Exact six-decimal figures remain available. HALF_UP
cent formatting preserves tiny nonzero losses explicitly, rather than showing a
misleading zero; the illustrative nature of starter costs is disclosed.

The selected period and existing report evidence remain shared by Sales and
Profit. No current-cost substitution, arbitrary expense allocation or financial
posting was introduced. Stock-only reversal disclosures remain part of the
report's existing explanation.

Evidence read/attributed: Hwaro 18 affected backend tests passed in 1.79 seconds;
Chengetai 46 independent/affected API checks passed in 2.17 seconds, including
Decimal rounding references; Runako 150 frontend tests passed after the targeted
completeness guard. Their test sources were inspected. Ruzivo did not execute
application tests, make live requests or post financial records. Ruzivo's six
isolated Decimal policy checks passed earlier. Final built-page checks were still
in progress at this financial source-review checkpoint and are not claimed here.

Changed files are this finance memo and Ruzivo's own brain checkpoints only.
Re-review any change to historical cost/price evidence, profit arithmetic,
completeness handling, rounding, reversal treatment or net-profit labelling.

### Independent QA evidence received after source review

Chengetai subsequently reported the final frozen bundle
`shop-aJiWshyF.js` / `shop-BlT4jWd4.css` passed 10 client checks in 246.91ms and
46 API checks in 2.17s. Built-app checks passed complete profit, losses and
negative margins, tiny loss, zero revenue, incomplete products, empty periods,
invalid-profit/error handling and shared verified Sales/Profit periods at mobile
widths. These results are attributed, not Ruzivo test executions. The final QA
condition is satisfied on that reported evidence; root runtime/APK and physical
phone conditions remain. The scoped accounting approval is unchanged.
