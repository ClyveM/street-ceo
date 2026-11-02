# Chengetai — Tasks

## Assigned by Mutungamiri

### W1-CHENGETAI-001 — Test and quality gate foundation — completed 2026-10-30

- Scope: `tests/`, `infra/`, and CI configuration only.
- Read `AGENTS.md`, this role, all six brain files, `docs/architecture.md`, `docs/api-contracts.md`, `docs/product-requirements.md`, and `tasks/master-board.md` before coding.
- Establish the smallest runnable test harness and quality checks for the new backend foundation; add security/test conventions and CI configuration without adding product features.
- Do not modify specialist application code or another agent's brain. Flag missing contracts or unsafe assumptions in the handoff.
- Acceptance: checks run from a clean checkout, failures are actionable, and the handoff records exact commands/results.

#### Verified evidence

- Added `tests/run_checks.py`, `tests/test_contracts.py`, `tests/test_security.py`,
  `tests/README.md`, and `tests/__init__.py`.
- Added `infra/security-baseline.md` and `.github/workflows/quality.yml`.
- `python tests/run_checks.py`: PASS, 6 passed, 1 intentional dependency skip.
- `git diff --check`: PASS.
- Backend `pytest` not run locally: `pytest` and FastAPI are unavailable; CI
  installs `services/api/requirements.txt` before running `python -m pytest services/api`.

No tasks assigned yet. Initialized 2026-10-29.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W6-DEMO-QA-001 — completed verification, release blocked — 2026-10-31

- Direct explicit assignment: LAN, sale/stock, purchase/WAC, day-close, Muse, social/image, APK gates; no features.
- Evidence and re-entry: `infra/w6-demo-qa-001.md`.
- 131 service tests pass with explicit import paths; 89 frontend tests and production build pass. Default baseline/service commands fail. LAN functional checks pass in separate synthetic shop; image appearance/device/CI/durability not approved.

### Release gate refresh — 2026-10-31

- Backend default and explicit serial commands: PASS, 60/60 each; eight deprecation warnings; isolated `--basetemp` used to avoid concurrent pytest temp-root contention.
- Frontend: PASS, 91 tests and production build (73 modules).
- LAN smoke: PASS, health/readiness, WAC, sale retry/stock, day close, Muse, social draft/image all returned expected evidence.
- APK: PASS for fresh web copy, Capacitor sync, Gradle debug build, current bundle parity, package/permissions. Artifact hash recorded in current-state and handoff.
- Blockers: baseline command still FAILS on import-path plus local env-file policy; no CI run, signature-tool verification, ADB device, physical-phone checks, production auth, or durable persistence evidence.

## Assigned by Mutungamiri — 2026-11-01 — SQLITE-ASSESS-QA-001
Read-only independent SQLite demo assessment requested by Owner. Load AGENTS.md, role.md, six brain files, relevant docs and master board. Inspect tests, finance review and persistence coverage. Define minimum acceptance checks and realistic 90-minute sequence for online-only SQLite demo; distinguish storage migration from accounting correctness. No product changes, live writes/restarts or secret inspection. Permitted writes: own brain only, structured handoff.

### SQLITE-ASSESS-QA-001 completed 2026-11-01
Read-only assessment persisted in current-state and handoffs. No tests run or product changes; SQLite acceptance requires real-file restart/replay/rollback evidence.

## Assigned by Mutungamiri — 2026-11-01 — DEMO-APK-SQLITE-QA-001
Follow full AGENTS activation. Validate new connected SQLite/manual and Apo APK demo against docs/demo-mvp-acceptance.md; own tests/, infra/, CI, own brain writes only; product code read-only. Coordinate root/Hwaro/Runako with defects. Repair baseline runner root imports and environment policy without reading/deleting user secrets: allow ignored untracked local .env configuration, fail tracked or nonignored .env files; keep committed-secret scanning. Add meaningful regression where appropriate. Run normal service suite and frontend tests/build after owners stabilize; independent real-file restart/voice retry/rollback and trace redaction checks. Review native ASR/TTS lifecycle/races and frontend repeated wake/payment loops. Do not claim phone acceptance; adb reports no attached devices. Packaging root/Runako coordinates. Financial review remains scoped separate. No live reset/provider calls. Persist handoff verdict and exact tests; use escalation if sandbox host restriction stalls tests.

### DEMO-APK-SQLITE-QA-001 implementation checkpoint
Baseline8/8 and trace6/6 pass; independent QA7 acceptance root-host pass attributed. CI/tests updated. Normal suite/backend compatibility fixes and native lifecycle owner review pending. See handoffs.

### DEMO-APK-SQLITE-QA-001 software verification complete
Software scoped PASS with baseline8/trace6/voice28 fresh own results; root full181/Runakofrontend114 attributed. Structured report infra/demo-apk-sqlite-qa-001.md. APK/device acceptance remains open.

## Assigned by Mutungamiri — 2026-11-01 — SPRINT90-QA-002
90-minute improvement sprint authorized Owner. Full AGENTS activation. Own tests/infra/CI/own brain only, product read-only. Independently review exact manualamount/voice/traces UX/API additions and add acceptance regression if needed. Build practical repeatable demo launcher in infra (PowerShell) single known SQLite backend8001 with safe existinglistener checks (never killunknown), configurable LAN URL and explicit diagnostics; support APK-only download on separateport if safe, no automatic firewall/security changes or secretvalues output. Include repeatable phone acceptance checklist and verify script syntax/behavior nonmutating. No unrelated features. Root performs privileged network/Gradle/ASGI commands; no subagent escalation stalls. Track screenshot/device QA limits, do not fabricate. Persist handoff/checkpoints.

### SPRINT90-QA-002 milestone
Launcher syntax+5safe behavior tests pass; baseline13pass.3more independent SQLite/trace tests ready for root host. Voice uncertainty cross-flow gap reported. Actual launcher host/phone/package verification pending.

### SPRINT90-QA-002 source/review handoff ready
Safe launcher/helper/checklist,3new independent API tests,3PS+3APK tests and review fixes persisted; own baseline13/focused37 pass and launcher3 pass. Host suite/runtime/package and physical acceptance remain root/tester pending. Report infra/sprint90-qa-002.md.

### SPRINT90-QA-002 final targeted review PASS
Root190backend/14baseline and Runako122frontend/build80 attributed; fresh own trace8 and finalUI/manual10 pass. NullproviderUnknown/truncatedpartial/source and recovery reviewed. Host runtime/launcher/APK batch and physicalphone remain pending.

### SPRINT90-QA-002 final history/migration targeted source gate PASS
Fresh14focusedpass; source currentname/savedsnapshot/legacycash and exactknownnativeconfig migration reviewed. Root finalpackaging supersedes candidatehash; physicalphonepending.

### SPRINT90-QA-002 launcher reuse correction
CIM+validatednetstatunion ready;7launcherregressionsPASS,fullbaseline18PASS. Roothostreuse/downloadfinalhashpending.

### SPRINT90-QA-002 final software/package gate complete (hostattributed)
Finallauncherreuses30460, finalsignedAPK/downloadhash verified root; own8launcherregressionspass. Reportfinalhash5ff29235d0e5a81edcddb28c4215b513767a7ed6984fbd7c50d4ea585182e91a. Rootfinalbaselinererunpending; physicalphoneacceptancepending. No furtherchanges.

## Assigned by Mutungamiri — 2026-11-01 — PHONE-RECOVERY-QA-001
Fullactivation. Own tests/infra/CI+brain, productreadonly. Reviewactualphone screenshots paths usercontext, roottracesprove no recentAPIevents19:47/48 (latest18:51). Independent regressions for validHTTP tenderquestions+no mutations and frontenduncertainrecovery/liveconnectivity; screenshotClosewrap identified. Verify old/latestAPK hashes/addressmigration possibility, sameLANrequirement and appnavigatorOnlinefalseassumption. No assumption userfault; rootaskednetwork/buildasync. No live sales/resets/keychanges, no escalations. Review Runako fix, roothostcommands. Persist handoff with clearremainingphonecheck.

### PHONE-RECOVERY-QA-001 targetedsoftware QA complete
Freshclient/probe9pass,baseline20pass,launcher9pass; rootAPI22pass andRunako130frontend/build84 attributed. Report infra/phone-recovery-qa-001.md. Physicalretest/rootfinalartifact pending; connectioncauseunconfirmed.

### PHONE-RECOVERY-QA-001 finalsource/freshness gate PASS
Own24worker/probe/payment +9independentclient tests pass;10launchertrustregressions pass. Root22API /Runako132frontend/build84 attributed. Finalhostartifact/physicalphonepending.

## Assigned by Mutungamiri — 2026-11-01 — CATALOGUE-VOICE-QA-001
Follow fullactivation. Own tests/infra/CI+brain, appreadonly. Independently validate actualcatalogueMuse fallback proposals, explicitspokenmatchconfirmation enforcement, allitems coverage/ambiguity/noinventedqty/id, contextualmissingqty, paidlegacyfingerprint/reviewreplay. Prevent tests hittingrealMeta: ownhelpers injectresolverNone/fakes whereappropriate; Hwaro APItesthelpersownedAPI coordinate. Rootrealprovider smoke separate. ReviewfrontendYes/No/Cancel/missingqty/no per-sale click, framesnabo terminalonly, uncertaintypreservation and provenance/providertruth inUI/traces. Add targeted independentHTTP+client tests inownscope ifneeded, not implementationmirror. No liveposts/resets/escalations. Roothostpytest/package/restartoldbackendafterstable. Persist gate/handoff, phoneaccuracy remainsactualtest.

### CATALOGUE-VOICE-QA-001 targeted software gate PASS
Independentclient6/voice36freshpass; root215broad/provider4nosale attributed. Intentcontractblockerfixed; reportinfra/catalogue-voice-qa-001.md. Finalbackendactivation/APK/actualphonepending.

## Assigned by Mutungamiri — 2026-11-01 — COUNTER-POLISH-QA-001
Fullactivation. Own tests/infra/CI+brain, productreadonly. Ownerphoneverifiedworking sale; scopevisualcleanup andnextApo/Applecompletedreceipt dismiss/unifiedhandsfree. Review newRunako flow safeguards: wakecloseONLYcompleted, neverpendingtender/match/clarification/uncertain; sameutterance remainder notlost; oneenabledpreference allresponses; closingreceipt notturnoff; explicitPause respected, typingavailable, ASRpausedTTS/bkg. Compactreceipt authoritative amounts preserved, diagnosticsreachableProfile/details, no unsupportedfullrefund claims. Useactualprovidedphoto+existinglogo read-only. Add meaningful independentstate/wake regression ifneeded, no implementationmirroring/layoutassertsnapshots. Nobackendchanges/livesales/resets/escalations. Finalsource/test gate beforeAPK; physicalnewlayout/repeatcycle requiresretest. Persist handoff.

### COUNTER-POLISH-QA-001 — completed software/source gate
PASS: own 6 independent +17 focused tests; root final frontend140 and baseline21 passed. Final artifact/hash and scope limits recorded in infra/counter-polish-qa-001.md. New physical layout/repeat retest remains; no active QA sessions.


## Assigned by Mutungamiri — 2026-11-02 STARTER-COGS-QA-001
Fullactivation protocol; scope tests/infra and ownbrain; productreadonly. Independently review/test starter demo costs JSON/backendseed/frontendparity. Ensure existingexactstarter missing-only costfill, knownzero/custom/provenancepreserved, no historicalCOGS modification, no prices/stock mutation, startuptransaction rollback/reopen durability and future sale COGS snapshot. Set STOREmemory/SEEDfalse beforeimports; tempDBtests only. No livecalls/restart/escalations; send root checks needed. Persist finalhandoff.

### STARTER-COGS-QA-001 — completed targeted software gate PASS
10 independent +3 owner Python cases passed; frontend canonical parity1 passed. See infra/starter-cogs-qa-001.md and handoff. Root retains integrated/live/APK verification.



## Assigned by Mutungamiri — 2026-11-02 MUSE-OUTAGE-QA-001
Fullactivation protocol tests/infra ownbrain productreadonly. Ungwaru confirmed8sresolver cutoff while actualMuse completed19.5s; defaultfix24s/max25 underfrontend30. Independently validate boundeddeadline/no retry/twoinflight untilcompletion and honesttimeout/busy/config/errorfallback with0actionablelines. No Applewordstrip or unknownproduct guesses; originalphrase ambiguous remainsclarification. No live/provider/escalation/restart. Persist handoff; rootowns hostsmoke/runtime.

### MUSE-OUTAGE-QA-001 completed — targeted PASS
Independent5+owner16 passed0.53s; root34 passed1.71s attributed. Source/capacity/framing review and handoff infra/muse-outage-qa-001.md. Root activation/provider/phone checks remain separate.



## Assigned by Mutungamiri — 2026-11-02 FAST-COUNTER-QA-001
Fullactivation protocol tests/infra ownbrain only; productreadonly. Ungwaru exactalias+observedboundedASRtail localproposals mandatoryYes/allitems/exactqty/nocataloguenoisecollision; providerfalse provenance,6sMusefallback,reusedclient. Runako nativeexclusiveimmersivenavigationbar+stableinsets/IME/lifecycle andwebsource label/handsfreepreservation. Testfastpath/no unknownstripping/partial/confirmation/replay/concurrency andnativeinset policymeaningfully; roothostbuild/ASGIsmoke. No liveprovider/restart/escalations. ReadofficialAndroidguide primary. ADBnodeviceavailable perroot. Persistchecks/limitations/handoff.

FAST-COUNTER-QA-001 temporaryscopeextension: services/api/test_catalogue_voice.py only, to setallow_local_proposals=False on syntheticprovider contract fixtures when needed; no APIproductsourcechanges. Retain/add separateactualdefaultfastpath HTTPconfirmguard coverage in tests/. Rootlogsonewriter.

### FAST-COUNTER-QA-001 checkpoint — offline/source PASS
45Python+12independent client tests passed; root HTTP added test pending execution. Native source policy reviewed, physical device not claimed. See infra/fast-counter-qa-001.md.


### FAST-COUNTER-QA-001 completed — software/integration PASS
Root132integrated14.90s includes newHTTP; nativeassemblePASS; own45Python/12client/diffPASS. Final report/handoff persisted, rootartifact/device acceptance separate.


FAST-COUNTER-QA-001 urgent infra follow-up complete: narrow corroboratedPID0 handling+3newregressionmethods; launcher13passed13.47s/diffPASS. Actual rootcause unconfirmed, restoration timing ambiguous; report/handoff distinguish observations from hypothesis. No active QA processes.



## Assigned by Mutungamiri — 2026-11-02 REPO-CLEAN-QA-001
Fullactivation tests/infra/.github +ownbrain scope. Userrepo cleanup+freshcloneease. Auditgeneratedfiles/secrets/logs/attachments/lockfiles/Androidwrapper assets andcleanclonequickstart dependencies; sendrootignoremanifest. CoordinateRunako+Hwaro separatesignoredteamUI/API defaultStreetCEObuild. CI shouldvalidateclean trackedexport withnogitignoredfilesdependency; preserve meaningfulshoptests, excludeonlyteamtestsfromrepo (localkept). Addstraightforwardstartdev/bootstrap scripts ininfra ifhelpful crossplatform Python+venv/npm prerequisites; rootwritesREADME/docs/envexample. No deletinglocaldata/secrets, no gitstage/commit/push byagents. QA allfeatures/security, setupfromcleanGitindexexport afterrootstage; no live/restart/escalation. Persisthandoff.

### REPO-CLEAN-QA-001 checkpoint — local gates PASS, export pending
Bootstrap+CI+manifest/security audit implemented; baseline29 and focused9pass. Rootstage/export/install/buildtest pending. Report infra/repo-clean-qa-001.md.


### REPO-CLEAN-QA-001 completed — final source/cleanexport PASS
Root361source manifest+freshinstall+255pytest29baseline117web65build/freshSQLiteAPI pass, attributed. Own29baseline/focusedgates pass. Handoff/report persisted. Commitpush/remoteCI root; no active QA tasks.



## Assigned by Mutungamiri — 2026-11-02 QUANTITY-REPLY-QA-001
Fullactivation tests/infra ownbrain productreadonly. Runako ASRfinal/auto-rearm lifecycle, native speechReady event+truthfulmodal actualstate; Hwaro safe structuredmissingqtytarget+scopedbarequantity. Verify bareone/1 noApo exacttarget, noisymodelqualifiedtarget, no guessedmultibasket/unknowns/crossshop/staleID/paidmutation, canonicalconfirmationrequired. IndependentfakeASRreadiness/TTS/finalpause/resume/duplicateguardtests andAPIacceptance. RoothostASGI/build/provider/liveunpaidonly. No liveoriginalrequestreplay/restart/escalation. Persisthandoff.

### QUANTITY-REPLY-QA-001 checkpoint — source/offline PASS
39Python/14Nodepass; background/lateReady findingsfixed byowner. NewHTTP/CI ready rootintegration. Report infra/quantity-reply-qa-001.md; no phonecauseclaim.


### QUANTITY-REPLY-QA-001 completed — final source/software PASS
Root310Python/29baseline/owner122frontend pass, own39Python14Node pass. Final report/handoff persisted; root package/unpaidprobe/physicalphone acceptance separate. No activeQA processes.



## Assigned by Mutungamiri — 2026-11-02 REPORTS-CLOSE-QA-001
Fullactivation tests/infra/.github ownbrain readonlyproduct. Readacceptance docs/reports-and-close-acceptance.md andRuzivopolicy-REPORTS-CLOSE-REVIEW-001.md. Independentlyvalidate reports datesinclusive/shopTZ/monthboundary/presets1/20/90, historicalmixedrevenueunknown notcurrentprice andfutureSnapshots/COGSunknown, stockUndo notfinancialrefund. Cashclosing singlebaseline/zero/unknown/countedsalesTOTALvsamounttendered/allactualmovements/cutoffcarry/priorvariance/banknull, stale-preview/post-closeactivity/idempotency/reopen. Voice endmyday idleonly beforeparser, pending/uncertainprotected, allreplieshandsfree, confirmation/noautobalance, optionalmonthendstockcountSkip. Productsource readonly roothostASGI/nativebuild/liveREADONLY. AddnewindependentsCIexplicitcommandsifneeded. No livefinancialposts/provider/restart/escalations. Persisthandoff+financialreviewneeds.

### REPORTS-CLOSE-QA-001 checkpoint — independent PASS
Pure11+client12combined pass;2HTTP rootrunready/CI updated. Report infra/reports-close-qa-001.md. Await rootintegration andRuzivostableimplementationreview, no livefinancialposts.


### REPORTS-CLOSE-QA-001 completed — final source/software PASS
Finalroot333postguardPython/129frontend/12client/DOMPASS, own13purePASS. Ruzivofinalapprovewithconditions. Report/handoffpersisted, rootruntimeAPK/phone acceptance separate. No activeQA processes.



## Assigned by Mutungamiri — 2026-11-02 NAPO-RETRY-QA-001
Fullactivation tests/infra/CI ownbrain readonlyproduct. Independentterminalnapple vsinternalapple safeguards, fullframedretryduringclarification vsbareone/Yes/Cash, splitASRutterances/framing/ownTTS/background/uncertainguards. Roottraces rawApple..napple whilequestion, latestreportsdidnotchangeNapomatcher. No actualphonecauseguarantee. Testrealhelpers andDOMfakeASR ifneeded; no live financial/provider/restart/escalation. Rootnativepackage/readonlyAPI. Persisthandoff.

### NAPO-RETRY-QA-001 completed — targeted source/software PASS
Own8+ownerfocused43pass; broader57pass453.1658ms. Report infra/napo-retry-qa-001.md andhandoffpersisted. Rootartifact/phone acceptance separate, no activeQA processes.


## Assigned by Mutungamiri — 2026-11-02 TERMINAL-MUSE-QA-001
After Hwaro TERMINAL-MUSE-001 handoff, independently review and test console tracing. Read activation protocol/own role/six brains/docs/master board. Read-only implementation review services/ai/console_trace.py,tracing.py, services/api/sqlite_store.py, infra/dev.py,.env.example; test ownership tests/ allowed if needed. Verify real isolated SQLite API local/mocked provider paths, named basket, truthful provider vs accepted proposal and timing, off/normal/detail, ANSI/credentials/PII sanitization and bounded payload, persistent logs unaffected, console failure cannot change outcomes. No real provider/live data mutation/restart. Root will notify when ready. Persist QA handoff.

### TERMINAL-MUSE-QA-001 completed — PASS
37 final affected tests passed7.72s; 5 independent acceptance cases, oversized honest-display finding fixed/retested. See own handoff. Runtime activation root; no active QA processes.

## Assigned by Mutungamiri — 2026-11-02 DEMO-MUSE-WAIT-QA-001
Review Ungwaru waitbudget24s/catalogueHTTP25s vs existing frontend30s request. Supersedes6s acceptance byOwnerexplicitinstruction. Readonlyimplementation, own focused tests if needed. Verify no local slowdown/retries/financialbehavior changes, failure/timeouts still nonactionable, max2inflight; focusedAI+APIcatalogue+terminal tracing regressions, tempDB blankcredentials only. Wait for implementation handoff before tests. Activationprotocol and persistent QA handoff required. No cloud/liveAPI mutation/restart.

### DEMO-MUSE-WAIT-QA-001 completed — PASS
117 focused tests passed4.10s;24sresolver/25scatalogueHTTP vs30sfrontend, generalMuse20s and local/safety guards preserved. Handoff persisted; activation root, no activeQA processes.

## Assigned by Mutungamiri — 2026-11-02 SHORT-VOICE-TRAIN-QA-001
Independent QA of Runako shortspoken Cashorbank/Salesaved +Profile5Naposamples and allsavedaliases persisted/migrated/reflectedSell. Tests/ scope; readonlyfrontendimplementation. Loadactivationprotocol/role6brains docsboard. Verify command terminalonly aliases and longestmatch, conflicts/badinput/dedup/cancel/reset/storagefailure, no productwordloss/partial basket/sale duringtraining, sharedhandsfree/TTSrecover. Sourcefocusedtests+type/build asappropriate, mockASRDOM iffeasible. Waitfinalsourcehandoff. No liveAPI/provider/nativefinancialmutation. PersistQAhand off. Rootgo packaging afterwards.

### SHORT-VOICE-TRAIN-QA-001 completed — PASS
24focused tests +builtDOM5sample/rearm/duplicate/cancel/storagefail/reload/reset/zeroPOSTpass. Owner137frontend/build attributed. Handoff persisted, rootpackaging/physical separate; no activeQA processes.

## Assigned by Mutungamiri — 2026-11-02 MUSE-INSIGHT-QA-001
Independent QA UngwaruAI exactbusinessschema and HwaroAPI repository top-product/simple sales responses. Readactivationownrole6brains docsboard. Test unitsvsrevenue/ties/zerosales/unknownlabels/dateTZ/uniquereceipts/currentcataloguevsreceipts, strictshape/citations/honestprovenance. Existingprofit semantics unchanged; non-simpleMuse route no hallucinatedproductanswers. SourceAPI+AIreadonly, tests/ scope permitted. FullAPI+AIaffectedtests iffeasible blankkeys/tempDB; no realcloud/livefinancialmutations. Waitsourcefreeze; persisthandoff.

### MUSE-INSIGHT-QA-001 completed — PASS
245broadaffected tests passed19.06s; finalguard22passed2.12s includes6independentcases. Source/schema/provenance reviewPASS; handoffpersisted. Runtime/cloudsmoke root only; no activeQA processes.

## Assigned by Mutungamiri — 2026-11-02 REPORTS-POLISH-QA-001
Independent test/visual review Runako reportredesign at320/390/desktop, realbuiltDOM mockAPI no livefinancialposts. Preserve presets/month/custom inclusivefilterrequest+activestate/datevalidation, products qty/revenueunknown vs0/warnings visible, loadedreportnotwronglabel, cashbanktotals existingparse, error/empty/retry, optionalmonthcount/Skip. EndDayCSS unaffected. Tests/ ownscope; readonlyfrontendimplementation. Need screenshotartifacts localignored for rootvisualreview, namedpath. Followactivation6brains docsboard; awaitfrozenbuild finaltest; packaging aftergate. No cloud/livefinancialmutation. Persisthandoff.

### REPORTS-POLISH-QA-001 completed — PASS
FinalbuiltDOM320/390/1280/filter/error/empty/incomplete/optionalSkip/EndDayCSSpass; screenshotsdata/qa-reports-polish-20261102. Own5clientpass431.71ms; owner141/buildattributed. Handoffpersisted; no activeQA processes, rootvisualreview/package/phone separate.

REPORTS-POLISH-QA-001 finalrootvisualfollowup completedPASS: shop-PXeLLDPl.js/CSSBV9CAqqX newDOM fullchecks +Reportsheader/Todaypreservation/lastrowaccess verified; screenshotsupdated, no activeQA.

## Assigned by Mutungamiri — 2026-11-02 STOCK-COUNT-HISTORY-QA-001
IndependentQA APIlistshopisolation/newest/reopen no mutation; frontend standaloneStart/history/details/draftresume/confirmedreadonly/emptyerror/loading/safeconfirm/blanknotzero. Tests/ scope readonlyimplementation. ActualbuiltDOM mockAPI320390 screenshotroot; Start→draftreview→explicitackconfirm→historyrefresh, stale/uncertainguard, existingReports/EndDay countlinksleadnewpage. No livefinancialmutation/cloud. Activation6brains/docsboard; waitfrozenbuild; persisthandoff. Packagingrootgoaftergate.

### STOCK-COUNT-HISTORY-QA-001 completed — PASS
22APItests6.28s +actualDOM320390 Start/history/draftack/confirm/reopenreadonly/503recoveryglobalguards/Reportslink/error/blanknotzero pass. Topviewports data/qa-stock-count-history-20261102/history-top-{390,320}.png. Handoffpersisted, packaginggo, no activeQA.

## Assigned by Mutungamiri — 2026-11-02 PRODUCT-PROFIT-QA-001
IndependentQA Hwaro exactread-onlysummary/productgrossprofit/margin andRunakoSales/Profit mobileUI. Followactivation6brains/docsboard. Tests/ ownscope readonlyimplementation. Ruzivopolicy grossprofitmicros exactrevenue*10000-cogs completeonly; marginbps DecimalROUND_HALF_UP signednullzerorevenue/unknown, nosumrounded/noexpensealloc. Tests complete/mixedunknowncost+revenue/legacy/costedloss/zerorevenue/zeroSales/currentcatalogueedits/TZ/dedup/stockUndo unchanged, parsergrossprofitvalidation. BuiltDOM320390views/datefilters/loss/unknown/empty/error screenshotsroot, Sales/EndDayStockCountregressionsappropriate. No livefinancialmutation/cloud. Awaitsourcefreeze; finalfinance approval neededbeforeactivationpackaging. Persisthandoff.

### PRODUCT-PROFIT-QA-001 completed — PASS
46API2.17s/10client246.91ms/finalBfx1YKMZ+B8gz1mm9builtProfit+Sales/EndDayDOMpass;320390singlelinemargins/screensdata/qa-product-profit-20261102. Missingcostmetadata-omittedguardfixed/retested. Handoffpersisted noactiveQA; rootfinance/visual/packagego.

## Assigned by Mutungamiri — 2026-11-02 STOCK-TABLE-QA-001
Independent Stock UI clickabletable test320390 actualbuiltDOM/mockAPI screenshotsroot. Preserve Stockcounts/retailcost/purchase/imageactions, rowtapreadonly opensdetails, keyboardEnter/Space/Close focus, searchnameSKU/clear/empty, longproductnames/quantity/price nooverflow, lowstock visible, selecteddetails refreshed aftercataloguechanges, costmutation/disabled/demo guards. No API/mathchanges. Tests/ scope readonlyimplementation. Regress ReportsProfit/StockCount basicnavigation ifappropriate. Followactivation/persistbrainhandoff; finalbuildfreeze beforetests; rootpackagingaftervisualgate. No cloud/livefinancialmutations.

### STOCK-TABLE-QA-001 completed — PASS
13focused495.11ms +actualDOM320390/rowkeyboard/search/readonly/photo/costdraftackconfirm/currentrefresh/unknownlatch/demo guards pass. DuplicateReactkeys realbugfixednamespacesandONEeditorassertionspass finalBWNPadqH/DquULXt2. Screensdata/qa-stock-table-20261102. Handoffpersisted noactiveQA; packaginggoafterrootvisual.

## Assigned by Mutungamiri — 2026-11-02 SALES-HISTORY-TABLE-QA-001
IndependentReadonlySalesHistorytable/receiptdetails APIamounts unchanged. Tests/ scope readonlyimplementation. Followactivation6brains/docsboard. MockactualDOM320390 table/datepaymenttotal/tapandkeyboard/focusclose, productsqty/total/tenderreceivedchange/legacycashmissing unknownvs0/banksettlementnote/snapshotlabelorcurrentfallback/renamed/deletedproducts/no currentpricereprice. Loading/error/empty/refresh stale recordclear; longlabels/largeamountswhole/pagebounds; currencycorrect. Assert0POST. RegressStock/Reportsnavappropriate. Awaitfrozenbuild; screenshotpathsroot; packagingaftervisualgate. No cloud/livefinancialmutation. Persisthandoff.

### SALES-HISTORY-TABLE-QA-001 completed — PASS
10client264.99ms+actualCWFztYnL/c83LHZFtDOM320390 receipttruth/snapshot/legacyunknownvs0/read-onlykeyboard/error/loading/empty/refreshstale-focus/0POSTpass. Screensdata/qa-sales-history-20261102. Handoffpersisted noactiveQA; rootvisual/package separate.

SALES-HISTORY-TABLE-QA-001 longreceiptfollowup resolvedPASS: finalB9k06aeq/CdW9NWd_ fullDOMrerun inclnatural7product320390headergeometry/titleClose96pxoffset+allfunctionalchecks. Screensreceipt-long-tap-{320,390}.png updated. NoactiveQA, readyrootvisual/package.

## Assigned by Mutungamiri — 2026-11-02 RETAIN-CAPTURE-EXPORT-QA-001
Multi-milestone independentQA. First RETAIN-BASKET backendfrozenHwaro59pass: newretained_lines/pendingslots/focusedclarification_of contextpersist100items, fullconfirmation/no partialpost/idempotency/forkguard. Scope tests/ readonlyimplementation. Review100items99known1unknown+multiplepending/missingqty/providerfail/restart/samekeyretry/differentkeyfork/exactremove/no accidentaldrop/pricestock guards. CoordinateRunako currentUIcontracts; finalDOM afterfreeze. Laterphotos/exportsCSVPDF/native andpaperdailybatchcontracts willfollow. No realshop/cloudfinancialcalls. Activationown6brains/docsboard/newacceptance, persistmilestoneQA. PDFvalidation appliesPDFskill markerbeforeactualtestPDFcreate, renderPNGreview (rootreadskillruntimepath providedlater). Do not editAPI/AI/frontend source. Keep QAunderseparatefilenameownbrain.

## 2026-11-02 RETAIN-CAPTURE-EXPORT-QA-001 backend milestone — blockers under repair
Activated acceptance/docs/own role+brain context, read-only implementation scope. Added tests/retained_basket_acceptance.py seven independent isolated SQLite/fakeprovider cases. Latest 5 passed/2 failed1.67s: deleted retained product/out-of-stock 409, foreign/missing context, multiitem/noisy focused responses preserve basket PASS. Blockers sent root/Hwaro: explicit 'remove this item' does not remove active slot; focused 'one bread and' drops trailing conjunction and offers full confirmation. Initial deletion/stock failures were stale test record reference across transaction reload; fixture corrected and both PASS, not implementation defects. Owner five retained tests previously ran in combined run8passed4failed before fixture correction. No realshop/cloud or financial mutation; no active QA processes. Await owner correction/freeze then broader API gate; photos/export/paper milestones pending UI/contracts. No final release gate yet.

### 2026-11-02 RETAIN-CAPTURE-EXPORT-QA-001 retained backend final milestone — PASS
Hwaro corrected both reported blockers: exact remove item/remove this item consumes only active slot; trailing conjunction retains unresolved context. Independent tests/retained_basket_acceptance.py now9cases including final-slot removal requires complete remaining-basketYes, retry stable/fork409, resolvedreview subset409/currentstock409. Final34affected tests passed6.83s: own9 + services/api/test_retained_basket.py + test_catalogue_voice.py + test_sqlite_store.py + services/voice/test_provider_tracing.py. All isolated tempSQLite, blankcloudcredentials, no live API/financial writes. Earlier initial6pass2fail milestone superseded. Retained backend scoped gate PASS; current task remains WIP for frontend/photos/CSV/PDF/native/paper contracts and actualbuiltDOM. No activeQA process. Root notified; implementation stays read-only.

## Assigned by Mutungamiri — 2026-11-02 PAPER-DAILY-QA-001
Hwaro PAPER-DAILY-API-001+STORED-PHOTOS backendmilestone34focusedpass3.83s sourcefreezing; independenttests/readonlysource+ownbrains. Reviewpolicy docs/finance/policy-PAPER-DAILY-REVIEW-001.md/HTTPcontractservices/api/PAPER_SALES_CONTRACT.md. Syntheticimages/fakeOCR only no livepost/userimagecloud. Verifyreviewno stockchange;todayopenonly/cashbankexact/nullableunitprice3for100/unknownqtypricemustreview/new-onlydeclarations+source/canonicaldup/currentstock/day/countbaselines/all-or-none; exactretry/no double deduct/restart; GETrecovery/lostconfirm; scope/imagebounded/private/no rawimage trace; countsindividualvsdaily; reportproduct/revenue/COGSunknownprofit/Today/Muse/cashclose/history onceonly; storedphotoindex/content scoped/getrestart bytes. BroadaffectedAPI+AI testsasappropriate. UIpaper/export/voicephotoDOM afterRunakofreeze, actualPDFartifactmarker/render stillpending. FinancialRuzivobackendreviewactive. Persistmilestones/handoff, no implementationwrites.

## 2026-11-02 RETAIN-CAPTURE-EXPORT-QA-001 / PAPER-DAILY-QA-001 final scoped software gate — PASS
Final frozen integrated app CvX88Bde.js /8Qthzhh1.css CAPTURE-SHARE-001 API8001. Owner171frontendPASS962ms attributed. Own final actualDOM tests:
- tests/paper_daily.dom.py PASS5.03s: syntheticPNGupload→editableOCR3units/1.00 mixedprices (unitnull), explicitcash0.40/bank0.60; save-review doesnotconfirm; threeackgate; 320390bounds. Confirmation503 locksnav/newimport/reconfirm, originalGETconfirmed correctversion recoversreadonly withoutsecondPOST; wrongversionconfirmed BEFOREfill doesnotshowsuccess. Originalretrycodedstale+verifiedsamebatchnonconfirmedGET offersReviewagain; staleoffer→laterconfirmedmismatch clearsoffer/stayslocked. Freshstale reoffers; explicitclickwritesoldkey/versiontombstone, samebatchfreshreview resetsallacks. Screensdata/qa-capture-integrated/paper-reviewed-{390,320}.png +paper-confirmed-320.png. Rootviewed320recorded.
- tests/retained_capture.dom.py PASS4.93s: actualnativefakeASR saved99known+1unknown; restoreResume blocksmanualReview/nav; focusedProduct99 lost503 leavespersistentattempt; reloadResume/spokenRetry reusesEXACTkey/body→100fullreview; spokenYes THENmissing-tenderquestion/shortCashorbank, nofinancialtenderpost. Manual/voicebasket storedphoto fromprivateindex+checksumcontent appearsafterreload; other99missingphotos donotblock. ExplicitDiscard and malformedcheckpointDiscard verifyclear. Screenssale-photos-{390,320}.png. FakeASR isnotphysicalacousticproof. Focusedmissing_tendermock contract andoldvisiblepromptassumptions correctedtestonly, notproductdefect.
- tests/capture_export.dom.py PASS3.69s: actualCSV/PDFnativebridge arguments, selectedUSD/period, browserpopupfinalembeddedbundledPNGdecodes, actualpopupPDFcreated,320390bounds, failedrefreshhidesexportbuttons, zeroPOST/noJSerrors. FinalremainingtestwaitwasoldaccessibleRefreshlocator (nowRefreshsalesreport), NOTprint/screenshot/producthang. Earlierphase1networklogo readiness concern supersededfinalembeddedlogoPASSED. ActualpopupPDFdata/qa-capture-export/output/pdf/street-ceo-sales-review.pdf Popplerbrowser-page-1.png visuallyinspectedcleanlogo/unknownsavedrevenue/grossnotes/countnounits/Page1. Nativebridge ismock; nativePdfDocument/physicalshare notproven.
- tests/capture_export_client.mjs5PASS204.48ms: CSVformula/controlwhitespace/quotenewlineescape; HTMLescape; exactnegative1micro; selectedZAR/period/source; unknowncostzeroRevenueundefined; dailySummaryseparatecustomer0count; sharedpercentageUnknownnocurrency/knownpercent. Sameactualhelper100productPDF8A4pages allPopplerPNGs visuallyclean aftertypedunitfix/Page1..8; markerinvokedexactlyoncebeforefirstPDFauthoring, neveragain. TestPDFs ignored operationalartifacts, notuserdeliverables.
Backend finalbroad162PASS21.32s inclservicesAPI+own5paper/9retained. Paper5independent actualSQLite_save failure503 rollsbackstock/audit/idempotency/review; reopenedretryonce; canonicalignoresnullableunitprice/tenderallocation; name/SKU/quantitydrift409. Owner6paperalsoPASS. Ownoldsqlite_demo_acceptance mixedquantity expectation updated pernewslots: activeCoke allowed ONLYwithbothpendingcaptured/noactionablelines; bareone retainsCoke+unicornpending; partialcommit409/stock18/historyempty. Focused1PASS0.90s. Rootfull329rerunpending afterthat obsoleteexpectationfix; priorroot328pass1oldexpectationfail29.93s attributed.
Source/security review: nativeplugin restrictedcanonicalcache report-exports FileProvider nonexported/read-onlytemporarygrant/ClipData/typeCSVorPDF/explicitchooser/boundedname,size,rows,pages/noarbitraryURLpath. Photoindex/content scope+ETag/hash guards andlocalpreviewgeneration win reviewed; actualbasicstoredphotoreload/noimagesnonblocking DOMverified, localrace notseparatelysimulated. OCR25syntheticfake-providerPASS0.27s decoded5MiB16MPsingleframe/strictschema/unknownnulls/noinference/noautoretry/bounded2worker24s/binarytraceomission. Rootsyntheticimageproviderconnectivity separate; no realcloud/userimage byQA.
Allnewfilesunder tests/ andownbrain, implementationread-only. No liveAPI/DB/financialmutation/restart/Gitwrites byQA. NoactiveQAprocesses. FinaltargetedsoftwaregatePASS; rootfullsuite/activation/packaging/signature/download/physicalphoneacceptance separate. Ruzivofinalfinancialsourceconditions+evidence sent; overallfinancialreviewrootcoordinates. Remaining actualphonehandwritingaccuracy/systemshare/photo/cycle acceptance cannotbeinferredfrommocks/build.

## Assigned by Mutungamiri — 2026-11-03 SEED-IMAGES-QA-001
Chengetai owns tests/ and infra/ independent QA of Hwaro SEED-IMAGES-001. Verify six canonical starter products have valid bundled PNG image metadata/content via normal endpoints on fresh memory and SQLite; SQLite restart/idempotent seed preserves image identity and uploaded replacements, unrelated shops/products untouched, stock/prices/costs/history unchanged. Fresh tracked-source assets available without network/developer data. Wait for Hwaro handoff before final tests. No live DB edits/restarts. Persist own handoff. Root coordinates docs.

## 2026-11-03 SEED-IMAGES-QA-001 — PASS
- Activation: AGENTS, role, all six brain files/current assigned task and current demo/SQLite docs read; implementation read-only except root-authorized temporary services/api/test_*.py expectation adjustment. Own tests/, infra/, CI and brain scope respected. No live API/database writes or restarts.
- Added tests/test_seed_product_images.py eight independent cases: memory+SQLite all six genuine 512px PNG contents via ordinary image index/metadata/private content endpoints; hashes/sizes/ETag/scope and local PNG/SVG source presence; idempotent seed; uploaded image preservation during missing-only SQLite backfill/reopen; full non-image shop record equality including sale receipt/cost audit/prices/decremented stock; renamed SKU/name/deleted product/renamed shop exclusions; seed-disabled empty state.
- Added six runtime PNG paths to infra/check_source_manifest.py REQUIRED and new regression file to existing .github/workflows/quality.yml backend test command. Runtime assets 104101 bytes total; no new dependency or cloud fetch. Root visually inspected illustrations separately.
- Focused independent+existing suite: 31 passed4.31s. First broad suite333passed/1obsolete test_paper_sales.py index expectation failed26.93s (assumed only uploaded photo). Strengthened expectation to exact six canonical product-ID coverage, five unchanged seed pictures plus latest uploaded replacement, full exact index after restart. Final full isolated services + tests/sqlite_demo_acceptance.py + new8: 334 passed27.90s.
- Isolation before import: STORE memory, SEED_DEMO0, LOCAL_TEAM_ENABLED0, blank LLAMA_API_KEY/MODEL/VISION_MODEL; temporary databases only data/qa-seed-images-* ignored. Sandbox Python stalled (terminated), elevated default temp path Windows permission denied; elevated explicit unique workspace basetemps passed. No product defect inferred from those tool/environment issues. No active test processes remain.
- Scoped source/software gate PASS. Root stages/commits/pushes assets, runs staged manifest gate, activates runtime and verifies live images separately. Remote CI and physical-phone acceptance not claimed. No APK rebuild required for backend-only bundled image seed through existing endpoints.
