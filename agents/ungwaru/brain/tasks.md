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
