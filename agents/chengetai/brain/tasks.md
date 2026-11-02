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
