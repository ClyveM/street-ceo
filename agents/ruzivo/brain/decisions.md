# Ruzivo — Decisions

## 2026-10-30 — W1-RUZIVO-001 MVP policy

- Adopt weighted-average cost for MVP stock valuation and COGS, with cost calculated
  at receipt and COGS applied at the pre-sale cost.
- Treat cash and bank as separate operational tender balances; bank/wallet settlement
  is not verified by the MVP.
- Treat owner injections/drawings and opening balances as non-revenue/non-expense
  balance movements, with explicit source and incomplete-data warnings when unknown.
- Require reversal entries, source links, daily tender close, and visible discrepancy
  warnings. No silent edits, hidden corrections, or automatic unexplained adjustments.
- Approve the memo for MVP implementation only; production/tax questions remain open
  and the reports must not be presented as statutory or audited accounts.

## 2026-10-31 — W6-DEMO-FINANCE-REVIEW-001
- Block financial sign-off pending close, journal/COGS integration, precision, invoice atomicity, damaged returns and correction controls. Preserve inventory total value and explicit rounding residuals; a damaged return must not credit inventory twice after a sale.
- Correct prior policy worked-example numerator from 40.00 to 22.00; WAC and subsequent totals were already based on 22.00.

## 2026-11-01 — DEMO-SALE-CASH-REVIEW-001
- Loaded AGENTS, role, six brain files, current task/board, accounting rules and connected demo acceptance; confirmed read-only product scope, writes docs/finance and own brain only; prior handoff read.
- Completed scoped code review; verdict APPROVE WITH CONDITIONS for single-worker connected SQLite catalogue/manual sale and voice sale/tender/change/stock/history/retry demonstration. Memo: docs/finance/review-DEMO-SALE-CASH-REVIEW-001.md.
- Confirmed integer-cent total/change, insufficient cash rejection, bank zero-change/recorded-only settlement, complete stock prevalidation, pre-sale COGS snapshot/unknown preservation, review/key binding and atomic staged SQLite receipt/state persistence.
- Condition: manual request has no cash-received amount/change calculator; use voice path for received/change demonstration. Fullledger/profit/dayclose/invoice/returns/security/phone acceptance remain separate; prior broad financial block not cleared.
- Files changed: new finance review memo; own current-state, tasks, decisions and handoffs append only. No product code or other brains changed.
- Tests: no fresh application tests or live mutations by Ruzivo. Evidence inspected and attributed: parent host181backend+independent tests passed; Runako114frontend/build passed; Chengetai focused voice QA report. Code/test arithmetic630total/1000received/370change verified by inspection.
- Next: parent verify actual runtime/APK and phone repeat-sale behavior; re-review if pricing/tender/commit/receipt/persistence semantics change. No statutory certification or full release signoff.

## 2026-11-01 — SPRINT90-CASH-REVIEW-002
- Reactivated from AGENTS, role, six brain files and latest assigned task/board/acceptance; prior handoff read. Scope app read-only, own finance memo and brain writes.
- APPROVE WITH CONDITIONS new manual and voice cash-change demo. Added dated addendum to docs/finance/review-DEMO-SALE-CASH-REVIEW-001.md; supersedes prior manual-no-change condition for current UI only, preserving history.
- Verified strict optional integer amount, server cash/bank validation before stock mutation, authoritative saved change, exact frontend cents/receipt checks, original frozen retry payload/config/key, exclude-none legacy fingerprint compatibility, real-file regression coverage by inspection.
- Legacy omitted/null received remains unknown, not proof exactcash; bank remains recorded tender, not settlement. Single-worker modest catalogue demo only; no fullledger/profit/dayclose approval or physicalphone claim.
- Evidence attributed: parent188 backend/acceptance passes and120 frontend passes before minor traceUI fix. No fresh application tests/live mutations by Ruzivo. Inspected relevant manual cash/replay/validation tests and code.
- Files changed: finance memo addendum; own current-state/tasks/decisions/handoffs append only. Next parent package/current runtime/phone evidence; re-review semantic changes.

## 2026-11-01 — CATALOGUE-VOICE-REVIEW-001
- Activation: latest AGENTS, role, six brain files, prior handoffs, assigned task, current demo acceptance and master-board checkpoints loaded. Scope app read-only; own docs/finance and brain writes only.
- APPROVE WITH CONDITIONS narrow catalogue-grounded voice proposals and explicit match confirmation. No new financially material posting bypass found in inspected source. Memo docs/finance/review-CATALOGUE-VOICE-REVIEW-001.md.
- Reviewed transcript-derived qty/slot coverage, known-ID and stock boundary, provider no-price authority, missingqty/unknown/incomplete nonactionability, strict defaultfalse approval gate, exact stored lines, UI explicitYes beforepayment, serverprice/change, legacyfalse fingerprint omission/replay.
- Conditions: singleworker modestinteger demo; actualphone hear/readback/Yes remains unverified; clientapproval flag is operator assertion, not authenticated speech proof. Provider matching not semantic guarantee; bank recordedonly. No fullledger/profit/dayclose expansion or approval.
- Tests: no new application runs/live/provider requests by Ruzivo. Parent reports215 broad backend plus18 independent confirmation tests,4 realprovider no-sale cases,136frontend passes. Relevant AI/API/client regressions inspected; results attributed.
- Files changed: new scoped finance memo, own current-state/tasks/decisions/handoffs append only. No product source/otherbrain edits. Next parent packagecurrentAPK and physicalproposal/Yes/payment/receipt/stock/history acceptance; re-review semantic changes.

## 2026-11-02 — STARTER-COGS-REVIEW-001 policy checkpoint
- Full latest activation context loaded; read-only product scope, own docs/finance+brain writes; previous handoff read. Dependency Hwaro implementation and Chengetai regression evidence.
- Approved illustrative USD unitcosts Coke1.00/Bread1.20/Sugar1.80/Milk0.90/Chips0.60/Soap1.50, not market/supplier facts. Initial Chips0.65 suggestion superseded in coordination by final0.60 cleanfixture; communicated finalvalues Hwaro/root.
- Required missing-only exactseedidentity update, preserve known non-nullinclzero/stock/prices/historicalCOGS, explicitdemo_seed audit qty0/noinvoice/payment/receipt fabrication, atomic/idempotent startup. Futurecost only; oldunknownsales remainunknown.
- Memo docs/finance/review-STARTER-COGS-REVIEW-001.md created. Final implementation review pending. No applicationtests/livemutations/sourceedits by Ruzivo.

## 2026-11-02 — STARTER-COGS-REVIEW-001 implementation review
- Reactivated from persisted task/handoff; ownfinance/brain writes only, productreadonly. Actualcode inspected: app.seed_demo_shop/_backfill_demo_costs, canonicalJSON, demo_seed enum, SQLite startuptransaction, authoredstartertests, frontendfallbackparity.
- APPROVE WITH CONDITIONS implementation: approvedsixvalues correct; fullshop+exactproductidentity/null-only guards and invoice/prioraudit skips preserve knownzero/knowncost/stock/prices/removedorcustomproducts; explicitdemo_seed qty0 audit noinvoice/payment; repeatedstartup idempotent; initializer never rewrites historicalsales/COGS/receipts/replaykeys. Future salecost snapshots continue existingbehavior.
- Evidence: authoredbackend fresh/legacy/reopen/knownzero/unknownreceipt/prices/identity/audit tests inspected; parent/QA running tests, no backendpass claimed by Ruzivo. Runako reports141frontend/build includingcanonicalparity passed, attributed. No own application/live/provider tests or productedits.
- Fileschanged: finance memo implementationaddendum; own current-state/tasks/decisions/handoffs append only. No otherbrains/productchanges. Conditions illustrativeassumptions disclosed, root/QA regression+saferuntimeactivation before delivery; no fullledger/retrospectiveprofit/physicalAPK approval.
- Next: parent record regression/runtimeevidence; re-review fixture/guard/audit/historicaltreatment changes. Handoff complete.
