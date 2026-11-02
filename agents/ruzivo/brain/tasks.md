# Ruzivo — Tasks

## Assigned by Mutungamiri

### W1-RUZIVO-001 — MVP accounting policy memo — completed 2026-10-30

- Scope: `docs/finance/` only.
- Read `AGENTS.md`, this role, all six brain files, `docs/accounting-rules.md`, `docs/product-requirements.md`, `docs/architecture.md`, and `tasks/master-board.md` before writing.
- Produce a concise policy memo for the MVP: sale revenue, returns, weighted-average stock cost, paid stock purchases, cash versus bank tender, expenses, owner drawings/injections, opening cash, daily close and incomplete-data warnings.
- Separate confirmed policy from assumptions and explicitly state that this is internal advisory guidance, not statutory certification.
- Do not edit implementation code or another agent's brain. Verengai will implement under this memo.
- Acceptance: dated memo with worked treatment for the demo flow and unresolved production/tax questions clearly marked; handoff records review notes.
- Evidence: `docs/finance/mvp-accounting-policy-2026-10-30.md`; repository check passed for all required sections, advisory disclaimer, and WAC treatment.

No tasks assigned yet. Initialized 2026-10-29.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W6-DEMO-FINANCE-REVIEW-001 — completed review 2026-10-31; remediation outstanding
- Direct assignment from Mutungamiri: immediately review sales, purchases, WAC, expenses and day-close.
- Evidence: docs/finance/review-W6-DEMO-FINANCE-REVIEW-001.md; fresh focused suite 28 passed. Verdict BLOCK; scoped accounting treatments approved subject to implementation corrections.

## Assigned by Mutungamiri — 2026-11-01 — DEMO-SALE-CASH-REVIEW-001
Follow full AGENTS activation. Read-only scoped financial review of SQLite-connected manual/voice sales MVP: catalogue prices, quantity/stock validation, tender, cash received/change, historical COGS preservation/retry. Inspect changed API/sqlite and frontend quickSale contract plus docs/demo-mvp-acceptance.md; parent full backend181passed and frontend114passed evidence. Do not expand to invoice/day-close/fullledger features deferred from demo. Give precise approve/conditional/block for sale/tender/change demonstration and any materially wrong behavior. Existing full finance signoff remains blocked separately. Own docs/finance + own brain writes only. No live mutations/secrets/source edits, no escalated tools (root runs checks if needed). Persist handoff promptly.

## 2026-11-01 — DEMO-SALE-CASH-REVIEW-001
- Loaded AGENTS, role, six brain files, current task/board, accounting rules and connected demo acceptance; confirmed read-only product scope, writes docs/finance and own brain only; prior handoff read.
- Completed scoped code review; verdict APPROVE WITH CONDITIONS for single-worker connected SQLite catalogue/manual sale and voice sale/tender/change/stock/history/retry demonstration. Memo: docs/finance/review-DEMO-SALE-CASH-REVIEW-001.md.
- Confirmed integer-cent total/change, insufficient cash rejection, bank zero-change/recorded-only settlement, complete stock prevalidation, pre-sale COGS snapshot/unknown preservation, review/key binding and atomic staged SQLite receipt/state persistence.
- Condition: manual request has no cash-received amount/change calculator; use voice path for received/change demonstration. Fullledger/profit/dayclose/invoice/returns/security/phone acceptance remain separate; prior broad financial block not cleared.
- Files changed: new finance review memo; own current-state, tasks, decisions and handoffs append only. No product code or other brains changed.
- Tests: no fresh application tests or live mutations by Ruzivo. Evidence inspected and attributed: parent host181backend+independent tests passed; Runako114frontend/build passed; Chengetai focused voice QA report. Code/test arithmetic630total/1000received/370change verified by inspection.
- Next: parent verify actual runtime/APK and phone repeat-sale behavior; re-review if pricing/tender/commit/receipt/persistence semantics change. No statutory certification or full release signoff.

## Assigned by Mutungamiri — 2026-11-01 — SPRINT90-CASH-REVIEW-002
Follow full activation; read-only app, own docs/finance + brain writes. Review new manual optional amount_received_cents integer validation, authoritative change, old omission compatibility, bank validation, replay fingerprint/restart; frontend exactcash and received/change receipt validation. Root integrated backend188passed and frontend120passed before minor traceUI fix. Previous condition manualdoesnotcalculatechange now superseded if code passes. Narrow sale/tender/cash review only, no unrelated fullledger expansion. No escalated/live commands. Persist scoped approve/conditions/block handoff promptly.

## 2026-11-01 — SPRINT90-CASH-REVIEW-002
- Reactivated from AGENTS, role, six brain files and latest assigned task/board/acceptance; prior handoff read. Scope app read-only, own finance memo and brain writes.
- APPROVE WITH CONDITIONS new manual and voice cash-change demo. Added dated addendum to docs/finance/review-DEMO-SALE-CASH-REVIEW-001.md; supersedes prior manual-no-change condition for current UI only, preserving history.
- Verified strict optional integer amount, server cash/bank validation before stock mutation, authoritative saved change, exact frontend cents/receipt checks, original frozen retry payload/config/key, exclude-none legacy fingerprint compatibility, real-file regression coverage by inspection.
- Legacy omitted/null received remains unknown, not proof exactcash; bank remains recorded tender, not settlement. Single-worker modest catalogue demo only; no fullledger/profit/dayclose approval or physicalphone claim.
- Evidence attributed: parent188 backend/acceptance passes and120 frontend passes before minor traceUI fix. No fresh application tests/live mutations by Ruzivo. Inspected relevant manual cash/replay/validation tests and code.
- Files changed: finance memo addendum; own current-state/tasks/decisions/handoffs append only. Next parent package/current runtime/phone evidence; re-review semantic changes.

## Assigned by Mutungamiri — 2026-11-01 — CATALOGUE-VOICE-REVIEW-001
FullAGENTS activation. Read-onlyfinancialcontrol reviewof catalogue-grounded Muse matching proposals + explicitspoken matchconfirmationbeforepayment; integerqty/catalogueIDs/serverprice boundary, mixedunknownnopartial, missingqtynotguessed, replay/legacyfingerprints. Own docsfinance+brain only. Rootbroad215passed and realprovider4no-sale cases correct, UI136passed. Existing accounting unchanged; no newfullledger/profitclaim. Lookfor financially material bypass andgive narrowapprove/conditions/block. No livecalls/escalations/sourceedits. Persist handoffpromptly.

## 2026-11-01 — CATALOGUE-VOICE-REVIEW-001
- Activation: latest AGENTS, role, six brain files, prior handoffs, assigned task, current demo acceptance and master-board checkpoints loaded. Scope app read-only; own docs/finance and brain writes only.
- APPROVE WITH CONDITIONS narrow catalogue-grounded voice proposals and explicit match confirmation. No new financially material posting bypass found in inspected source. Memo docs/finance/review-CATALOGUE-VOICE-REVIEW-001.md.
- Reviewed transcript-derived qty/slot coverage, known-ID and stock boundary, provider no-price authority, missingqty/unknown/incomplete nonactionability, strict defaultfalse approval gate, exact stored lines, UI explicitYes beforepayment, serverprice/change, legacyfalse fingerprint omission/replay.
- Conditions: singleworker modestinteger demo; actualphone hear/readback/Yes remains unverified; clientapproval flag is operator assertion, not authenticated speech proof. Provider matching not semantic guarantee; bank recordedonly. No fullledger/profit/dayclose expansion or approval.
- Tests: no new application runs/live/provider requests by Ruzivo. Parent reports215 broad backend plus18 independent confirmation tests,4 realprovider no-sale cases,136frontend passes. Relevant AI/API/client regressions inspected; results attributed.
- Files changed: new scoped finance memo, own current-state/tasks/decisions/handoffs append only. No product source/otherbrain edits. Next parent packagecurrentAPK and physicalproposal/Yes/payment/receipt/stock/history acceptance; re-review semantic changes.


## Assigned by Mutungamiri — 2026-11-02 STARTER-COGS-REVIEW-001
Review starter demo unit costs and missing-only backfill policy with Hwaro, ownership docs/finance and own brain. Load activation protocol. Provide explicit illustrative demo cost suggestions, ensure no invented historical COGS or known-cost overwrite; advisory review and handoff. No product edits.

## 2026-11-02 — STARTER-COGS-REVIEW-001 policy handoff
- Assignment: approve illustrative six startercosts and safe missing-only initialization treatment. Full current activation read; previous handoff confirmed. Scope own docsfinance/brain, productreadonly.
- Verdict APPROVE WITH CONDITIONS policy/design only: USD Coke1.00/Bread1.20/Sugar1.80/Milk0.90/Chips0.60/Soap1.50 (1000000/1200000/1800000/900000/600000/1500000micros). Synthetic demo assumptions, not researched market/supplier prices. Exact values communicated Hwaro/Runako/root.
- Hwaro intended guards confirmed: defaultdemo shopUUID/name/currency/timezone + productUUID/SKU/name/shopid, only nullcost; preserve knownzero/non-null, skipinvoice-linked or priorcost-audited deliberateunknown; qty0 demo_seed audit STARTER-COGS-001, no invoice/payment; atomic/idempotent startup, historicalCOGS/receipts/stock/prices unchanged. Design acceptable pending code/tests.
- Files changed: docs/finance/review-STARTER-COGS-REVIEW-001.md and own current-state/decisions/tasks/handoffs append only. No productcode/otherbrains changed.
- Tests: no applicationtests/live/provider/database mutations by Ruzivo. Reviewed current seed, pre-saleCOGS snapshot, missinghistoricalCOGS reportguard and startuptransaction by inspection. Implementation/regression evidence pending Hwaro/Chengetai; no fabricated pass or fullledger signoff.
- Next: Hwaro implement and Chengetai validate freshcost/missing-only/knownzero/audits/restart/historicalunknown invariants. Parent may reactivate Ruzivo to inspect stable actualcode/tests before final implementation approval; keep demoassumption disclosure with futureCOGS.

## 2026-11-02 — STARTER-COGS-REVIEW-001 implementation review
- Reactivated from persisted task/handoff; ownfinance/brain writes only, productreadonly. Actualcode inspected: app.seed_demo_shop/_backfill_demo_costs, canonicalJSON, demo_seed enum, SQLite startuptransaction, authoredstartertests, frontendfallbackparity.
- APPROVE WITH CONDITIONS implementation: approvedsixvalues correct; fullshop+exactproductidentity/null-only guards and invoice/prioraudit skips preserve knownzero/knowncost/stock/prices/removedorcustomproducts; explicitdemo_seed qty0 audit noinvoice/payment; repeatedstartup idempotent; initializer never rewrites historicalsales/COGS/receipts/replaykeys. Future salecost snapshots continue existingbehavior.
- Evidence: authoredbackend fresh/legacy/reopen/knownzero/unknownreceipt/prices/identity/audit tests inspected; parent/QA running tests, no backendpass claimed by Ruzivo. Runako reports141frontend/build includingcanonicalparity passed, attributed. No own application/live/provider tests or productedits.
- Fileschanged: finance memo implementationaddendum; own current-state/tasks/decisions/handoffs append only. No otherbrains/productchanges. Conditions illustrativeassumptions disclosed, root/QA regression+saferuntimeactivation before delivery; no fullledger/retrospectiveprofit/physicalAPK approval.
- Next: parent record regression/runtimeevidence; re-review fixture/guard/audit/historicaltreatment changes. Handoff complete.


## Assigned by Mutungamiri — 2026-11-02 REPORTS-CLOSE-REVIEW-001
Fullactivation docs/finance ownbrain advisory. Userwantsmonthly/productperiodreports+voiceEndmyday openingcash+cashsalesrecon countedonhanddiff,monthendoptionalstockcount. Reviewexistingopeningcalculation cumulativeallprioropening incorrectforperday; defineexplicitdailyopening/carryforwardunknownnotzero, registeredcashin/out/refunds/purchases/expenses, cashsalesnetcash(effectsale totalnotamounttendered), banknotverified/bankunknowncash-onlyclose, cashvariance sign, latestreceiptsfrozenatclose/lateactivityflag, idempotency,nodoubleopeningcarry. ReportsactualgrosssalesvsstockonlyUndo notfinancialrefund mustnotinventnetsales/profit. Sendpolicy toHwaro/Runakopromptly, reviewfinalimplwhenstable. No liveapps/financialpostings. Monthendstocktakeoptionalnotgate. Handoff.

## 2026-11-02 — REPORTS-CLOSE-REVIEW-001 policy handoff
- Activation current AGENTS/role/sixbrain/task/board/demo acceptance and prior financialhandoffs loaded. Scope docsfinance+ownbrain, productreadonly; prior handoff read. Dependencies Hwaroimplementation/RunakoUX/ChengetaiQA.
- Approved implementation policy in docs/finance/policy-REPORTS-CLOSE-REVIEW-001.md. Current _day_close_breakdown allprioropening sum/sameday omission/priortrade omission is confirmed source defect, not approved for reuse.
- Sent Hwaro/Runako/root authoritative rules: singlelatest openinganchor or priorCOUNTEDclose+subsequentnetactivity, preservepriorvariance warning, explicitzero allowed/noanchorunknown; cashsalesTOTAL nottendered, paidcashin/out/refunds/adjustments, stockUndo notrefund, banknull oncashonlyclose; variance=counted-expected, frozenasofsnapshot/stalepreviewconflict/idempotency/lateactivityvisible.
- Reports: inclusive shoplocal dates/presets1/20/90, savedgrossreceipts; futurelineprice+costsnapshots; legacySINGLELINE savedtotal/knownCOGS exactattributable, MULTILINE missinglinehistory unallocated notcurrentprices/pro-rata; unknownmargin staysunknown, stockUndo separate notnetfinancialsale. OptionalmonthendSTOCKcount notcashclosegate; explicitstockadjustaudit, nofakecash/revenue; historicalstocknotcurrentstock.
- Purchase valuationmicros mustnot silentlyfloor to paidtender; actualpaidminor preferred, legacyuncertainty disclosed/resolved, anyaggregate currencyrounding estimate explicitlylabelled/source/residual preserved.
- Fileschanged newfinancepolicymemo and own current-state/tasks/decisions/handoffs appendonly. No product/otherbrain changes. No tests/livecalls/postings by Ruzivo; source inspection only. Implementationapproval pending stablecode+rootQA evidence; fullledger/production notapproved.
- Next root free slot forQA, reactivate Ruzivo after implementation stable for exactrules/sourcecontrols review. Handoff complete.

## 2026-11-02 — REPORTS-CLOSE-REVIEW-001 actual-code checkpoint
- Read stable reports.py/cash_close.py, app/model routes, REPORTS_CASH_CLOSE_CONTRACT, ownerSQLite/reporttests and independentpolicytests; ownfinance/brainwrites/productreadonly. Priorhandoff loaded.
- SoleconfirmedBLOCKER: generic POSTcash-movements accepts NEWcashopening_balance bypassing confirmedopeningroute knownanchor/frozen safeguards. Rootagreed rejectnewcashopening there/directnewendpoint, preserve exactoldidempotentreplaysfirst; finalguard/regressionreviewfollowup required. No liveclosebeforeapproval.
- Otherinspected controls conform: singlelatestbalanceanchor/priorcountcarry/interveningcash/priorvariancewarnings; saleTOTALnotTendered; fractionalpurchaseunknownblocked; banknull cashonly; strictconfirmedcounts; staleversion/retry/frozenlatewarning; legacyALLcashcomponents correctedengine andcash/fulldoublecloseguard, legacybankestimateswarnednotapproved. Reports savedlinesnapshot/inclusiveUTC/localdates/legacyunknownamounts andstockUndo disclosure correct; optionalstockcountseparate.
- Policyclarification added: retrospective FIRSTmissingopening aftertrading explicitlydeclared/source/actor/confirm isallowed, notknownanchorreset nor derivedfromendcount.
- Changed financepolicyactualreviewaddendum andown current-state/tasks/decisions/handoffs only. No product/otherbrain edits. No application/live/provider/postingtests byRuzivo. QAattributes root329Python+12purepolicy+5clientpasses; notownruns. Physicalvoice/close notclaimed; fullledger/production separate.
- Next rootreactivateHwaro guard+regressions thenRuzivo finalreview; slotfreedforimplementation. AdditionalQA futurewithin-sameday movement cutoffquestion relayedroot as untestedfollowup, notaddedconfirmedblocker.

## 2026-11-02 — REPORTS-CLOSE-REVIEW-001 final implementation handoff
- Reactivated from task/priorcheckpoint; actual finalguard source read in app.py/cash_close.py plusowner/independentregressions. Scope productreadonly/docsfinance+ownbrainwrites, no livepostings.
- APPROVE WITH CONDITIONS newperiod/productreports+cash-onlyclose; soleconfirmedopeningbypassBLOCKER CLEARED. Genericroute exactoldreplayfirst, newcashopening409→explicitconfirmedendpoint, futureactualcash422; legacyfutureeffectiveevents excluded/warned untilactualtime andnotappliedsourceIDsbeforetime. FirstMISSINGopening retrospective explicitdeclaration allowed; knownanchor replacement forbidden.
- Priorreviewed controls retained: singleanchor/countedcarry/priorvariancewarning/saleTOTAL/paidcashcomponents/unknownpaymentguards/banknull/staleversion/frozenlate/replay; savedhistoricalpricescosts+unknownlegacyallocations; stockUndo notfinancialrefund; optionalstockcountseparate.
- Parentattributes15ownerreports/retailpasses includingfinalguards; earlier329Python predateslastguard, finalfullsuite stillrunning. Independentguardsource inspected. No ownapplication/live/provider/postingtests. Conditions rootfinalregression/runtimeAPK andphysicalphoneacceptance; legacybankestimates/fullledger/statutoryproduction notapproved.
- Fileschanged financepolicyfinaladdendum andown current-state/tasks/decisions/handoffs appendonly; no product/otherbrains. Next rootintegratefinalevidence+packaging; re-review financialsemanticschanges. Handoffcomplete.
