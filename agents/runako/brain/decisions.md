# Runako — Decisions

No decisions recorded yet. Initialized 2026-10-29; no work performed.

## 2026-10-31 — W3/W4 frontend decisions

- Shop-ID: use source-confirmed seed ending 0001; reject nil/malformed values.
  Preserve valid overrides and require explicit correction instead of silently
  switching a configured shop to demo. Source: Hwaro's seed/handoff/contracts.
- Office: independent HTML entry and bundle; remove Team completely from shop.
  Local planning structure is not backend authority. Extra rooms cannot reuse
  the one verified Street CEO evidence/chat adapter. Future room API adapter
  and persistence phases are documented, not fabricated.
- Status: assignment comes from the board; activity comes from repository file
  mtimes. Six-hour freshness matches Hwaro's contract. File lists are filtered
  by scope, not attributed to agent authorship. Historical pass-count mentions
  are labelled as overlapping evidence, not current CI totals.
- Images/social: verify file type/size/signature/decoding, show local preview
  separately from uploaded metadata, and never treat memory:// as an image URL.
  Current image-generation response is unavailable only; no successful output
  shape or text-generation route is invented. Export/publication are separate.

### 2026-10-31 — W5-COSTS-INVOICES-UI-001

- Consume source-verified invoice review/confirm and expense draft/confirm only.
  Keep review separate from effects, require explicit product matches and an
  acknowledgement of stock additions; no fake OCR or automatic recurring charge.
- Do not implement cost-only correction through receipt confirmation: backend
  adds units and weighted cost, and has no verified direct correction endpoint.
- Preserve APK reachable root: local browser override used only for QA, restored
  after evidence capture; localhost is not a usable phone backend address.

### 2026-10-31 — W6-REALTIME-OPS-MVP-UI

Follow the narrower urgent30minute cut: existing repository activity endpoint only.
Separate15second receipt freshness from six-hour evidence freshness and actual
session state. Initial history is never emitted as new live events. Remove
Working inference from assignments/files; keep session state unverified. Retain
last successful snapshot on errors and bound local observed-change history.

### 2026-10-31 — W5-DATE-UI-001 revised requirement

Use device/browser local timezone and locale in production (Intl default, no
explicit timeZone). Inject locale/timezone and clock only for deterministic tests.
Minute-boundary and resume updates prevent an open demo from retaining old date
or time-of-day greeting. This supersedes the initial fixed-Johannesburg request.

### 2026-10-31 — W5-COSTS-INVOICES-UI-001

Use verified product-cost correction draft/confirm separately from stock
receipts; exact micros, mandatory source/reason/actor/effective date, explicit
acknowledgment, audit readback. Keep central purchase as the single visible
invoice receipt path to avoid double receiving. Source suggestions never
auto-match. Unknown cost outcome freezes retry because API has no saved-draft
lookup/idempotent replay contract. Manual invoice review is honest provider
fallback, not OCR. No financial posting or historical profit claims invented.

## 2026-10-31 — W6-APO-HANDSFREE-001
Native Android SpeechRecognizer bridge preferred to unsupported WebView browser ASR. Pronunciation setup stores user-confirmed ASR aliases with prefix-collision rejection; no acoustic training claim. Canonical Apo/Napo framing restored with legacy closing Apo compatibility for typed/review path. Foreground opt-in only; audio/provider behavior requires device QA.

## 2026-10-31 — W6-VOICE-PROFILE-001
Pronunciation enrollment belongs Profile. Sell shows primary hands-free control/status; optional hold/text entry under accessible disclosure. Keep raw connection detail expanded while visible/spoken error gives concise next action. No catalogue fuzzy substitutions introduced.

## 2026-11-01 — DEMO-APK-APO-001
Owner explicitly requires voice-only demo. Native launch auto-arms Sell/Quick after OS permission; no per-sale enable tap. Foreground only, whole-token Apo/Napo, strict backend catalogue confirmation, no partial unknown-product sale. Native TTS completion gates ASR; bridge operations serialized and session-owned. Original key preserved on mutating5xx because trace persistence can fail after durable sale commit.

## 2026-11-01 — SPRINT90-UX-002
Cash amounts parsed to integer cents without float rounding. Accept explicit decimal/point-digit/dollars-cents wording and bounded integer words; ambiguous phrases ask again. Unknown manual/voice mutation retains original request and blocks cross-flow new sales even if recovery returns4xx. Investigation events remain distinct from durable sale receipts; no completion inference from log phase alone.

## 2026-11-01 — PHONE-RECOVERY-001
Ownerphoneevidence exposed misleadingnetworkOnline and questionfetchclassifiedasunknownsale. Use actualreadonly ready+shopchecks. Backendcontract proves incompletepaymentrequest cannotpost; recoverquestion with samebasket/key, not freshsale. Priorpaidunknown remainssticky; onlyverifiedreceipt settles. Completepaymentruntimevalidation required before mayCommitclassification to avoid backendcoercion. No screenshot-only5G/oldAPKdiagnosis.

## 2026-11-01 — CATALOGUE-VOICE-UX-001
Nonexact groundedlines are proposals, neverautomatic sales. SpokenYes explicitlyconfirmsmatch; servermatch_confirmed required. Missingquantitycontext remainsserver-owned, rawuserreplypluspriorreviewID, noquantityguess. Newcorrectedexactfollowups askYes asconversationconfirmation. Retainunknown/noisy ordinarywords, terminalnaboalias only; provenance requiresactualprovider_called. Pauseownbackgroundprobes while actualmodel/APIrequest holdsstoretransaction toavoidfalseunavailability.

## 2026-11-01 — COUNTER-POLISH-001
Receipt primaryitems/Total/Tendered/Changehero, diagnosticsnotdeletedbutondemand. Wakeadvancesonlyverifiedcompletedreceipt; eventemittedwithoutresettingASRmachine so sameutteranceandbarewakecontinuationpersist. Appleonlyleadingidlewake, neverinternalproductreset. Onecontrolledexplicitpersistedvoicepreference spansmain/modal/replies; focuspauseisnotoff. Suppresseditingfocusrestoreoncompletedwake/Doneclose, retainingcounterfocusandASRcontinuation.

## 2026-11-02 — STARTER-COGS-UX-001
MirrorRuzivoapprovedillustrativeunitcostmicros inlabelledfallback only; canonicalbackendJSONparity test guardsseeddrift. Preservecatalogueidentities/prices/stock andno fictitiousinvoiceorProductsourceflag. Backendcost-auditprovenance remainsHwaro/Ruzivo scope.

## 2026-11-02 — ANDROID-COUNTER-INSETS-001
Reserve stable Android bars/cutout outside WebView even while navigation hidden: transient controls overlay, so visibility-only padding is unsafe. Use max with IME rather than addition and consume child insets; no double CSS spacing. Preserve status bar and all speech lifecycle; root owns packaging.

## 2026-11-02 REPO-SHOP-UX-001
GenericapiUrl staysshopowned; optionalteamtransports confinedlocaloffice. Defaultbuild/typecheck/test neednoignoredteamfiles. Localofficepreservedbymove notdeletion. Diagramseparatescustomerflowfromruntimearchitecture andmobileusesfulltextorder insteadof shrinkingSVGlabels.

## 2026-11-02 QUANTITY-REPLY-UX-001
Voicepreferenceisnotmicrophonereadiness. Modalusesactualready/start/errorfeedback; speechReady isonlynativeextension. Terminalfinalduplicatesuppression lastsasynccommandturn, notforeveruntilincidentalReacteffectreset. PostTTSepochrearmsreplysafely; pendinghandler musttrackbackgroundevenafterrecognizerstop. Preservepaiduncertainty/confirmationcontracts.

## 2026-11-02 REPORTS-CLOSE-UX-001
Serverownsreportpreset/businessdate/TZ/expectedcash/version; clientonlyformatandexplicitreview. BareEndmydayisidlecontrol, neverproductwordstripping/pendinginterrupt. SameHandsFreecontrollerandTTSepoch reused. OpeningandclosingareseparateexplicitYesmutationswithfrozenunknownretrycontext. Banknotcountedstaysnull. MonthreviewCountorSkipdoesnotlockledgerperiod. Legacyfullbankcloseentrypreservedsourcebutnotvisibleinnewcash-onlydemo workflow.

## 2026-11-02 NAPO-RETRY-001
Clarificationmayacceptbareanswersorintentionalfullretry. Leadingknownwakeandterminalknownenddefineframe; neverremovegenerictrailingapple. Bufferfinalchunksuntilclosingword; preserveoriginalreviewcontextandexplicitYes. Nappleterminalaliasonly; longestpersonalaliasesfirst. LegacyApo…Apocompatibilityhelperonly, noglobalendexpansion.

2026-11-02 SHORT-VOICE-TRAIN: additive v1napoAliases keepslegacyaliases; five reviewed samples atomic onfifth withduplicatescount, max10personalvariants. No fuzzyglobalnepal. Speechseparatefromvisiblepaymentquestion; savedreceiptvoice exactlySale saved.

2026-11-02 REPORTS-POLISH: Todaydefault explicitlylabelled; selection-keyed report preventsstale periodmislabel; draftsseparate. Grosssales notprofit; incompletecostvisible whilecoverage/auditdetailssecondary. PreserveEndDaystylesunchanged. MonthstockcountonlyinMonthreview.

2026-11-02 STOCK-COUNT-HISTORY: dedicatedpageoneflow, GETlist+freshitemonopen, expected_snapshot authoritative/currentlabelsdisclosed. Draftresumealwaysfreshack; uncertainconfirmationmustreloadverified andrefreshcatalogueifconfirmed, navigationblockeduntilknown. Historydifferencescountproductsnotnetunits.

2026-11-02 PRODUCT-PROFIT: sharedReportsperiods/optionaladditivefields preserveSalesoldbackend, missingprofitIncomplete. BigIntvalidate exactGP/signedHALF_UPbasispoints. MoneycentHALF_UP tinyknownlossmarkedLoss<USD0.01 withexact6details. Grossprofitbeforeexpenses, no allocation/netclaim.

2026-11-02 STOCK-TABLE: semanticclickabletable+keyboardproductbutton selectedinlinepanel keepsallactionswithoutrowclutter; exactintegercentprices andcurrencyfromverifiedGETshop only. Rootapprovedcostbusy/uncertaincallbackglobalnavguard preventslostoperationstate; Stockgreetinghidden noavatarbypass.

2026-11-02 SALES-HISTORY-TABLE: readonlyDate/Payment/Total table +primaryreceipt productsqty/total/received/change. Optionalverifiedhistoricalnames preferred currentlabelsfallbackhonest; no repricing. Legacycashpaymentunknownnever0, exactzeroevidencepreserved. Invalidrowsnotdropped; generationguardloaded/cached/errorstates explicit.


### 2026-11-02 DEMO-CAPTURE-EXPORT-UX-001 narrow recovery freeze
- Root/Ruzivo authorized original-key retry recovery only for explicit409 paper_review_stale then fresh same-shop/same-ID nonconfirmed GET. UI offers explicit Review this summary again, writes/verifies retired old key/version tombstone, verifies pending marker removal, resets all acknowledgements and requires fresh review. Retired version cannot be confirmed or retried. Generic errors/auth/key mismatch/confirmed mismatch stay guarded.
- Daily/monthly report count column now Receipts with separate daily-summary count, avoiding0 sales next to batch revenue.
- Evidence:171 frontend tests PASS1103ms; tsc/Vite83modules PASS, final shop-DB1P-Fuv.js/shop-8Qthzhh1.css CAPTURE-SHARE-001 API8001. Root/QA/Ruzivo notified; no dist writes until concrete findings; no APK packaging until GO.

2026-11-03 EMERALD-UX-001: Adopt emerald/pastel visual inspiration with system-font fallback and decorative receipt/mic icons; actual API/microphone state and all safety flows authoritative. No mock trends/metrics or unsupported loan/guaranteed pronunciation claims. Diagnostics and trace history remain accessible in collapsed details.
