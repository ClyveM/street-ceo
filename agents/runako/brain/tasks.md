# Runako — Tasks

No tasks assigned yet. Initialized 2026-10-29.

### W3-VOICE-INPUT-001A — Browser microphone capture — assigned 2026-10-30

- Add a visible microphone/push-to-talk control in the web app.
- Capture audio with the browser MediaRecorder API and show listening, recorded,
  transcribing, confirmation, success, and failure states.
- Do not place provider keys in the browser. Hand off a bounded audio request to
  Hwaro's backend contract; keep text fallback available.
- Scope: `apps/web/` voice UI only. Add focused tests or a manual verification note.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W2-RUNAKO-001 — Mobile-first web shell and manual sale UI — implementation complete, build verification blocked 2026-10-30

- Scope: `apps/web/` excluding the offline layer owned by Fambai.
- Read AGENTS.md, this role, all six brain files, `docs/product-requirements.md`, `docs/architecture.md`, `docs/api-contracts.md`, and `tasks/master-board.md`.
- Build the first visible PWA slice: branded shell using the supplied Street CEO logo where appropriate, Today/Sell/Stock navigation, responsive mobile layout, product search/catalogue, manual sale basket, cash/bank action states, and clear loading/empty/error/offline placeholders. Keep API calls behind a small client boundary so Fambai can add sync without rewriting screens.
- Do not implement IndexedDB/service worker/sync or backend/finance/voice code. Use mock data only where the API is unavailable and label it as demo data in the UI.
- Acceptance: local dev command documented, responsive preview can be opened, manual sale flow is demonstrable against the W1 API shape, and accessibility basics are covered.

#### Extension: local Team Monitor (2026-10-30)

- Added within the same `apps/web/` ownership: six local agent lanes (Hwaro,
  Verengai, Dura, Runako, Fambai, Inzwi), task/status/changed-file/last-activity
  details, and a clearly labeled simulated typing preview.
- The monitor is a local mock model only; it does not claim to be a real
  line-by-line subagent stream. It is opened through the `Team` bottom-nav item.
- Verification: source inspection confirmed all six lanes and README guidance;
  npm build remains blocked by unavailable registry resolution in this session.

#### Extension: simulated 3D command room (2026-10-30)

- Added a CSS/HTML 3D command room with CTO desk, specialist desks, planner
  cards, and a shared wall board for task, commit, unit-test, and warning stats.
- Uses optional local `window.__STREET_CEO_TEAM_ACTIVITY__` data with a
  deterministic fallback. 2D Team Monitor remains directly accessible.
- UI and README explicitly state that the scene/activity is simulated and does
  not expose private agent thoughts or a true line-by-line generation stream.

#### User-requested extension — local Team Monitor

- Add a Team Monitor view within the same `apps/web/` scope. Show the six Wave 2 lanes, task/status, last activity, changed files, and a code-activity panel.
- The code activity panel must be clearly labeled simulated/demo activity; it must not imply access to hidden line-by-line model generation. Prefer workspace-derived activity when available, with a deterministic mock fallback for local preview.
- Document how to open the monitor locally and preserve the core sale UI.

#### User-requested extension — simulated 3D Team Room

- Add a dependency-light simulated 3D command-room view: CTO desk, specialist desks, adjacent planners, and a shared stats board.
- Display task/status/last activity per desk and board metrics for completed/active tasks, commits, total tests, passing tests, and warnings. Use real repository-derived values when available and deterministic preview data otherwise.
- Keep the existing 2D Team Monitor available as a fallback. Label the 3D room and simulated code activity clearly; never imply private agent thoughts or a true hidden-generation stream.

### W3-LIVE-TEAM-001B — Live Team Monitor client — complete 2026-10-30

- Scope: `apps/web/` excluding Fambai's offline layer.
- Replace the hardcoded Team Monitor snapshot with polling of the local activity endpoint when `VITE_TEAM_ACTIVITY_URL` is configured. Display a live/local badge, last refresh time, and an explicit unavailable state; use the current deterministic snapshot only as a clearly labelled fallback.
- Keep the 2D monitor and simulated 3D room, but feed both from the same typed live snapshot. Do not claim live agent private streams or line-by-line generation.
- Acceptance: polling updates agents/stats, endpoint failure falls back visibly, no API configuration keeps demo preview working, and the build passes.

- Implementation evidence: `src/teamActivity.ts` owns the typed snapshot,
  response validation, deterministic fallback, and endpoint client. `App.tsx`
  polls every 10 seconds and passes one snapshot/meta state to both Team views.
  Live/fallback status, last refresh, and endpoint errors are visible.
- Build evidence: `npm run build` passed; Vite transformed 21 modules and
  emitted the production bundle under `apps/web/dist/`.

### W3-VOICE-INPUT-001A — Browser microphone capture — complete 2026-10-30

- Added `VoiceCapture` to the Sell surface with browser `MediaRecorder`,
  push-to-talk controls, listening/transcribing/confirmation/success/failure
  states, and a text command fallback.
- Added `voiceClient` behind optional `VITE_VOICE_INPUT_URL`. No provider key
  or provider SDK is shipped in the browser; no undocumented default endpoint
  is assumed. The existing Hwaro sale client remains the only transaction
  writer.
- Build evidence: `npm run build` passed; Vite transformed 24 modules and
  emitted the production bundle.

### Priority wave — PWA install slice and tool entry points — complete 2026-10-30

- Added `manifest.webmanifest`, branded `icon.svg`, install metadata, service
  worker registration for the existing Fambai-owned worker, and an install
  prompt. No worker sale integration was changed.
- Added Today entry points and safe pending states for Social Update and
  Profitability Analysis; no undocumented tool endpoints were invented.
- Updated offline wording to describe local screen availability without
  claiming sale queue/sync behavior in Runako-owned code.
- Build evidence: `npm run build` passed; Vite transformed 26 modules and
  emitted manifest/icon assets plus the production bundle.

## Assigned by Mutungamiri

### 2026-10-31 — Final frontend checkpoint (supersedes earlier WIP notes)

- W3-ASK-MUSE-UI-001: UI implemented, including real typed request, loading,
  answer/missing-data/unavailable/error states, evidence period/coverage.
- Workbench 404 follow-up: implemented root normalization, actionable errors,
  retained drafts and explicit stored-only receipt semantics.
- W3-TEAM-CHAT-001: frontend implemented against Hwaro's dedicated member chat
  routes; live listener returned history 404 during QA, requiring backend update.
- W3-LIVE-DESK-STATUS-001: implemented exact SAST evidence timestamps, source
  label, independent board assignment/freshness, owned-path file filtering,
  and no-new-evidence state. No screen/typing claims.
- W4-PROJECT-OFFICE-UI-001: standalone office.html, multi-project/room planning,
  product/workstream UI, tasks/desks/chat/evidence views, and migration plan
  implemented. Only verified initial room adapter is connected; new room-scoped
  API integration/auth/persistence remains an explicitly documented next phase.
- W4-APK-FIRST-UI-001: completed custom install UI removal and native browser
  beforeinstallprompt suppression, preserving worker/manifest files.
- W4-REMOVE-TEAM-PAGE-001: completed shop nav/page/state/polling/UI removal;
  reusable office exists only in standalone entry.
- W4-MUSE-SHOP-ID-001: completed as previously recorded; valid overrides kept.
- W4-PRODUCT-IMAGES-UI-001: optional validated photo preview/upload, shared Social
  selection, image request/loading/retry/unavailable/export gating implemented.
  Real generated-image preview/download remains blocked by provider/output API.
- W4-SOCIAL-UI-001: selected-product/image inputs, verified source brief,
  loading/errors, manual copy and explicit local exports implemented. Actual AI
  text draft generation remains blocked by absent HTTP endpoint; not called done.
- Final evidence: npm run test:frontend **41 passed, 0 failed**; npm run build
  exit 0, **55 modules**, emitted shop and office entries. Latest handoff contains
  exact files, browser checks, blockers, and receiving-session instructions.

### W4-MUSE-SHOP-ID-001 — complete frontend slice, 2026-10-31

- Confirmed existing non-nil seeded ID from Hwaro/backend evidence; centralized
  default and preserved valid saved/environment overrides.
- Missing/nil/malformed IDs and missing/invalid backend URLs cannot reach the
  Muse request; correction UI and explicit demo choice provided.
- Evidence: 30 frontend tests passed; build passed, 47 modules and two entries.
- Backend listener seeding/provider readiness are not claimed by these frontend
  tests. Structured handoff records exact files and limits.

### 2026-10-30/31 — Current frontend assignments (in progress)

- W3-ASK-MUSE-UI-001: wire real Muse contract and visible honest response states;
  include follow-up Workbench 404 handling. Scope apps/web plus own brain.
- W3-TEAM-CHAT-001: each member desk opens history/task/status/action composer;
  coordinate the source-backed API with Hwaro; no invented replies/typing.
- W3-LIVE-DESK-STATUS-001: exact Last verified repository activity time,
  assignment separated from evidence freshness, honest no-new-evidence state.
- W4-PROJECT-OFFICE-UI-001: standalone reusable project office UI, project/room/
  workstream hierarchy, Street CEO preserved, incremental migration plan.
- Evidence milestone: 22 focused tests and production build (41 modules) passed
  before latest per-member API/standalone-office changes; final checks pending.

### TEST-MEMORY-001: summarize agreed React PWA frontend architecture — assigned 2026-10-29

- Description: read-only task. Load brain per AGENTS.md, read
  docs/architecture.md and docs/product-requirements.md, summarize the agreed
  frontend architecture. No code or shared-doc changes; write only to own brain.
- Dependencies: none.
- Status: complete (2026-10-29).
- Acceptance criteria: dated handoff in brain/handoffs.md; brain/current-state.md
  updated; task status recorded here; summary reported to Mutungamiri.
- Acceptance evidence (2026-10-29, TEST-MEMORY-001): read-only task, no code or
  shared-doc changes. Activation files loaded: AGENTS.md, role.md, all six brain
  files, docs/architecture.md, docs/product-requirements.md. Handoff entry dated
  2026-10-29 appended to brain/handoffs.md; brain/current-state.md updated;
  status marked complete here; summary reported to Mutungamiri in completion
  message.

### 2026-10-31 — W5-COSTS-INVOICES-UI-001 / mobile QA / demo audit

- Invoice upload/manual review/product matching/explicit confirmation and guided
  expense draft/review/confirm implemented and verified against local API.
- Catalogue cost display and invoice-based cost review implemented. Direct
  cost-only editing blocked by missing backend correction contract.
- W4-MOBILE-QA-FINAL-001: measured320/390/431 browser viewports, fixed overflow
  and photo target. APK checklist published; physical-device pass outstanding.
- W5-DEMO-READINESS-UI-001: audit/storyboard/video checklist published; local vs
  LAN mismatch isolated, positive synthetic costs/sale/profit checks recorded.
- W4-SOCIAL-UI-001/W4-PRODUCT-IMAGES-UI-001: newly verified text/image adapters
  integrated; actual text fallback timeout and image provider_not_configured.
- Final evidence:52 frontend tests passed,0 failed; production build exit0,
  60modules,shop and office entries. Full structured handoff has exact records,
  files, remaining contracts, release reviews and physical-phone requirements.

### 2026-10-31 — W6-REALTIME-OPS-MVP-UI

Urgent polling cut complete frontend slice. Existing team/activity only,5second
polling,15second snapshot freshness,6hour repository evidence age, server/receipt/
last-change times,11members/team filter and task/file/test/commit history.
58tests passed, build62modules/exit0; actual endpoint and320px browser QA passed.
Wider W6-REALTIME-OPS-UI-001 heartbeat/session source is not implemented by this
cut; verified backend/collector contract required. Exact files/URL in handoff.

### 2026-10-31 — W5-DATE-UI-001 complete (revised local timezone)

Today date/greeting follow browser local timezone/locale, refresh each minute
and on focus/visibility resume. Deterministic formatter/clock tests4passed,
build exit0/63modules. Exact files/evidence in latest structured handoff.

### 2026-10-31 — W5-COSTS-INVOICES-UI-001 finalization complete frontend slice

Verified current contracts; added direct cost-only draft/confirm/audit UI and
invoice source status/recovery. Existing single purchase receipt flow and all
seven expense categories/one-off/recurring periods retained and live verified.
Focused27passed; full91passed; productionbuild73modules/exit0. Latest handoff
has exact files, synthetic receipts and mobile/desktop evidence. OCR/durability
and Ruzivo/Chengetai reviews remain external limitations; no fake OCR claimed.

## Assigned by coordination — W6-APO-HANDSFREE-001 — 2026-10-31
Frontend slice implemented;98tests passed/build76modules. Parent handles APK, phone validation outstanding. Exact scope/evidence in handoffs.md.

## Assigned by coordination — W6-VOICE-ERROR-001 — 2026-10-31
Frontend error classification/recovery complete;11focused tests passed,build76modules. Parent APK/device check outstanding. Evidence in handoffs.md.

## Assigned by coordination — W6-VOICE-PROFILE-001 — 2026-10-31
Profile enrollment/Sell cleanup implemented;103tests passed/build77modules. Actual CORS fix belongs backend,parent restart/APK. Evidence handoffs.md.

## Assigned by Mutungamiri — 2026-11-01 — DEMO-APK-APO-001
Implement hands-free APK MVP in apps/web/ excluding offline modules and apps/android/ native source (explicit temporary CTO scope extension) plus own brain. Load activation protocol and current code. User requires saying Apo to start, products, sale and tender/change without per-sale button clicks; auto-arm foreground APK listening after OS microphone permission (OS prompt unavoidable); Napo completion remains supported. Voice payment answers must work without Apo if prompted, speak unknown product/not found and no sale, authoritative total/change, resume wake loop after responses, pause recognition during TTS and lifecycle. Keep manual sale/stock/history refreshed. Coordinate backend with Hwaro. Add meaningful tests and build. Do not package until root coordinates final backend/web state; do not edit API/AI/offline or other brains. Persist handoff; report physical-device limits honestly.

## DEMO-APK-APO-001 checkpoint — 2026-11-01
Frontend/native sources implemented;114frontend tests pass/build77modules. Root native compile/package and Chengetai targeted review pending. Physical-device acceptance open; see structured handoff.

## Assigned by Mutungamiri — 2026-11-01 — SPRINT90-UX-002
90-minute improvement sprint authorized Owner. Full AGENTS activation. Own apps/web excluding offline and apps/android native source temporary CTO extension + own brain. Improve visible MVP: clear foreground Apo listening/processing/payment/success/error states and visible latest receipt with server total,received,change; no per-sale buttons in voice flow. Manual cash amount+change UI against Hwaro contract. Add small recent-request investigation view Profile using new shop-scoped sanitized trace API, show correlation/time/status/input/result, explicit errors no fake fixtures. Fix actual voice recovery pitfalls, natural cash decimal/word forms safely (never guess ambiguous amounts), tests for repeat/error scenarios. Coordinate Hwaro contract early. Keep scope demo only, preserve currentwork. Run frontend tests/build; no subagent escalations; root host native package. No live reset. Persist handoff/checkpoints.

## SPRINT90-UX-002 — frontend implementation complete, 2026-11-01
120frontend tests pass, final build80modules/shop-BJ3ZpTSI.js, scoped diffcheckpass. Chengetai targeted source review clear. Root packaging and physical/render acceptance remain. See structured handoff.

SPRINT90-UX-002 integration follow-up: legitimate provider_called=null accepted and displayed Unknown.121tests/build80modules/shop-DdDVC_iF.js pass; root packaging next.

SPRINT90-UX-002 finalpartial trace repair: explicit bounded truncated prefix display;122tests/build80modules/shop-QyDfyL_X.js pass. Root packaging next.

SPRINT90-UX-002 savedhistory+knownnativeconnection upgrade complete:125frontendtests/build82modules explicit8001/shop-l6068vGv.js pass. Sourcefrozen; root finalpackaging and QA/deviceacceptance next.

## Assigned by Mutungamiri — 2026-11-01 — PHONE-RECOVERY-001
User supplied actualphone screenshots21:47/21:48: recognizedCoke, awaitingtender but uncertain Recoveroriginal, brokenClose wrap. Root currentUTC19:50, latestdefaultcommittraces18:51 (hourbefore). Screenshots5G noWiFi. FullAGENTS activation. Own web exceptoffline +Androidnative onlyifneeded +ownbrain. Fix closebuttonheader minwidth/nowrap/mobilelayout. Replace misleading navigatorOnline as shopreachable with realnonmutatingAPI readiness status/lastcheck/address and clear localLAN/connection guidance, no falseclaim5Gmustfailuniversally. Unknowncommitpreserveoriginalkey/basket; improve message distinguishes no receipt vs saleproof; no clearinguncertainty automatically. Paymentquestion/incomplete not mutating state inUI, ensure valid200needs_tender branch doesnotfallinto uncertain. Add realresponsefixturetests and connection/receiptstatusregressions. Do not changebackend/secrets orresetdata. No agent escalations; roottests/package. Checkpointpromptly, persist handoff.

## Assigned by Mutungamiri — PHONE-RECOVERY-001 temporary scope extension
2026-11-01: sole writer apps/web/public/service-worker.js narrowly authorized for network-only API/readiness/no-store/cross-origin handling and cacheversion update. Existing SW stale API fallback undermines truthful shop probe. No IndexedDB/sync/queue work. Fambai not active; no conflictingwriter. Persist tests/handoff.

PHONE-RECOVERY-001 implementationfinal:132frontendtests/build84modules explicit8001/shop-Ct0WV7-I.js pass; cachev4andbuildlabeldistverified; scoped diffcheckpass. Rootpackages, QA/actualupdatedphone acceptance next. TemporarySWscope released.

## Assigned by Mutungamiri — 2026-11-01 — CATALOGUE-VOICE-UX-001
Fullactivation. Ownwebexceptoffline +nativeAndroid temporaryscope +brain. Coordinate Hwaro/AI newcatalogueclarification and explicitspokenmatchconfirmation. Useractuallogs:1 bread glove number;1coca-cola nabo marble;bath soap nabo maple map;coca-cola missingquantity. Exactfastpathsame; nonexactMuse/localproposals mustbe spoken Didyoumean1Breadloaf? acceptsYes/No/Cancel handsfree (no per-sale buttons), newcommitflagasagreedbackend. Ambiguous/missingquantity promptfollowup, neverautocommitmodelguess; retainoriginaltranscript+matchsource visiblyactualMuse thinking onlywhenrequestinflight. ImproveApo/Napo boundedframehandling cautiously commonASRvariantnabo onlyterminal appropriate oruserconfirmedaliases; do not silentlystripordinaryproductwords/number andsell. NativeASRalternatives optional ifsmall clearcontract otherwisefocuscore. Preservepaymentuncertainty/Retry/Cancel/receipts/networkfreshness. Labelnewbuild CATALOGUE-VOICE-001. Tests actualexamples andnegative aliases/falseconfirmation. NoAPI/AIwrites/liveresets/escalations; rootpackaging. Persist handoff.

CATALOGUE-VOICE-UX-001 sourcecomplete:136frontendtests/build84modules explicit8001/shop-D3It--1w.js pass; scoped diffcheckpass. GroundedproposalYes/No/Cancel+missingquantitycontext wired. RootAPI/AI/QA/provider/packaging+phoneacceptance next.

## Assigned by Mutungamiri — 2026-11-01 — COUNTER-POLISH-001
FullAGENTS activation. Owner confirms phone sale works; PRESERVE functional sale/catalogue/Muse/payment/retry/backend contracts. Own webexceptoffline +nativeonlyifnecessary +ownbrain. User photo path .codex-remote-attachments/01a19763-315a-7d33-a788-00d9150a85c9/4ce0acee-bece-4c97-ad4e-03e36106c24a/1-1000389737.jpg inspectpluslogo. Clean busy-shop counter UI: compact receipt showsitems andTotal/Tendered/Change (changehero), shortpaidstate; diagnostics/build/server IDs/timestamps/legalstockundo text behinddetails orProfile, keep investigationdata notdelete. Gentlebrand character fromexistinglogo (teal/green,warmaccent,friendly restrainedcopy), no newassetsframework/unrelatedpages. Completedreceipt: Apo or Apple wake immediately dismisses modal/resets currentUI toSell while preservinglatestpaidreceipt/history and SAMEutterance remaindercaptured fornextsale; wake mustNEVERdiscard pendingpayment/clarification/uncertain outcome. Handsfree APKdefaulton, singlepersistenttoggle applies wake/YesNo/qty/CashBank/retries andnextsale; modalclose/completedflow shouldnotdisablelistening. ExplicitPause onlyoff; typing remainsavailableunderTypeinstead. Preserve TTS/selfecho/lifecycle safeguards. Prefer treatAppleonlyidle/completed startnotasproductinternalword; user saysApple. Add meaningful wake+session tests, buildnewCOUNTER-POLISH-001. NoAPI/AI/offlineedits/livemutations/escalations; roothostpackage. Persist handoff/checkpoint.

COUNTER-POLISH-001 sourcecomplete/frozen:140frontendtestsPASS; final86moduleAPI8001build shop-D1AJuhDJ.js PASS; scoped diffcheckPASS. Compactcounter/sharedvoicepreference/completed-onlyApoApplewake ready. Rootpackaging andupdatedphoneacceptance next.


## Assigned by Mutungamiri — 2026-11-02 STARTER-COGS-UX-001
Load full activation protocol. Scope apps/web/src/api.ts demoProducts only, related frontend fixture tests and own brain; no UI/session changes. Coordinate exact illustrative unit_cost_micros values with Hwaro/Ruzivo so frontend fallback catalogue matches backend starter costs. Preserve names/prices/stock. Run focused/fullfrontend/build explicitAPI8001; no packaging or live calls. Persist handoff.

STARTER-COGS-UX-001 complete/frozen2026-11-02: canonicalfallbackcostparity1test/full141frontendtests PASS; explicitAPI8001build86modules/shop-D4hvSYIv.js PASS; scoped diffcheckPASS. NoUI/session/native/backend/livewrites orpackaging. Rootintegrationnext.


## Assigned by Mutungamiri — 2026-11-02 ANDROID-COUNTER-INSETS-001
Fullactivation; temporarily exclusive apps/android/android/app/src/main native source/resources +apps/web UI/styles (excludeoffline) +ownbrain. Userbottomappbuttons behindAndroidnav, wants Androidcontrols revealedbyupwardswipe. Implement platformappropriate immersive transientnavigationbars with safe WebView/appbottomnav insets avoidingoverlap onreveal, gestures/3button/keyboard, lifecycle. Preservepermission/ASR/TTS/voiceflows andtyping; keepstatusbar ifappropriate. Readcurrentnativebeforeediting. Sourcefornewfastproposal provenance UI ifneeded coordinateUngwaru/root. Test/build explicit8001, freezehandoff. RootsolegeneratedAPKpackager; no SW/provider/API/live/escalations.

ANDROID-COUNTER-INSETS-001 source COMPLETE/frozen 2026-11-02:142frontendpass,86moduleAPI8001build/shop-CMFZxwB9.js, QA sourcePASS; nativecompile/package+physicaldevice gates remain root/Owner.


## Assigned by Mutungamiri — 2026-11-02 REPO-SHOP-UX-001 andPRODUCT-DIAGRAM-001
Fullactivation. Scope apps/web source/config/tests excludingoffline + temporary docs/product-diagram/ artifacts andownbrain. Userwantsseparatedteamviewexcluded/ignored whileStreetCEOcleanclonebuildworks. Auditdependencies, split genericAPIURLvalidation outof teamMessages into shopownedgenericmodule; moveoffice/team-onlycode+tests intoignored local area (rootowns.gitignore, coordinateexactlist), optionalofficeentry localonlydefaultVite/TS/testbuild mustnotdependignoredfiles. Preservelocalteamapp working optionalworkflow ifpossible; no deletion oflocalfiles or agentsbrains. No sale/voiceUIfunctionalitychanges. Separately createvisuallyappealingeditableSVG+standaloneHTMLproductdiagram andPNG/PDFpreviewifavailable within docs/product-diagram/ (explicittemporaryscope); use existingbrand, currentMVPcatalogue→sale/manualorApo→tender/change→stock/history,SQLite+Muse tracing,safeproposalconfirmation. Readvisualization skill C:/Users/clyve/.codex/plugins/cache/openai-curated-remote/build-web-data-visualization/0.1.21/skills/data-visualization/SKILL.md; pickdirectstaticSVGsoftware/productflow plusaccessiblemobileHTML, noconceptapprovalrequired. AvoidclaimingallAIlocalproposalsareactualMuse. Rootwritesbuilderbrief/docsotherpaths. Sendexclusionmanifest ASAP beforeedits andhandsoffbuild; noAPKpackaging/live/escalations. Tests+handoff.

REPO-SHOP-UX-001+PRODUCT-DIAGRAM-001 source/artifacts COMPLETE2026-11-02:117shop+26optionalofficepass,65/44modulebuildsPASS, editableSVG+mobileHTML+actualPDF/PNGpreviewvisuallyinspected. Parentcleanexportverificationpending; no deletion/staging/live/native/SWchanges.


## Assigned by Mutungamiri — 2026-11-02 QUANTITY-REPLY-UX-001
Fullactivation webUI+ownbrain scope, native speechread-only initially. Ownerscreenshot17:30 asksHowmanyPotatochips; useroneanswer notheard, shouldnotneedApo. Roottraces show07? actual15:30UTC requestputadochipsnaples reasonmissingqty and nofollowupreplyrequest; inspectfrontend/nativehandoff ASRreplylife/callback/errors/finalone handling. Reproducewithmeaningful fake native/recognizer harness ifpossible, fixconfirmedbug notcosmetic only. ShowlisteningstateinmodalactualASR state notenabledflag. Preserveallhandsfree/paiduncertainty. Rootmaygrantnativeifneeded, noAPKbuild/live/restart/escalation. Testsource+explicitAPI8001 build labelledQUANTITY-REPLY-001 andhandoff.

QUANTITY-REPLY-UX-001 explicittemporarynativeextension: apps/android/android/app/src/main/java/com/streetceo/app/ApoSpeechPlugin.java speechReady readinessnotification only; ownweb speechbridge lifecycle/readiness. No permission/ASRlanguage/tuning/windowpolicy changes.

QUANTITY-REPLY-UX-001 source COMPLETE/frozen2026-11-02:122frontendPASS,66moduleAPI8001build shop-D8flaUN9.js,5newlifecyclecases; actualready/foreground/promisehandlerguards. RootQA/nativepackage/physicalphone gatesseparate.


## Assigned by Mutungamiri — 2026-11-02 REPORTS-CLOSE-UX-001
Fullactivation webUI+ownbrain scope excludingoffline/nativeinitialread-only. Owner mobile reports monthlysales+salesbyproduct inclusivecustomdates presetslast1/20/90days; endmyday spokencommandwhileselling startsquestions countedcash/neededopening, comparesserverexpected &counteddiff,confirmbeforepersist,monthendoptionalcount notgate. ReuseHandsFreeVoice/speechLoop sharedpreference/noquestiontap, typingfallback. Routeendmyday beforeproductparser (alsoApo endmyday Napo andbarephrasewhileidle; don'tinterruptpending/uncertain sale). CoordinateHwaroAPI/Ruzivo policy, no bankbalancefakezero. Reports mobilecleanfilters; basicmonthendsummary optional stocktake link+Skip. ScopeappUI/contracts; nofinancialmathauthoritativeclient, noAPI/nativewrites. Handoff fullfrontendbuild explicit8001 labelREPORTS-CLOSE-001; rootAPKpackager.

REPORTS-CLOSE-UX-001 source COMPLETE/frozen2026-11-02:129frontendPASS,69moduleAPI8001build shop-BlQoqAAb.js; finalcontractstubDOMhostrerun+QA/finance/nativepackagingparentgate. No physicalacceptanceclaim.


## Assigned by Mutungamiri — 2026-11-02 NAPO-RETRY-001
Fullactivation webUI/wake/speechtests ownbrain; nativeinitialreadonly. UseragainNapo struggles. Gitdiffd5caac8..HEAD shows noNapomatcher/nativeASRchange, onlybareendday branch. LatestphoneAPItraces16:02UTC raw 'apple one bath soap napple' andearlier 'apple one Butt song apple' in clarification, timeouts. Neednarrow terminalnapple alias (notapple) and proper full-framed retries whileawaitingcatalogueanswers: normalize recognizedApo/Apple/personalstart +Napo/Nabo/Napple/personalend exactlyatboundaries, preserveeveryproductword/internalapple. Bareone/Yes/payment repliesunchanged. Do notbroadlystriptailapple orarbitrarynoise; incompleteframedretry mustnotlosebodyorresetsale. Senddesignfirst/stabletests andfakeASRrepro ofquestion→fullframedretry→Yes→payment. No cloud/financial/APIchanges. Rootpackager afterQA, buildNAPO-RETRY-001 explicit8001. Readlatestacceptance/brain; persistfinalhandoff.

NAPO-RETRY-001 source COMPLETE/frozen2026-11-02:132frontendPASS,69moduleAPI8001build shop-BCeIFwuy.js;3newhelper/fakeASRcases+legacycompat. RootQA/nativepackaging/physicalgate separate.

## Assigned by Mutungamiri — 2026-11-02 SHORT-VOICE-TRAIN-001
Owner: screen prompts may remain full, spoken tender exactly Cash or bank?; spoken sale completion Sale saved. Preserve other critical error/clarification speech and EndDay own flow. Profile pronunciation setup collect5 reviewed Napo samples per device, retain distinct valid variants across save (dedup allowed with5sample progress); support observed nepal/nepo/nopple safely via reviewed personal aliases, no broad fuzzy/fruitstripping. Keep existing v1 savedapo/napo migration, safe validation/conflicts acrossallaliases, longest boundary matching, no partial productloss; reset clears aliases; Profile state updates reflected Sell withoutreload. Full localstorage errors honesty, cancellation safe, trainingneverposts sale. Runako singlewriter apps/web/ UI/voice/helpers/buildInfo/tests. Temporary packaging extension apps/android generated assets/build outputs only; no native source changes. Load AGENTS role sixbrains docs/masterboard; test meaningful parsing +shortTTS+5sample flow. Root docs; ChengetaiQA. Build final API8001 frontend+APK label SHORT-VOICE-TRAIN-001 afterQA rootgo, existing same signing key only; no live API/data changes. Persist handoff.

SHORT-VOICE-TRAIN-001 sourcefrozen137testsPASS/build70modules shop-DKDHubvq.js; QA/packaging/physicalgate pending seehandoff.

SHORT-VOICE-TRAIN-001 packaged7168817bytes SHA2562b85be34b5e9a3822f01e035db5f19bd76a1c4f247f68f140937d70fa9c5bfee; samev1/v2cert/7assets PASS; finalhandoffpersisted physicalgateOwner.

## Assigned by Mutungamiri — 2026-11-02 REPORTS-POLISH-001
Owner mobileReports confusing/embarrassing requests redesign. Runako apps/web Reports.tsx and reports-close.css reports-only selectors/newreporthelpers/tests/buildInfo; preserve EndDaystyles/no API/calculationchanges. Build brandedclean mobile320/390: compactheading/logocharacter, oneclearperiodselector activepill Today/20days/90days/Month/customdisclosure, prominent salestotalcard+transactions, simplecash/bankbreakdown, productlist rank/units/amount clearhierarchy. Defaultperiod intentionalexplicit, usermonth/datechanges validated/stalecontentnotmislabelled. Hide technicalcoverage/asof/COGSdetails in disclosure but missing/incomplete warningvisibleconcise, neverfake0profit. Monthly/dailydetails secondary; optionalmonthstockcount subordinate onlymonthreview intuitiveSkipcount preserved. Loading/error/empty intentional, accessible44pxcontrols nooverflow. Do not change reportsemantics/snapshots/reconciliation. FollowAGENTSactivation role6brains docsboard. Sourcebuild/tests thenfreezeQA; temporarygeneratedAndroidpackaging extension only afterrootgo, samekey/API8001 labelREPORTS-POLISH-001. Persisthandoff.

REPORTS-POLISH-001 sourcefrozen141testsPASS/build71modules shop-BsA05o4-.js CSSshop-BzDVHsCO.css; QA/screens/rootGO pending.

REPORTS-POLISH-001 software/packagecomplete7170003bytes SHA2564fc69bbee696e19e25d684eb9a43dbf6f74ffe60b940ddada29b7254fcd49345; samekey/7assetsPASS; physicalacceptanceOwner.

## Assigned by Mutungamiri — 2026-11-02 STOCK-COUNT-HISTORY-UX-001
Owner standaloneStockCount page withStart stockcounttop historicalcountsbelow. Runakoapps/web scope App/Stock/RetailControl/Stocktake/newpageCSS/clienttests/buildInfo. Dedicatedview reachableStock and existingReports/EndDay countactions; removeburiedcounttab orredirectexistingentry soonecountflow. Pagecleanbranded newStartbutton +datedhistory/draftconfirmedstatus/products/differences summary; open savedcount details expected/count/difference actor/notes/status, confirmedread-only, draftsresumeexistingreview guardedconfirm; newformonlyafterStart nofakehistory. Existingcountsblanknotzero/stale/uncertainreload/ackandstockconfirmation preserved. Hwaro listGETsamecollection returnslistStockTakeRecord newestfirst, existingitemGETresume; parservalidates shop/id/status/dup. Demo disconnectedclearly noactualsavedhistory; loading/error/empty/retry accessible320390. Sourcebuildtests freezeQA; Androidgeneratedpackaging extension afterrootgo samecert/API8001 labelSTOCK-COUNT-HISTORY-001. No backend/nativewrites/livefinancialposts. Followactivation/persistbrains/handoff.

STOCK-COUNT-HISTORY-UX-001 sourcefrozen144frontendPASS/build73modules shop-CwgRw3nQ.js; QA/screens/rootGO pending.

STOCK-COUNT-HISTORY-UX-001 software/packagecomplete7172841bytes SHA256d08bbd5c6470d324f33bf724049601f2bca0bbb96583314a3ce158c8b5259a80; samekey/7assetsPASS; physicalacceptanceOwner.

## Assigned by Mutungamiri — 2026-11-02 PRODUCT-PROFIT-UX-001
Owner addsProfitbyproduct Reports. Runakoapps/web Reportsscopeclienttypes/parsers/helpers/reportCSS/buildInfo/tests. KeepcleanbrandedReports; pageheadingReports, clearSales/Profitselector sharedperiods. Profitview summary revenue/recordedCOGS/grossprofit/margin +perproduct qtysalescostgrossprofitmargin, rank grossprofit completefirstunknownhonest; showlossnegative/zeromarginundefined, incompletevisible no fakezero. NewAPIadditive summary/product nullablegross_profit_micros/margin_bps; productcogs existsalready addparse. BigIntvalidatemath/safeints no currentcataloguecostprofit. Explain grossprofit beforeexpenses; no arbitraryexpensesallocation/netprofitclaim. Ruzivopolicy pendingrounding. ExistingSales/StockCount/EndDayunchanged. FrozenbuildQA/finance thenrootpackaginggo generatedAndroidscope samecert/API8001 labelPRODUCT-PROFIT-001. Followactivation/persistbrains/handoff. No backend/native/livefinancialposts.

PRODUCT-PROFIT-UX-001 sourcefrozen150frontendPASS/build74modules shop-aJiWshyF.js; QAfinance/screens/rootGO pending.

PRODUCT-PROFIT-UX-001 software/packagecomplete7174651bytes SHA256843db5f53cd586cb17a4c4f422a2ec92b4eddcfba7a1b05011a331eae57abee6; samekey/7assetsPASS; physicalacceptanceOwner.

## Assigned by Mutungamiri — 2026-11-02 STOCK-TABLE-UX-001
Owner says Stock APKformatting embarrassing asksclickabletable. Runakoapps/web StockCatalog/newstockCSS/helpers/tests/buildInfo +minimalAppstockwelcomehide clean asReports ifneeded. Preserve products/actions/costeditor/imagecontrol/stockcount/retailcontrol. Compactbrandheader+smallsummary, Start/Openstockcountcompactlink notlargehero, searchable actualtable columnsProduct/Onhand/Sellprice (shopcurrency label no inventedcurrency), lowstockbadge readable, nameSKUwrap. Taprow/productbuttonopens productdetailpanel (accessiblekeyboardclose/focus), costdetail+purchase/costcorrection/imageactions movedoutofallrows into selecteddetails, no stockchangefromrowtap. Preserve imagefeedback/costmutationguard/refreshselectedproductdata/no duplicates. No backend/native/mathchange. ExistingReports/StockCountflows remain. Screenshot320390 +keyboard/longnames/prices/emptyfilter/error/costediting no silentlostpending mutation. Followactivation6brains/docsboard, sourcebuildtests freezeQA. Androidgeneratedpackagingafterrootgo samekey/API8001 labelSTOCK-TABLE-001. Persisthandoff.

STOCK-TABLE-UX-001 sourcefrozen153frontendPASS/build76modules shop-cpAvRe4C.js; QA/screens/rootGO pending.

STOCK-TABLE-UX-001 software/packagecomplete7175921bytes SHA256c69fd17958c94c049aaa7880bfe65892f2f301cdd568c0a9b03a79988c0ade73; samekey/7assetsPASS; physicalacceptanceOwner.

## Assigned by Mutungamiri — 2026-11-02 SALES-HISTORY-TABLE-UX-001
Ownerasks APKfolderlink clarified andSalesHistoryclickabletable tap→products/total/amounttendered/change. Runakoapps/web Transactions/receiptHistory/types/styles/tests/buildInfo +minimalApppropscurrency/loading/refresh/welcomehide transactions ifneeded; nobackend/native/mathmutation. Cleanactualtable Date/Payment/Total (fullreference/detailsecondary), wholeamounts/qty/nooverflow, keyboardproductreceiptbutton+rowtap detailfocusclose. Receiptcard authoritative savedtotal, method, received/change unknownlegacy notinvent0; productsqty savedreceipt_lines labels ifvalidoptional otherwise honestcurrentcatalogue/IDfallback nevercurrentprice costreprice. Existinghelperpaymentsemantics preserve. Readonly no sales/stock/cashrequests. Loading/error/empty distinct, onRefresh mayexistinglistSales fromApp optionalnoextraneous. Currencyfromverifiedconnection likeStock fallbackshopcurrency. Existinghistorycurrentrecordrefreshselection notstale. Followactivation6brains/docsboard. BuildtestsfreezeQA actual320390screens, generatedAndroidpackagingafterrootgo samecert/API8001 SALES-HISTORY-TABLE-001. No livefinancialposts/cloud. Persisthandoff.

SALES-HISTORY-TABLE-UX-001 sourcefrozen157frontendPASS/build77modules shop-CWFztYnL.js; QA/screens/rootGO pending.

SALES-HISTORY-TABLE-UX-001 software/packagecomplete7177667bytes SHA25629935451ee963589c266dea510a78a123fcb83d59c172af0b1782e5778672b9f; samekey/7assetsPASS; physicalacceptanceOwner.

## Assigned by Mutungamiri — 2026-11-02 DEMO-CAPTURE-EXPORT-UX-001
Owner4tasks. Runako singlewriter apps/web and explicitAndroidnativeexportplugin scope apps/android/android/app/src/main/java/... plusManifest/FileProvider/xml ifneeded (avoidnewdependencieswhereplatformPrintManager/shareworks). 1) voicefocusedclarification coordinateHwaro additive retainedbasket/pendingcontext preserve100alreadyunderstood nofullresay/partialpost, controlskeep/resolve/removeexplicit; clientsafetyexisting. 2) salephotodisplay useexistingproductImages inSellCheckout andvoicesavedbasketwhenIDmatches; localpreviewversusserverphotoshonest fallback. 3) Reports exportCSV+brandedPDF phone share; CSVcannotlogo textualStreetCEOheader, correctsales/profit/currentperiod/currency/unknownnotzero andCSVformulainjection protection, stableescapedUTF8, no currentcostreprice. BrandedPDF viaAndroidPrintManager/WebViewHTMLor verifiedbrowserprint path, nativeShareintentCSVFileProvider; browserdownload/sharefallbackhonest. Explain grossbeforeexpenses/sourceperiod/unknownstatus logosinPDF. Integrate export helpers independently UIpaths, cleancontrols. 4) handwritten combineddailylist uploadreview UI laterAI/backendcontract pendingRuzivopolicy, do notfakeOCR orautopost; rootwillassignfollowup oncecontract. Work1photos+exports whilebackendclarificationcontractpending; nofinancialbackendwrites. Loadactivation6brains/docsboard; checkpointmilestones/persist. SourcefreezeQAfinance/nativepackagingrootgo later samekey/API8001 buildlabelpending. No livefinancialcalls/cloudrealimage.

DEMO-CAPTURE-EXPORT-UX-001 phase1frozen163tests/nativecompilePASS; QA/PDFongoing, paperUI nextnewfiles no distwrites untilphase1done.


### 2026-11-02 DEMO-CAPTURE-EXPORT-UX-001 packaged CAPTURE-SHARE-001
- Parent packaging GO after isolated329testsPASS27.25s, scoped QA DOM/export/PDF PASS and Ruzivo financial approval (runtime/phone boundary). Copied approved CvX88Bde/8Qthzhh1 dist, Capacitor copy and Gradle assembleDebug offline SUCCESS6s. No further product changes.
- APK apps/android/android/app/build/outputs/apk/debug/app-debug.apk:7307805bytes; SHA2563f0ab7380927fad1863c4f0bbd1715a1953575080916496c8a2d616464005814. All7dist files byte-identical in APK. Embedded CAPTURE-SHARE-001/API http://192.168.10.213:8001 verified.
- apksigner v1/v2 valid, unchanged cert SHA2560e5aee54456b088eb817214d7c08f209169d9b2f68268dca4d6f6ad21aacd3ed. StreetReportExportPlugin present in DEX; javap compiled MainActivity proves registerPlugin call for report plugin and existing ApoSpeech preserved. aapt2 packaged manifest verifies com.streetceo.app.reports FileProvider exportedfalse/grantUriPermissionstrue, report_export_paths restricted to cache report-exports/.
- Root notified for independent HTTP download/hash/launcher-state verification. No live API/DB mutation performed by Runako. Native export compiled/packaged, but actual phone sharing, microphone/wake interaction and device installation still require physical-phone acceptance.

## Assigned by Mutungamiri — 2026-11-03 EMERALD-UX-001
Runako owns apps/web UI/CSS only (exclude offline layer), refresh Today/Sell/Stock/Reports/Profile from owner supplied five visual suggestions, not authoritative requirements. Keep actual logo, emerald/pastel unified hierarchy/icons, compact mobile header/nav/safe insets, appealing voice hero with truthful actual listening state, readable existing baskets/clickable stock/history and product photos, simpler Reports hierarchy, clearer pronunciation settings. Preserve all handlers/state/voice/payment/recovery/report contracts and existing features. No fake comparison/insights/trends, no unsupported loanpack or guaranteed pronunciation claims; gross profit remains accurate cost coverage. Do not add Apo training if unsupported. No backend, tests/infra or native writes. Build/test frontend, visually render all five screens at narrow Android width via available local Playwright; root coordinates QA/native packaging. Follow activation protocol, record handoff. Reference images owner local Temp 7d1f5aae-a326-4e7f-9ba1-3a6e67961eef (Sell),40e23760-92c1-47e6-97ac-a017e076c539 (Today),91ab6595-ccfd-4876-a414-e2a1453df47a (Stock),40dfd827-243d-4d44-b7d8-8922cd37b63e (Reports),53c49fa7-b831-4312-b03b-004dd57d61cc (Profile), all codex-clipboard-*.png.

## 2026-11-03 — EMERALD-UX-001 source freeze
- Restored AGENTS/role/six brain files/current demo acceptance/latest board and owner reference screenshots. Owned apps/web UI/CSS only, excluding offline. No backend/native/business rule changes.
- Added ShopIcon.tsx decorative inline SVG icons and emerald-ux.css final presentation layer. Original logo preserved. Unified emerald/pastel surfaces, mobile header/nav with explicit active state and system-font fallback, Today real receipt/sales/stock data, static fictional sparkline removed (receipt emblem decorative), existing sale action restyled. Existing non-null comparison displays its actual sign.
- Sell counter microphone illustration and shorter guidance, actual HandsFreeVoice readiness remains source of status; all sale/payment/uncertainty/checkpoint/voice/EndDay handlers unchanged. Manual products/basket retain image/control flow. Stock table now uses already-loaded photos beside names, existing row/detail/cost/count handlers unchanged; stock details scroll margin96px avoids sticky header.
- Reports short explanatory hierarchy + tab/filter/share styling, actual gross-profit/data-coverage unchanged. Profile includes clear pronunciation controls, personal phrase semantics unchanged (one Apo/five Napo); diagnostics/build and activity/request history collapsed by default but accessible. No fake trends/insights/loanpack/training guarantee added.
- Files: src/App.tsx, Reports.tsx, StockCatalog.tsx, VoiceCapture.tsx, buildInfo.ts, main.tsx; new ShopIcon.tsx, emerald-ux.css. Final label EMERALD-UX-001, build85modules shop-DvytmpBm.js/shop-DppMBC4o.css. tsc/Vite PASS (existing500KBchunk advisory); final171frontend PASS1176.93ms. git diff --check apps/web PASS. Early script failed Windows defaultcp1252 decode before any file write; rerun PYTHONUTF8 successful. Two npm/path commands used wrong cwd and were corrected; final checks all correctcwd.
- Ran Chengetai authored tests/emerald_visual.dom.py read-only fixture gallery on finaldist via escalated localmsedge headless PASS8.65s (five360/390/1280 bounds/navtargets/sixbundledimages/noJSerrors/noPOST). Visually viewed allfive390 firstpass and Today/Stock/Profile after typography/diagnostic correction. Gallery data/qa-emerald-ux/ ignored; no live API/shop writes. Firstsandbox tests/build worked; browser only hostescalation. Systemfonts avoid externalfont availability; code/pre/kbd remain monospace.
- Handoff root and Chengetai notified source freeze; QA owns independent interaction regressions. Root must review screenshots before packaging/deployment. No APK rebuilt, no native/backend changes, no Git commit/push or runtime restart by Runako. Physical phone acceptance remains owner step. Source unchanged until concrete QA finding.
2026-11-03 XLSX-EXPORT-001: Runako scoped apps/web/src/reportWorkbook.ts only. Genuine OOXML workbook with emerald title/header bands, summary/coverage notes, product filter and frozen header, numeric money/margins and formula-like text stored as inline strings. Small stored ZIP writer; no new dependency. Generated fixture passed Python zipfile CRC and openpyxl type/amount/percent/style/filter/freeze checks. Root integrates browser and Android transport and validates final build. No APK or live writes by Runako.
