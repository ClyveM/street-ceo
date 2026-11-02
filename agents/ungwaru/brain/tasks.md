# Ungwaru — Tasks

## Assigned by Mutungamiri

### W1-UNGWARU-001 — Meta/Llama capability spike — completed 2026-10-30

- Scope: `services/ai/` only; record findings in this agent's brain and propose updates to shared docs through handoff rather than editing another owner's files.
- Read `AGENTS.md`, this role, all six brain files, `docs/architecture.md`, `docs/product-requirements.md`, `docs/voice-design.md`, and `tasks/master-board.md` before investigating.
- Define a provider-neutral boundary for structured sale-intent and business-insight responses, with schema validation, timeout/error fallback, prompt-injection boundary, and a capability matrix for the available Meta/Llama route. Do not claim live model access without evidence.
- Do not implement voice capture, API endpoints, UI, or financial logic.
- Acceptance: a small testable module or design artifact in `services/ai/`, explicit verified-vs-unknown findings, and a handoff naming integration dependencies.

- Evidence: `services/ai/boundary.py`, `services/ai/capability_matrix.py`,
  `services/ai/test_boundary.py`; six unittest cases and py_compile passed.
- Dependencies for integration: Hwaro must expose a versioned AI insight
  request boundary; Inzwi must provide transcript text only; Chiono must supply
  evidence snapshots with stable IDs; Chengetai must add the module to the
  repository-wide quality gate; Mutungamiri must approve provider/credentials,
  timeout, and cost envelope.

No tasks assigned yet. Initialized 2026-10-29.

### W3-MUSE-001 — Live Ask Muse backend path — completed 2026-10-30

- Scope: `services/ai/` plus the explicitly permitted AI API integration in
  `services/api/app.py`; no frontend files changed.
- Added a server-only Meta/Llama provider adapter and a structured Ask Muse
  endpoint that filters sales by common periods and cites evidence IDs.
- Profit/margin questions fail closed with explicit missing COGS and expense
  requirements; revenue is never presented as profit.
- Acceptance evidence: 9 AI unittest cases passed, 5 focused Muse/API pytest
  cases passed, and Python compilation passed.
- Handoff dependency: Runako must wire the existing form to
  `POST /api/v1/shops/{shop_id}/muse`; Verengai/Chiono/Hwaro must supply COGS
  and expense evidence for numeric profitability analysis.

### W3-VOICE-INPUT-001D — Meta understanding review — assigned 2026-10-30

- Review the Meta Llama transcript-to-intent prompt/schema for short noisy-shop
  commands, injection resistance, and structured output failures.
- Propose test utterances and acceptance criteria for Apo/Napo understanding.
- Scope: `services/ai/` and Meta-owned docs/tests only; do not modify voice or API
  implementation files.

### W4-SOCIAL-001 — Safe product-to-social draft boundary — completed 2026-10-31

- Scope: `services/ai/` only; no API or frontend files changed.
- Added explicit product inputs, optional shop image reference, bounded brief,
  structured social draft output, evidence-linked claims, and draft-only status
  validation.
- Provider instructions prohibit fabricated discounts, stock, popularity,
  availability, customer results, locations, and other unsupported claims.
- Evidence: 14 AI unittest cases passed; 11 focused pytest cases passed;
  compilation passed.
- Handoff: Hwaro must expose the API route; Runako must wire the Social Update
  form; Chiono should review claim policy for future analytics-backed copy.

### W4-MUSE-IMAGE-001 — Draft-only Meta image boundary — completed 2026-10-31

- Scope: `services/ai/` only; no API or frontend files changed.
- Confirmed from current repository evidence that `LLAMA_MODEL` is a text chat
  configuration. Official Meta documentation describes Muse Image separately as
  `muse-image-1.0` at `/v1/images/generations` and `/v1/images/edits`.
- Added explicit image request/response types, product/image-reference safety
  validation, Meta image adapter, and `provider_not_configured` fallback.
- Evidence: 20 AI unittest cases passed; 11 focused social/image pytest cases
  passed; compilation passed.
- Handoff: Hwaro exposes the API; Runako renders the draft/unconfigured state;
  deployment owner performs a credentialed image smoke test.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W5-DEMO-READINESS-AI-001 — Urgent AI demo audit — completed 2026-10-31

- Audited typed Muse, Apo/Napo, profitability, social caption/draft, and image
  generation against repository code, configuration, and tests.
- No live provider claim: local port 8000 was inaccessible and no credentialed
  Meta request was made.
- Findings: typed Muse is wired but live-unverified; profitability reports
  missing COGS/expenses; voice confirms intent but does not post a sale; social
  draft is API-backed but not connected in the visible UI; image generation is
  not configured and its fallback labels mismatch.


### W6-DEMO-AI-001 — LAN AI verification — completed with API integration blocker 2026-10-31
- Assigned directly by Mutungamiri: verify invoice OCR and social/image runtime;
  fix only proven provider/schema issues, test and persist exact evidence.
- Social text/image LAN drafts succeeded; direct synthetic invoice adapter
  succeeded. LAN upload still hardcodes provider_unavailable, requiring Hwaro.
- No application files changed; 30 focused AI tests passed. See handoffs.md.

### W6-MUSE-PROVIDER-WIRING-001 — invoice/provider wiring correction — completed 2026-10-31

- Verified current LAN behavior: no local API/dev-server listener was available,
  so no live LAN success was claimed.
- Fixed only `services/ai/`: PDF invoice file references beginning with either
  `file-` or `file_` are now sent as `file_id` parts.
- Evidence: 31 focused AI pytest cases passed and AI adapter compilation passed.
- Remaining integration dependency: Hwaro's upload route must call the invoice
  adapter; social/image API routes still own runtime injection and persistence.

## Assigned by Mutungamiri — 2026-11-01 — DEMO-MUSE-TRACE-001
Implement sanitized durable Muse provider request/response tracking for investigation in services/ai/ only plus own brain. Load activation protocol. Coordinate Hwaro who owns API and SQLite: design durable trace sink/schema or SQLite trace module in AI scope reusable by API. Track correlation IDs, timestamp/model/operation, sanitized request and provider response, status/error/latency; no keys/auth headers/secrets or raw audio, bounded payloads and redaction; operational trace logs separate from brain memory. User explicitly asks requests/responses kept. Cover voice interpretation/Muse model calls used by APK; inspect services/voice read-only and report integration needed to Hwaro (do not edit voice). Logging must not emit false success or leak failures. Tests own AI scope. No product UI/API edits/live resets. Persist handoff.

### DEMO-MUSE-TRACE-001 result — 2026-11-01
Completed AI-owned implementation with 51 passing AI tests, compile and scoped diff checks. API/voice integration remains parent-owned dependency; persisted detailed handoff.

## Assigned by Mutungamiri — 2026-11-01 — SPRINT90-TRACE-003
Follow AGENTS full activation, own services/ai + own brain only. Fix SQLiteTraceStore.record oversized-event fallback preserving sanitized bounded shop_id, operation, model, phase, source, provider_called and correlation envelope so shop-scoped investigations does not lose oversized request/response events. No raw secrets retained, no arbitrary context values outside sanitizer. Add regression oversized event remains scoped readable using API test if owningcode unavailable coordinate Hwaro/root; AI own test envelope adequate. No unrelated features, no live restart/escalations. Root runs hosttests, persist handoff promptly.

### SPRINT90-TRACE-003 result — completed 2026-11-01
Fixed oversized trace envelope scoping; 8 focused and 53 full AI tests passed. Handoff persisted; parent integration pending.

## Assigned by Mutungamiri — 2026-11-01 — CATALOGUE-VOICE-MUSE-001
Fullactivation. Own services/ai +brain only. Implement real catalogue-grounded Muse fallback resolver for imperfectvoice transcript. Coordinateexactinterface/schemaimmediatelyHwaro andRunako. Supplyactual boundedcatalogue namesIDsSKUs (pricesonlyifneeded) as trusteddata; transcriptuntrusted. Returnstructuredknownproduct/explicitquantity proposals, requiresconfirmation, unresolved/clarification/unknown withspokenspecificprompt; validateallIDs/quantities/noinventedprices/all requesteditemscoverage. ExactparseroutsideAI ownedAPI. Sample 1 bread glove number ->propose1Breadloaf askconfirm, notautopost; coca-cola withoutqty ->askhowmany; 1coke1unicorn ->no partialsale. Trackactualproviderrequest/responselatency/redacted payload usingexistingtracecontext, boundedtimeouts/failures explicitsource nofakeMuse. Localclosematch fallback onlyclarifyandlabelsnotMuse. Tests providerfake/hallucinatedIDs/changedquantities/ambiguity/failure/redaction; root willrealliveprovider smoke withoutsale. No API/voice/UIwrites, noescalations. Persist handoff.

### CATALOGUE-VOICE-MUSE-001 result — 2026-11-01
AI scope complete; actual Muse-backed default plus injectable seam, bounded executor/timeouts, strict all-segment/known-ID/source-quantity validation and confirmation-only proposals. Full AI 65 passed; handoff persisted. No actual live smoke claimed.


## Assigned by Mutungamiri — 2026-11-02 MUSE-OUTAGE-001
User screenshot09:27 Shopconnected/Museunavailable. Fullactivation protocol; scope services/ai and ownbrain; read operationaltraces locally sanitized no secrets. Investigate recent actualcatalogueprovider failures; fix concrete AIbug ifconfirmed and targetedtests. No credentials printing/no livecalls/escalations/restarts; root hostprovidercheck. Report exact safe diagnostic and requiredactivation. Preserve validation/nopartial/confirmation/tracing. Handoff.

### MUSE-OUTAGE-001 result — completed AI scope 2026-11-02
Deadline repair24s/default25max, honest failure prompts; verified trace metadata and69AItests. Handoff persisted; independentQA/root activation pending.


## Assigned by Mutungamiri — 2026-11-02 FAST-VOICE-001
User rejects24s wait, needsfast handsfree fullsale. Fullactivation; scope services/ai+ownbrain. Investigate providerconnectionreuse/compacttaskrequest/safe boundeddeadline and conservative immediatecatalogue proposal for commonASR noise (explicitspokenYes required, no partial/unknown guessing). Exact fastpath alreadyexists. Send design/rootcontractneeds beforeeditingmatchingsemantics. Realprovenance, quantity/allitemguard,2capacity maintained. No livecalls/escalations/restart; roothandles. Must notclaim Meta model guaranteedfast. Tests/handoff.

### FAST-VOICE-001 AI result — completed 2026-11-02
Immediate conservative local proposals + explicit source/approval, single6sMusefallback/poolreuse/compactprompt. 21focused/74fullAI evidence; root integratedQA pending. Detailed handoff persisted.

## Assigned by Mutungamiri — 2026-11-02 DEMO-MUSE-WAIT-001
Owner now explicitly accepts longer Muse wait for demo, superseding fast-counter6s budget. Ungwaru single writer permitted services/ai/catalogue_voice.py, muse.py and focused AI tests; load AGENTS role six brains docs/masterboard. Set catalogue wait24s, max24; underlying catalogue-only HTTPtimeout25s using narrowly scoped optional builder parameter or equivalent; leave other Muse tasks default20s. Verify web voice quickSale existing30s request budget adequate (read-only). No frontend/APK change if adequate. Update regression default budget, bounds, tests. Preserve max2 inflight, no automatic retries, exact/local fast paths and confirmation. No provider call/live restart. Persist handoff. Root owns docs/activation, Chengetai QA.

## 2026-11-02 — DEMO-MUSE-WAIT-001
- Owner explicitly accepts longer demo Muse wait, superseding FAST-VOICE six-second provider deadline. Scope services/ai catalogue_voice.py/muse.py/tests only plus own memory; no backend/frontend/native or live changes.
- Catalogue resolver default/max now24s; its cached provider receives narrowly scoped HTTP25s override. build_muse_ai keeps general HTTP20s and StructuredAI20s defaults; catalogue calls provider directly under its24s outer deadline. Shared2worker/2inflight capacity, no retries, immediate local matching, item/quantity validation and required confirmation unchanged.
- Read-only frontend verification apps/web/src/quickSale.ts interpretation request timeout30s, sufficient for resolver24s + normal overhead. No APK rebuild needed for server-only budget update. Transport timeout is not a guarantee of provider latency; slow/unknown results still clarify honestly.
- Evidence: isolated escalated python -m pytest services/ai -q -p no:cacheprovider --basetemp .pytest-demo-muse-wait-ungwaru =>75passed1.27s. New builder test proves defaultHTTP20 vs catalogueHTTP25; updated resolver24/default boundary/max24.1 rejection and cachedpool override tests. Scoped diff--check PASS; stale6sassert search tests/servicesAI clean. No real provider invocation, API restart, live shop mutation or Git actions. Root/Chengetai own independentgate/activation.

## Assigned by Mutungamiri — 2026-11-02 MUSE-INSIGHT-SCHEMA-001
Owner latest insights invalidresponse. Verified17:41UTC providerbusinessinsight returned insight/evidence_ids only; systemprompt omitted exactschema although boundaryrequires6fields. Fix providerprompt/schema grounded exactbusinessinsight response structure+types/enum/null action; preservestrictvalidation/no looseaccept arbitraryprovider. Scope services/ai/muse.py,boundary.py,AI tests only. FollowAGENTSactivation6brains/docs/board. Add capturedshape regression demonstratesproperoutgoinginstructions/validfullresponseaccepted/invalidstillrejected. Othercatalogue24s/25s unchanged. No realcloud/liveAPIrestart. Persistbrainhandoff/tests. APIworkparallelHwaro separatefiles.

## 2026-11-02 — MUSE-INSIGHT-SCHEMA-001
- Root assigned confirmed business-insight provider shape mismatch: outgoing JSON-mode prompt omitted the boundary's six-field schema, while actual provider returned only insight/evidence_ids. Scope services/ai/muse.py,boundary.py,test_muse.py and own memory; activation context reloaded. API repair parallel Hwaro separate files.
- MetaMuseProvider now appends business_insight output_schema to the actual system message. StructuredAI.business_insight supplies complete exact-object schema: required kind/title/summary/evidence_ids/confidence/suggested_action; allowed kind enum excluding unavailable; bounded nonempty strings, supplied evidence-ID enum/min1, confidence number0..1. Prompt explicitly forbids insight extra field and null suggested_action, retaining current strict nonempty-string validator rather than relaxing provider acceptance. Other task prompts, catalogue24s/HTTP25s and all validators unchanged.
- Tests: isolated escalated python -m pytest services/ai -q -p no:cacheprovider --basetemp .pytest-insight-schema-ungwaru =>76passed1.64s. Actual adapter fakeHTTP outgoing message parsed to assert complete transmitted schema and valid response acceptance. Captured partialshape regression plus null action, extra field, invented evidence, unsupportedkind, stringconfidence still fallbackinvalidresponse. Scoped diff--check PASS (CRLF warnings only).
- No actual cloud invocation, live API restart, shop mutation or Git changes. Root/Chengetai own independent QA and runtime activation; live provider compliance is not guaranteed by fakeHTTP tests. No active test processes. Next verify real next owner insight and investigate sanitized trace if provider still violates schema.

## Assigned by Mutungamiri — 2026-11-02 PAPER-DAILY-OCR-001
Owner explicitcombineddailyhandwrittenproductlist→review→record, policy docs/finance/policy-PAPER-DAILY-REVIEW-001.md. Ungwaru AI specialist singlewriter services/ai/handwritten_sales.py/newfocusedAItests +newcontractdocs withinservices/ai only (temporary docs there allowed), NOapp.py/voicecatalogue changes (Hwaroowns). LoadAGENTS role6brains sharednewacceptance/policy board. Buildreview-only Meta image extraction adapter with groundedcatalogue knownIDs nullableunknowns/rawlabels/positiveqty/pricesiflegible otherwiseNone; no guesses/tender inference/customertransactions. Boundedimagevalidation pngjpegwebp max5MiB, dataURLbinarysanitization/no rawimageeventoutput; promptimagesuntrustedinstructionsasdata. Reuseexistingsettings/tls/MetaChat tracing whereappropriate, explicitconfiguredvisionmodel no fictitiousOCRfallback. CanGETmodelsmetadata andsyntheticNON-userimage smoke onlyifneeded authorisedlowrisktest; neverrealcustomer/shopdata oruserimage/cloud automatically. Verify fakeprovider/schema/imagebadinput, writeexactPythoninterface+contractHwaro andRunako immediately. ExistingMuse24/25voice unchanged. No livefinancialposts/APIrestart/package/Git. Persisthandoff/checkpoints; realvisioncapabilityunverifiedmustsay.

## Assigned by Mutungamiri — PAPER-DAILY-OCR-001 extension
Ungwaru solewriter services/api/requirements.txt may add Pillow for bounded decodedimagevalidation (5MiB/16MP/singleframe); Hwaro must not touchsamepath concurrently. Sharedacceptance path docs/capture-sharing-acceptance.md. OCRdraftsha256metadata consumedbybackend topreventsource duplicates. Existing configuredvisioncapabilitymustnotbefaked.

## 2026-11-02 — PAPER-DAILY-OCR-001
- Activated current AGENTS/role/sixbrains/task, capture-sharing-acceptance, Ruzivo policy and latest board. Scope ONLY new AI handwriting adapter/tests/contract; root explicitly extended services/api/requirements.txt solewriter for Pillow>=11,<13. No app.py/cataloguevoice/frontend changes; Hwaro/Runako received exact interface early.
- New services/ai/handwritten_sales.py: extract_handwritten_sales(bytes,MIME,catalogue)->frozen HandwrittenSalesDraft; validatedoriginalbytes SHA256, statusreview/unavailable, raw labels plus nullable knowncatalogueID/wholeqty/unitpricecents/linetotalcents, warnings/provenance/reason. Full decode PNG/JPEG/WebP MIMEagreement, singleframe<=5MiB<=16MP. Image invalidraisesValueError beforeprovider; missingPillow RuntimeError. Strict row/key/type/allknownID/amountmath output validation, unknown/illegible valuesnull, no date/payment/customerreceipt/cost inference or unwritten amount calculation. No mutations; manualreview required.
- Existing explicit LLAMA_VISION_MODEL/key/verifiedTLS reused; no textmodel fallback. Separate2worker/2inflight24souter25sHTTP, bounded lingering calls/no retries, connectionpoolcached. Safe traces replace image with contenttype/size/omittedmetadata; rawbase64 also explicitsecretsredaction. Providerreturned output is untrusted review only. Contract services/ai/HANDWRITTEN_SALES_CONTRACT.md documented forbackend/UI,35sclientrecommended.
- Tests: fullAI101passed1.27s isolatedfakeHTTP/syntheticimages. Tests include known+nullableunknownrows, no inventedfield fill, invalidIDs/quantities/bools/decimalprices/negative/mismatchedamounts/extra fields, imageformats/MIMEmismatch/oversizebytes/pixels/multiframe/truncation, unconfiguredmodel, emptyreadwarnings, actualHTTPpayload+correlatedtrace noimage/key, busy/timeoutno retries. First run100passed2setup errors were pytest implicitbinaryparameterIDs exceeding Windows tempfilepath; explicitshortIDs finalpass. Scoped diffcheckPASS.
- Permitted lowrisk actualcapability check: GET Meta/v1/models returned200 with configuredmuse-spark-1.3 entry, metadata lackedmodalitydeclaration. Generated ONLY syntheticprintedimage fakeBread Qty2 Unit1.80 Total3.60 with fakecatalogue synthetic-bread; actualMeta review returnedproductID/qty2/price180/total360,warningsnone in3.855s. Traces separate ignoreddata/qa-handwritten-synthetic-provider.sqlite3. No actualuser/shopdata/image uploaded. Confirms syntheticprintedimage support only, NOT handwriting/photoaccuracy. No livefinancial/APIrestart/package/Git actions.
- Outstanding: root/Hwaro integrate APIreview/confirm/batch/policy guards; Runako UI; independentQA andRuzivofinalgate; Owner realhandwritingphoto physicalacceptance. Sourcefrozen and no runningtests; handoffready.
