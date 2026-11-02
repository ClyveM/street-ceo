# Reports and counted-cash close QA — 2026-11-02

REPORTS-CLOSE-QA-001 checkpoint: independent offline checks PASS; integration and Ruzivo stable implementation review pending.

Full AGENTS/role/six-brain/task-board restoration, docs/reports-and-close-acceptance.md and Ruzivo policy-REPORTS-CLOSE-REVIEW-001 read. Scope tests/infra/.github/own brain, product read-only. No live finance/provider calls, reset, restart, host escalation or packaging. Root runs isolated HTTP/native and read-only runtime checks. Policy approval is not final implementation approval or full accounting certification.

## Tests and evidence

- tests/reports_close_acceptance.py11 pure policy cases: shop-local half-open date bounds and unique savedreceipt IDs, inclusive1/20/90 presets, legacy mixedbasket unknown product revenue/COGS, immutable future price/cost/label snapshots, missing versus explicitzero opening and banknull, one latestanchor+intervening trade, saleTOTAL nottender/change, paidcash expenses/purchases/refunds/signedadjustments, fractionalpayment unknown notfloor, priorcountvariance+lateactivitycarry with frozenclose, legacysingle attribution and stock-onlyUndo nofinancialrefund. Fresh11passed1.48s.
- tests/reports_close_client.mjs5 independent cases +owner7:12passed364.2933ms. Exact idleEndmyday/pending/manual/unknown guards, shortage/banknull/noauto-balance, verified serverprefix openingreason, deletedSKU-null/other-tender reports, fractionalpaymentnull onlywithreview, lostclose samebody/key uncertain retry.
- tests/sqlite_demo_acceptance.py2 HTTPcases added for root execution: missingopening409/fabricatedbankzero422; explicitopening+saleTOTAL, stale preview after sale409, savevariance/nullbank, restart exactretry/changedpayload409, postclose late sale preserves frozenreceipt and warns.
- New Python/Node files included CI explicit commands. Scoped diffcheck PASS, only Windows newline notices.

## Findings addressed by owners

Initial WIP reports needed uniqueSaleID dedup and currentmonth-to-date coverage; owner added both. Opening server auditreason prefix initially conflicted with clientinput equality, nullSKU deletedhistory and other-tender amount handling conflicted with parser; Runako aligned contract and independent APIshape fixtures pass. Fractionalpurchase paidcomponent now null/review, frontend accepts/displays Unknown rather than0. Legacy priorclose lacks cutoff/source evidence; owner added conservative possiblelate-ordering warning. New confirmation/actor validation concerns sent backend owner for review. Source fixtures gained posting timestamps as cutoff tracking evolved; no policy assertions weakened.

## Source review

Server preview/close use one explicit/priorcount anchor, counted-minus-expected variance, no balancing adjustment, cash-only banknull, preview digest concurrency and immutable saved snapshots. Source-linked late activity is disclosed and carried once rather than silently rewriting oldclose. Future receipt lines save unitprices/lineamounts and pre-sale costs; legacy mixed product amounts stay unknown, labels current/snapshot explicit. Reports use server shop timezone and observed coverage; current catalogue price is never substituted.

EndDay hook asks actualcash, asks explicit opening ifunknown with separateYes, previews comparison and asksYes beforeclose. Original config/body/key remain frozen across unknown results; confirmedopening followed by readfailure is recovered rather than duplicated. Shared handsfree/TTS loop answers without newApo, actual readiness shown. Endmyday command intercepts only exact idle/completed state, pending/manual/paidunknown guards retained. Optional stockcount/Skip does not gate cashclose; no historicalstock or accountingperiod lock promised.

Root host HTTP/backend/native tests and Ruzivo stablecode approval still required. Physical phone report dates, whole Endmyday opening/count/Yes/Cancel/recovery and optionalmonthskip remain acceptance, not inferred from source or fake transport.

## Additional source review caveat — pending owner disposition

QA found RetailControl still exposes legacy Daily close -> /day-close and the known old additive-opening/floored-purchase calculator remains in that path. The new cash-only path does not reuse it, but the old UI is reachable through retail controls. Root/Runako notified: hide/disable or route the demo entry to reviewed new flow, or explicitly retain the legacy path outside acceptance with finance approval. Do not claim all reconciliation was repaired. This is separate from the passing new cash-close calculation tests. A DST23h calendar-boundary test was added; fresh pure12 passed1.80s.

## Correction after full current legacy function read

The earlier legacy cash concern was based on an incomplete function read. Current app.py _day_close_breakdown calls calculate_cash_preview, rejects missing opening/payment evidence409, and replaces all cash buckets before return. Preliminary additive cash/floored purchase values do not reach the cash result. There is no current legacy-cash blocker on that basis. Legacy BANK figures remain recorded-movement estimates with an explicit warning; those are outside the new cash-only null-bank reconciliation scope. Root and Ruzivo were informed with the current source distinction. Historical policy defect finding remains valid for the old implementation, not the corrected one.

Root reports329 integrated Python passed41.53s including independent HTTP cashclose tests. Browser assertions reached completion but final CP1252 arrow printing caused exit1; root is rerunning corrected wrapper/final source, so that run is not claimed fully passed yet. Pure current12 passed1.80s; independent+ownerclient12 passed364.2933ms. Ruzivo is reviewing stable actual implementation; finalfinancegate pending.

## Root frozen-build browser evidence

Root reports final DOM simulated-ASR scenario PASS on retry6.8s: bare End my day, countedcash first, explicitzero opening/Yes, shortage0.50/finalYes,503 Retry with identical payload/key, Cancel blocked while unknown, bankunknown, Done→nextApo, monthly/product reports,390/320-width nooverflow, Skip and actualStocktake tab. First final rerun hit local page-start timeout; repeat passed. This is simulated browser/DOM evidence, not physical/native acoustic acceptance. Final backend narrow guard and Ruzivo implementation signoff remain pending.

## Narrow guard recheck

Current source verifies exact old generic cash-movement replay precedes new-input restrictions; new cash opening via generic route409 directs confirmed opening endpoint; future actual cash movement422. Preview excludes legacy future-effective events and warns. Independent fixed-clock futureevent regression passes: finalpure13 passed1.24s. Added generic-opening bypass409 assertion to independent HTTP close test for rootrun. CI includes final testfiles. Ruzivo informed with exact current guard; host affected regressions/final financial disposition pending.

## Final source/software gate — PASS

Final root post-guard integrated suite **333 passed33.56s**, including all independent reports/cash tests, generic-opening bypass and future-effective controls. This supersedes the earlier329 pre-guard result for final regression evidence. Root reports129frontend and12combinedclient checks passed; frozen-build DOM simulated-ASR flow passed as described above. QA's independent post-guard pure13 passed1.24s and scoped diffcheck passed. Host/owner results are attributed, not QA executions.

Read Ruzivo's final actual-code addendum: **APPROVE WITH CONDITIONS**, opening bypass blocker cleared. Guard order preserves exactoldreplay, newgenericcashopening409/futureactualcash422, legacyfutureevents excluded/warned. Conditions retain warnings/uncertainty, exactruntime/APK verification and physicalphone acceptance; legacybank estimates, full balancedledger/netprofit/statutoryperiodlock/production accounting are excluded.

No remaining concrete blocker for the scoped source/software gate. Root owns native packaging, signatures/assets/download and read-only runtime verification currently underway. No live original-shop close, opening, adjustment or provider call was made by QA. Physical Endmyday and reporting acceptance remains separate; no acoustic or bank reconciliation claim. Final files: tests/reports_close_acceptance.py, tests/reports_close_client.mjs, tests/sqlite_demo_acceptance.py, tiny .github/workflows/quality.yml inclusion, this report and ownbrain updates. All handoff evidence persisted; no active QA processes or further product/code changes planned.
