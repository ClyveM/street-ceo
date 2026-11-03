# Ungwaru — Current State

Updated 2026-10-31 after W4-MUSE-IMAGE-001.

## Status

W4-SOCIAL-001 AI boundary completed in owned scope; API and frontend wiring
remain integration dependencies.

W4-MUSE-IMAGE-001 image boundary completed in owned scope; image-provider
configuration and API/frontend wiring remain integration dependencies.

## Work in progress

- `services/ai/muse.py` provides the server-only Meta/Llama adapter through the
  existing `LLAMA_API_KEY` and `LLAMA_MODEL` settings.
- `POST /api/v1/shops/{shop_id}/muse` in `services/api/app.py` builds a bounded
  repository evidence snapshot and returns a structured answer.
- Ask Muse frontend still needs to call this endpoint instead of displaying its
  local request-captured placeholder.
- `services/ai/boundary.py` now exposes `SocialRequest`, `SocialProduct`, and
  draft-only `SocialDraft` validation for product-to-social content.
- `services/ai/test_social.py` covers valid drafts, unknown-product claims,
  prompt injection, missing products, and publish-status rejection.
- `services/ai/image.py` separates Meta Muse Image from the text-only Llama
  adapter and requires explicit `MUSE_IMAGE_MODEL` configuration.
- `StructuredAI.social_image` returns `provider_not_configured` when image
  access is not explicitly configured and enforces draft-only output.

## Latest verified results

- `python -m unittest discover -s services\\ai -p 'test_*.py' -v`: 6 passed.
- Same command after W3-MUSE-001: 9 passed.
- `python -m pytest services/ai/test_muse.py services/api/test_muse.py -q`: 5 passed.
- `python -m py_compile services/ai/muse.py services/api/app.py services/api/test_muse.py`: passed.
- `python -m py_compile services\\ai\\__init__.py services\\ai\\boundary.py services\\ai\\capability_matrix.py services\\ai\\test_boundary.py`: passed.
- `python -m unittest discover -s . -p 'test_*.py' -v` from `services/ai`: 15 passed.
- `python -m pytest services/ai/test_social.py services/ai/test_muse.py services/api/test_muse.py -q`: 11 passed.
- `python -m py_compile services/ai/boundary.py services/ai/muse.py services/ai/test_social.py`: passed.
- `python -m unittest discover -s . -p 'test_*.py' -v` from `services/ai`: 20 passed.
- `python -m pytest services/ai/test_image.py services/ai/test_social.py -q`: 11 passed.
- `python -m py_compile services/ai/boundary.py services/ai/image.py services/ai/test_image.py`: passed.
- Verified: strict schemas, prompt-injection quarantine, timeout fallback,
  provider exception fallback, evidence citation enforcement.

## Known blockers

- A live Meta/Llama network smoke test was not run in this task. The adapter is
  tested with an injected HTTP client; deployment still needs a reachable API
  and valid server-only credentials.
- The current shop repository has sales/products but no COGS or expense records,
  so profit and margin questions intentionally return `needs_data`.
- Runako must wire the Ask Muse form to the new endpoint; no frontend files were
  changed under this assignment.
- W4-SOCIAL-001 still needs Hwaro to expose a versioned social-draft API route
  and Runako to send selected catalogue products plus an optional image upload.
- Current `.env` exposes only the text model setting (`LLAMA_MODEL`); no
  `MUSE_IMAGE_MODEL` is configured. Image credentials/model entitlement remain
  unverified because no live image request was made.

## Next immediate action

Hwaro should expose the social boundary through a shop-scoped endpoint. Runako
should send `brief`, selected `SocialProduct` facts, optional `shop_image_ref`,
and duration, then display the returned editable draft as draft-only. Chiono
should review factual-claim policy before adding product-performance claims.
For image generation, Hwaro/Runako should use `SocialImageRequest`, display the
explicit provider-not-configured state, and only enable `muse-image-1.0` after a
credentialed staging smoke test.

## 2026-10-31 — W5-DEMO-READINESS-AI-001

- Audit evidence: 21 AI unittest cases passed; 14 focused API tests passed; 41
  web node tests passed; web production build passed.
- No live Meta claim: local port 8000 was inaccessible from this environment.
- Voice confirmation still stops at review and does not post a sale.
- Social image fallback labels differ between backend and frontend parser.


## 2026-10-31 — W6-DEMO-AI-001 fresh checkpoint
- LAN social draft and image generation returned real draft-only outputs.
- Direct Muse Spark synthetic invoice extraction succeeded with correct values.
- LAN invoice upload remains provider_unavailable: API upload does not invoke
  the adapter. Hwaro owns this integration blocker; no AI code fix indicated.
- Focused AI pytest suite: 30 passed. Exact live IDs/evidence in handoffs.md.
- Initial connection reset observed; sustained runtime reliability not proven.

## 2026-10-31 — W6-MUSE-PROVIDER-WIRING-001
- LAN verification from this environment found no listener on ports 8000,
  5173, or 9001; `/healthz` and OpenAPI could not be reached. No live LAN
  success is claimed.
- Fixed a proven invoice adapter mismatch: the boundary accepts both `file-`
  and `file_` provider IDs, while the Muse Spark PDF adapter only preserved
  `file-` IDs. Both forms now become `file_id` parts.
- Focused AI pytest suite: 31 passed; AI adapter compilation passed.
- API upload still needs Hwaro to invoke `extract_invoice_image`; this task
  intentionally did not modify `services/api/`.

## 2026-11-01 — DEMO-MUSE-TRACE-001
AI scope complete: durable redacted provider traces in services/ai/tracing.py; Muse chat wrapped and worker correlation copied. Final AI pytest: 51 passed. Root/Hwaro own voice/API integration and runtime QA. See handoff for contract, limits and next steps. No live provider/device verification performed.

## 2026-11-01 — SPRINT90-TRACE-003
Oversized trace events now retain sanitized bounded shop/investigation envelope. New real-file regression and Unicode/redaction/size test pass. Full AI suite 53 passed; scoped diff check passed. Root owns integrated API/host verification; no live restart.

### SPRINT90-TRACE-003 final envelope follow-up — 2026-11-01
- Parent requested API diagnostic fields status_code and error_type also survive oversized event truncation. Added both to the existing sanitized bounded envelope in services/ai/tracing.py and asserted their preservation in existing oversized regression.
- Fresh focused evidence: python -m pytest services/ai/test_tracing.py -q -p no:cacheprovider — 8 passed in 0.37s. No new features, API changes, live actions or escalations. Root final integrated tests remain parent-owned.

## 2026-11-01 — CATALOGUE-VOICE-MUSE-001
Catalogue-aware actual Muse fallback resolver implemented in AI scope; all nonexact proposals require confirmation and all item/quantity/ID coverage validates before any lines returned. Missing quantity/unknown/ambiguity no lines. 65 full AI tests passed, compile/diff checks passed. Parent owns live-provider smoke; API/voice UI integration remains Hwaro/Runako.

## 2026-11-02 — MUSE-OUTAGE-001
Confirmed8s resolver deadline discarded actual19.506s provider completion; not provider outage evidence. Raised default24s/max25 (<frontend30), differentiated honest timeout/busy/config/error prompts, preserved2worker limit/no-retry/all safety checks. Focused16/fullAI69passed; compile/diffPASS. Root owns backend activation/live acceptance; no live action here.

## 2026-11-02 — FAST-VOICE-001
Root-approved conservative exact-alias+boundedASRtail immediate proposals (mandatoryYes/source local_catalogue_proposal/providerfalse), immediate exactmissingqty question, remaining realMuse6smax/no retry, same2capacity. Providerpool reused/compactprompt. Focused21/fullAI74passed; final and/plus no-partial guard focusedrerunPASS. RootQA/runtime activation pending. No live actions.

## 2026-11-02 — DEMO-MUSE-WAIT-001
- Owner explicitly accepts longer demo Muse wait, superseding FAST-VOICE six-second provider deadline. Scope services/ai catalogue_voice.py/muse.py/tests only plus own memory; no backend/frontend/native or live changes.
- Catalogue resolver default/max now24s; its cached provider receives narrowly scoped HTTP25s override. build_muse_ai keeps general HTTP20s and StructuredAI20s defaults; catalogue calls provider directly under its24s outer deadline. Shared2worker/2inflight capacity, no retries, immediate local matching, item/quantity validation and required confirmation unchanged.
- Read-only frontend verification apps/web/src/quickSale.ts interpretation request timeout30s, sufficient for resolver24s + normal overhead. No APK rebuild needed for server-only budget update. Transport timeout is not a guarantee of provider latency; slow/unknown results still clarify honestly.
- Evidence: isolated escalated python -m pytest services/ai -q -p no:cacheprovider --basetemp .pytest-demo-muse-wait-ungwaru =>75passed1.27s. New builder test proves defaultHTTP20 vs catalogueHTTP25; updated resolver24/default boundary/max24.1 rejection and cachedpool override tests. Scoped diff--check PASS; stale6sassert search tests/servicesAI clean. No real provider invocation, API restart, live shop mutation or Git actions. Root/Chengetai own independentgate/activation.

## 2026-11-02 — MUSE-INSIGHT-SCHEMA-001
- Root assigned confirmed business-insight provider shape mismatch: outgoing JSON-mode prompt omitted the boundary's six-field schema, while actual provider returned only insight/evidence_ids. Scope services/ai/muse.py,boundary.py,test_muse.py and own memory; activation context reloaded. API repair parallel Hwaro separate files.
- MetaMuseProvider now appends business_insight output_schema to the actual system message. StructuredAI.business_insight supplies complete exact-object schema: required kind/title/summary/evidence_ids/confidence/suggested_action; allowed kind enum excluding unavailable; bounded nonempty strings, supplied evidence-ID enum/min1, confidence number0..1. Prompt explicitly forbids insight extra field and null suggested_action, retaining current strict nonempty-string validator rather than relaxing provider acceptance. Other task prompts, catalogue24s/HTTP25s and all validators unchanged.
- Tests: isolated escalated python -m pytest services/ai -q -p no:cacheprovider --basetemp .pytest-insight-schema-ungwaru =>76passed1.64s. Actual adapter fakeHTTP outgoing message parsed to assert complete transmitted schema and valid response acceptance. Captured partialshape regression plus null action, extra field, invented evidence, unsupportedkind, stringconfidence still fallbackinvalidresponse. Scoped diff--check PASS (CRLF warnings only).
- No actual cloud invocation, live API restart, shop mutation or Git changes. Root/Chengetai own independent QA and runtime activation; live provider compliance is not guaranteed by fakeHTTP tests. No active test processes. Next verify real next owner insight and investigate sanitized trace if provider still violates schema.

## 2026-11-02 — PAPER-DAILY-OCR-001
- Activated current AGENTS/role/sixbrains/task, capture-sharing-acceptance, Ruzivo policy and latest board. Scope ONLY new AI handwriting adapter/tests/contract; root explicitly extended services/api/requirements.txt solewriter for Pillow>=11,<13. No app.py/cataloguevoice/frontend changes; Hwaro/Runako received exact interface early.
- New services/ai/handwritten_sales.py: extract_handwritten_sales(bytes,MIME,catalogue)->frozen HandwrittenSalesDraft; validatedoriginalbytes SHA256, statusreview/unavailable, raw labels plus nullable knowncatalogueID/wholeqty/unitpricecents/linetotalcents, warnings/provenance/reason. Full decode PNG/JPEG/WebP MIMEagreement, singleframe<=5MiB<=16MP. Image invalidraisesValueError beforeprovider; missingPillow RuntimeError. Strict row/key/type/allknownID/amountmath output validation, unknown/illegible valuesnull, no date/payment/customerreceipt/cost inference or unwritten amount calculation. No mutations; manualreview required.
- Existing explicit LLAMA_VISION_MODEL/key/verifiedTLS reused; no textmodel fallback. Separate2worker/2inflight24souter25sHTTP, bounded lingering calls/no retries, connectionpoolcached. Safe traces replace image with contenttype/size/omittedmetadata; rawbase64 also explicitsecretsredaction. Providerreturned output is untrusted review only. Contract services/ai/HANDWRITTEN_SALES_CONTRACT.md documented forbackend/UI,35sclientrecommended.
- Tests: fullAI101passed1.27s isolatedfakeHTTP/syntheticimages. Tests include known+nullableunknownrows, no inventedfield fill, invalidIDs/quantities/bools/decimalprices/negative/mismatchedamounts/extra fields, imageformats/MIMEmismatch/oversizebytes/pixels/multiframe/truncation, unconfiguredmodel, emptyreadwarnings, actualHTTPpayload+correlatedtrace noimage/key, busy/timeoutno retries. First run100passed2setup errors were pytest implicitbinaryparameterIDs exceeding Windows tempfilepath; explicitshortIDs finalpass. Scoped diffcheckPASS.
- Permitted lowrisk actualcapability check: GET Meta/v1/models returned200 with configuredmuse-spark-1.3 entry, metadata lackedmodalitydeclaration. Generated ONLY syntheticprintedimage fakeBread Qty2 Unit1.80 Total3.60 with fakecatalogue synthetic-bread; actualMeta review returnedproductID/qty2/price180/total360,warningsnone in3.855s. Traces separate ignoreddata/qa-handwritten-synthetic-provider.sqlite3. No actualuser/shopdata/image uploaded. Confirms syntheticprintedimage support only, NOT handwriting/photoaccuracy. No livefinancial/APIrestart/package/Git actions.
- Outstanding: root/Hwaro integrate APIreview/confirm/batch/policy guards; Runako UI; independentQA andRuzivofinalgate; Owner realhandwritingphoto physicalacceptance. Sourcefrozen and no runningtests; handoffready.

## 2026-11-03 — W6-LOAN-FOLLOWUP-001
- Web build and 12 Muse tests passed. Reloaded local API passed five-turn Shona loan intake and repayment estimate. Final estimate uses English. See handoffs.md.
