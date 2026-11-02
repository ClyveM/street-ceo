# Ungwaru — Handoffs

## 2026-10-31 — W6-MUSE-PROVIDER-WIRING-001 — completed

### Assignment summary

Verified current LAN behavior for Muse Spark invoice OCR and social/image
provider paths, then fixed one proven AI-owned provider mismatch. The invoice
boundary accepted both `file-` and `file_` provider IDs, but PDF transport only
recognized `file-` and would incorrectly send `file_` IDs as inline file data.

### Files changed

- `services/ai/invoice.py` — preserve both accepted Meta file-ID prefixes as
  `file_id` content parts for PDF requests.
- `services/ai/test_invoice.py` — regression test for underscore-prefixed file
  IDs.

### Verification evidence

- Focused command: `python -m pytest services/ai/test_invoice.py services/ai/test_image.py services/ai/test_social.py services/ai/test_muse.py -q`
- Result: **31 passed**.
- Compilation: `python -m py_compile services/ai/invoice.py services/ai/test_invoice.py services/ai/image.py services/ai/boundary.py` — passed.
- LAN check: no listeners on ports 8000, 5173, or 9001; `/healthz` and
  `/openapi.json` were unreachable from this environment. No live LAN success
  or Meta entitlement is claimed.

### Outstanding issues / next action

- `services/api/app.py` still stores invoice uploads as `provider_unavailable`
  without invoking `extract_invoice_image`; Hwaro owns that integration change.
- Social draft and image routes already build provider boundaries, but a fresh
  LAN smoke test requires the API/dev server to be running and reachable.

## 2026-10-30 — W1-UNGWARU-001 — completed

### Assignment summary

Defined a provider-neutral, schema-first boundary for sale intent and
evidence-backed business insights, including prompt-injection boundaries,
timeouts, provider error handling, and tested fallbacks. Recorded the
Meta/Llama capability evidence without claiming live access.

### Files changed

- `services/ai/__init__.py` — public exports.
- `services/ai/boundary.py` — provider protocol, request contracts, validators,
  prompt boundary, timeout/error handling, typed fallbacks.
- `services/ai/capability_matrix.py` — verified-vs-unknown capability register
  with official evidence URLs.
- `services/ai/test_boundary.py` — six dependency-free tests.
- Own brain files: `memory.md`, `current-state.md`, `decisions.md`,
  `lessons.md`, `tasks.md`, and this handoff.

### Tests and results

- `python -m unittest discover -s services\\ai -p 'test_*.py' -v` — 6 passed.
- `python -m py_compile services\\ai\\__init__.py services\\ai\\boundary.py services\\ai\\capability_matrix.py services\\ai\\test_boundary.py` — passed.

### Outstanding issues

- No live Meta/Llama credentials, installed provider SDK, deployment target,
  smoke test, latency measurement, or cost measurement was available.
- The provider adapter and API endpoint remain to be selected and wired by the
  owner agents; this task intentionally did not implement API, voice, UI, or
  finance logic.

### Next-session instructions

- Obtain Mutungamiri approval for the provider and budget before adding an SDK.
- Hwaro should map the typed results to a documented API contract.
- Inzwi should pass bounded transcript text and retain confirmation before any
  sale endpoint call.
- Chiono should provide stable evidence IDs and consume only validated insights.
- Chengetai should include these tests in the repository-wide quality gate.

## 2026-10-30 — W3-MUSE-001 — completed

### Assignment summary

Diagnosed the Ask Muse placeholder: the Today screen was capturing the request
locally and never calling a backend AI route. Implemented a real, structured
Meta/Llama request path using the existing server-only `LLAMA_API_KEY` and
`LLAMA_MODEL` settings. The route uses repository sales evidence and refuses to
invent profit when COGS or expenses are absent.

### Files changed

- `services/ai/muse.py` — Meta-compatible provider adapter, environment-backed
  builder, bounded Ask Muse helper.
- `services/ai/test_muse.py` — provider, fallback, and configuration tests.
- `services/api/app.py` — `MuseAskRequest`, `MuseAskResponse`, period evidence
  construction, and `POST /api/v1/shops/{shop_id}/muse` integration.
- `services/api/test_muse.py` — API behavior tests for missing financial data
  and validated model responses.
- Own brain files: `current-state.md`, `tasks.md`, and this handoff.

### Tests and results

- `python -m unittest discover -s . -p 'test_*.py' -v` from `services/ai` — 9 passed.
- `python -m pytest services/ai/test_muse.py services/api/test_muse.py -q` — 5 passed.
- `python -m py_compile services/ai/muse.py services/api/app.py services/api/test_muse.py` — passed.

### Outstanding issues

- No live network request was made during this assignment; the adapter's HTTP
  contract is covered with an injected client, but runtime reachability and
  provider credentials still need deployment smoke testing.
- The current repository model has no COGS or expense records. Profit questions
  therefore return `needs_data` with explicit required inputs.
- Frontend remains on the local “Request captured” state until Runako wires the
  form to the new endpoint.

### Next-session instructions

- Runako: POST the existing Ask Muse question to
  `/api/v1/shops/{shop_id}/muse` with the normal `X-Shop-ID` header and render
  `status`, `answer`, and `missing_data`.
- Hwaro/Verengai/Chiono: expose source-backed COGS and expense evidence before
  changing the fail-closed profit behavior.
- Chengetai: include the focused tests in the release gate and perform one
  credentialed staging smoke test without logging the API key.

## 2026-10-31 — W4-SOCIAL-001 — completed

### Assignment summary

Implemented the safe Meta/Llama content-generation boundary for the Social
Update feature. The boundary accepts a bounded brief, explicitly selected shop
products, an optional shop image reference, and a requested duration. It returns
an editable draft only; it never publishes or schedules content.

### Files changed

- `services/ai/boundary.py` — `SocialProduct`, `SocialRequest`, `SocialClaim`,
  `SocialDraft`, strict social schema validation, and `StructuredAI.social_draft`.
- `services/ai/__init__.py` — public exports for social boundary types.
- `services/ai/test_social.py` — focused safety and provider tests.
- Own brain files: `current-state.md`, `tasks.md`, and this handoff.

### Tests and results

- `python -m unittest discover -s . -p 'test_*.py' -v` from `services/ai` — 14 passed.
- `python -m pytest services/ai/test_social.py services/ai/test_muse.py services/api/test_muse.py -q` — 11 passed.
- `python -m py_compile services/ai/boundary.py services/ai/muse.py services/ai/test_social.py` — passed.

### Outstanding issues

- No live network call was made; the existing Meta adapter is covered with an
  injected provider/client and still requires a deployment smoke test.
- The optional image is currently an explicit reference only. Image upload,
  storage, retrieval, and any multimodal model path belong to API/UI owners.
- No API endpoint or frontend UI was changed under this assignment, so the
  current Social Update placeholder will remain until integration is completed.

### Next-session instructions

- Hwaro: expose a shop-scoped social draft endpoint that maps API payloads to
  `SocialRequest` and returns the validated `SocialDraft` without publishing.
- Runako: replace the placeholder with product selection, optional shop-image
  upload, brief/duration inputs, and an editable draft preview.
- Chiono: provide only verified product-performance facts if analytics claims
  are later added; do not add “best-selling” or availability claims without
  evidence.

## 2026-10-31 — W4-MUSE-IMAGE-001 — completed

### Assignment summary

Investigated image-generation capability and separated it from the existing
text-only Llama path. Repository evidence shows the current runtime has
`LLAMA_MODEL` configured for chat, but no `MUSE_IMAGE_MODEL`; no live image
credential smoke test was performed. Official Meta documentation supports a
separate `muse-image-1.0` model through `/v1/images/generations` and
`/v1/images/edits`.

Implemented a safe, draft-only image contract for selected products and
optional shop/product image references. Missing image configuration returns an
explicit `provider_not_configured` response explaining that text-only Llama
cannot generate images.

### Files changed

- `services/ai/boundary.py` — `SocialImageRequest`, `SocialImageDraft`, image
  reference validation, `StructuredAI.social_image`, and draft-only checks.
- `services/ai/image.py` — explicit Muse Image settings, generation/edit HTTP
  adapter, and builder gated by `MUSE_IMAGE_MODEL`.
- `services/ai/__init__.py` — public exports.
- `services/ai/capability_matrix.py` — image capability status recorded as
  documented but unavailable here until configured/smoke-tested.
- `services/ai/test_image.py` — focused capability, endpoint, scope, and safety
  tests.
- Own brain files: `current-state.md`, `tasks.md`, and this handoff.

### Tests and results

- `python -m unittest discover -s . -p 'test_*.py' -v` from `services/ai` — 20 passed.
- `python -m pytest services/ai/test_image.py services/ai/test_social.py -q` — 11 passed.
- `python -m py_compile services/ai/boundary.py services/ai/image.py services/ai/test_image.py` — passed.

### Outstanding issues

- No live image-generation request was made; credentials and model entitlement
  remain unverified.
- Current `.env` has no `MUSE_IMAGE_MODEL`, so the built boundary correctly
  returns `provider_not_configured`.
- No API endpoint, upload handling, frontend preview, publishing, or Facebook
  integration was changed under this assignment.

### Next-session instructions

- Hwaro: expose a shop-scoped image-draft API route mapping product selection,
  image references, size, and output format to `SocialImageRequest`.
- Runako: display the explicit unavailable state and make the generated image
  editable before any future publish handoff.
- Deployment owner: configure `MUSE_IMAGE_MODEL=muse-image-1.0` only after
  confirming account access, then run a redacted staging smoke test.

## 2026-10-31 — W5-DEMO-READINESS-AI-001 — completed

### Audit result

`LLAMA_API_KEY` is set and `LLAMA_MODEL=muse-spark-1.3` is configured, but a
live Meta request was not verified because local port 8000 was inaccessible.
`MUSE_IMAGE_MODEL` is absent. No image output is claimed.

### Readiness

- Typed Muse: partial; route and safe fallback exist, live provider unverified.
- Apo/Napo: partial; interpretation and confirmation work, but confirmation
  does not post a sale. Manual basket sale is the reliable demo.
- Muse profitability: reliable limitation response; numeric profit is blocked
  by missing COGS and operating expenses.
- Social caption/draft: partial; backend draft route exists, visible UI still
  uses a verified brief/manual caption.
- Image generation: not ready; model is not configured and fallback labels
  mismatch between backend and frontend expectations.

### Exact setup and 3–5 minute demo

Keep the existing API key server-only and run one safe typed query against a
reachable backend. For image generation, add `MUSE_IMAGE_MODEL=muse-image-1.0`,
verify entitlement, and run a redacted smoke test. Connect COGS/expenses before
showing a numeric profit. For the demo: (1) connect and show live catalogue if
reachable, (2) complete a manual Coke/Sugar/Milk basket sale, (3) run a typed
stock query, (4) ask Muse for last-30-day profit and show the honest missing-data
answer, (5) verify products and show the editable/manual social draft, and (6)
label image generation unavailable unless its smoke test passes.

### Required owner actions

Inzwi must complete or clearly label voice sale posting; Hwaro/Runako must wire
the social caption route and align image fallback labels; deployment must verify
the Meta text and image providers without logging credentials.

## 2026-10-31 — Muse image configuration audit — completed

### Verified result

The repository contains `LLAMA_API_KEY`, but its configured model is
`muse-spark-1.3`, the existing text-chat model. Key presence alone does not
prove image-model entitlement, and no live image request was made. `MUSE_IMAGE_MODEL`
is currently absent.

### Implementation and evidence

- `services/ai/image.py` now exposes a redacted configuration audit that
  distinguishes missing model, unsupported model, missing key, and ready-for-
  smoke-test. It never claims live access from configuration alone.
- The documented image model is `muse-image-1.0`; generation and edit endpoint
  constants are recorded in the adapter.
- `python -m pytest services/ai/test_image.py -q` — 8 passed.

### Exact external blocker

Set `MUSE_IMAGE_MODEL=muse-image-1.0` server-side and restart the backend, then
run a real request. If it returns 401/403 or a model-access error, the Meta
Model API project/key needs Muse Image access or a separately issued key. The
repository cannot determine that entitlement without making the request.
## 2026-10-31 — W5-FINAL-IMAGE-001 — final provider verification
### Result
The real adapter and draft-only validation are implemented, but live generation
cannot be verified in this workspace because `.env` has `LLAMA_API_KEY` and
`LLAMA_MODEL=muse-spark-1.3` while `MUSE_IMAGE_MODEL` is absent. The redacted
configuration audit returned `missing_model`; no image URL is claimed.
### Provider contract
Verified against Meta's official Muse Image documentation: model
`muse-image-1.0`; `POST https://api.meta.ai/v1/images/generations` for prompt-only
generation and `POST https://api.meta.ai/v1/images/edits` when selected product
or shop references are supplied. The adapter sends JSON with `model`, `prompt`,
`n`, `size`, and `output_format`, plus `images` containing URL/data URL/file ID
references for edits. It accepts only a returned `data[0].url` or
`data[0].b64_json` and never fabricates an output URL.
### Tests
- `python -m pytest services/ai/test_image.py -q` — 8 passed.
- `python -m pytest services/ai -q` — collection blocked by the pre-existing
  `test_boundary.py` discovery import (`from boundary import ...`); the focused
  image suite remains green.
### Exact user setup action
Add `MUSE_IMAGE_MODEL=muse-image-1.0` to the backend `.env`, restart the API,
and run one real draft request. A 401/403/model-access response means the Meta
project/key needs image-model entitlement or a separately issued credential;
configuration alone cannot establish that permission.

## 2026-10-31 — Muse Spark invoice vision — completed

### Provider verification

The existing Meta credential supports `muse-spark-1.3` image and PDF input.
Official Meta documentation specifies `POST https://api.meta.ai/v1/chat/completions`
with image input as an `image_url` content part and PDF input as a `file` content
part containing inline `file_data` plus `filename` (or an uploaded `file_id`).
Muse Spark 1.3 is documented as accepting text, image, and PDF input and
returning text.

### Configuration

Configured server-side in `.env`:

```env
LLAMA_VISION_MODEL=muse-spark-1.3
```

The existing `LLAMA_API_KEY` remains server-only. No separate IP or provider
credential was required.

### Live evidence

- Synthetic PNG invoice fixture through the real adapter: `source=provider`,
  `status=review_required`, `model=muse-spark-1.3`, two extracted lines, and
  `review_only=true`.
- Synthetic PDF invoice fixture through the real adapter: same successful result
  and structured lines.
- No stock, product cost, or invoice confirmation mutation occurred.

### Implementation and tests

- `services/ai/boundary.py` — strict invoice schema, image/PDF validation,
  deterministic catalogue product suggestions, and review-only result contract.
- `services/ai/invoice.py` — Muse Spark image/PDF adapter using the verified
  Chat Completions content-part format.
- `services/ai/__init__.py` and `services/ai/test_invoice.py` — exports and
  focused tests.
- `python -m pytest test_invoice.py test_boundary.py test_muse.py test_image.py test_social.py -q`
  from `services/ai` — **38 passed**.

Product matches are suggestions only (`suggested_product_id`,
`match_status="suggested"`) and require the existing human review/confirmation
workflow before any stock or cost mutation.

## 2026-10-31 — W6-OCR-LLAMA4-001 — release gate completed

### Final verification

- Authenticated `GET https://api.meta.ai/v1/models` returned HTTP 200.
- The existing key exposes Muse models, including `muse-spark-1.3`, but no
  Llama 4 Scout model ID. `LLAMA_VISION_MODEL` is unset.
- A safe 1x1 PNG fixture sent to the official image-input chat endpoint with
  `model=muse-spark-1.3` returned HTTP 200, a JSON response, and a populated
  `choices[0].message.content`. This verifies the existing key and hosted
  image-input endpoint, but it does not verify Llama 4 Scout access.
- No fake OCR output, invoice line, stock update, or cost update was created.

### Exact contract and configuration

The supported endpoint is `POST https://api.meta.ai/v1/chat/completions` with a
user message containing an `image_url` part and `response_format:
{type: json_object}`. The review-only extractor is gated by:

```env
LLAMA_API_KEY=your_server_side_meta_key
LLAMA_VISION_MODEL=<exact model id returned by GET /v1/models>
```

No Scout slug was guessed or added. Meta must first expose a Scout model to the
project. No separate IP is required for the hosted API.

### Tests

- `python -m pytest test_invoice.py test_boundary.py -q` from `services/ai` —
  **18 passed**.

### Release blocker and user action

The invoice boundary is implemented and review-only, but the requested Scout
configuration is blocked by account/model access. In the Meta Model API
project, request/enable hosted Llama 4 Scout access, then run `GET /v1/models`
and place the exact returned Scout ID into `LLAMA_VISION_MODEL`. Until that ID
appears for this key, invoice image extraction must remain unavailable rather
than falling back to fake OCR or an unapproved model.

## 2026-10-31 — Invoice image vision audit — completed

### Provider verification

The authenticated Meta Model API catalog was queried with the existing server
key via `GET https://api.meta.ai/v1/models`.

Returned model IDs included `muse-wonder-1.0`, `muse-spark-1.3`, and
`muse-image-1.0`, but no Llama 4 Scout model ID. The official Llama 4 model
documentation describes Scout as multimodal, but does not provide a hosted
Meta Model API slug that this key can use. Therefore no Scout identifier was
guessed or written to `.env`.

The hosted API uses `https://api.meta.ai/v1/chat/completions` with a user
message containing an `image_url` content part and `response_format:
{type: json_object}`. This is compatible with the review-only invoice boundary,
but it cannot be enabled until Meta exposes an image-capable model ID to the
project.

### Implementation

- `services/ai/boundary.py` — invoice image request, bounded line extraction,
  review-only validator, and safe `StructuredAI.invoice_extract` method.
- `services/ai/invoice.py` — Meta chat-completions image adapter and builder
  gated by explicit `LLAMA_VISION_MODEL` plus `LLAMA_API_KEY`.
- `services/ai/__init__.py` — public exports.
- `services/ai/test_invoice.py` — image request shape, review-only enforcement,
  missing configuration, and unsafe input tests.

No invoice is confirmed, product matched, stock changed, or cost changed by
this boundary. Human review remains mandatory.

### Tests

- `python -m pytest test_boundary.py test_invoice.py test_muse.py test_image.py test_social.py -q`
  from `services/ai` — **36 passed**.

### Exact setup blocker and action

The current key requires hosted model access before configuration. Do not set a
guessed Scout name. In Meta Model API, enable/request a multimodal Scout model
for this project, then copy the exact ID returned by `GET /v1/models` into:

```env
LLAMA_VISION_MODEL=<exact model id returned by Meta>
```

Keep `LLAMA_API_KEY` server-side. No separate IP is required for the hosted API;
only the project/key's model entitlement must be present. Hwaro/Dura should wire
the resulting review-only extraction into the existing invoice review endpoint.

## 2026-10-31 — W6-RETAIL-INSIGHTS-AI-001 — completed

### Contract

Added a provider-neutral retail insight contract for confirmed purchase, cost,
supplier, price, stock-count, stock-movement, and cash-close evidence. Allowed
insight kinds are `cost_increase`, `savings_opportunity`, `supplier_change`,
`price_change`, `stock_variance`, and `cash_close_anomaly`.

Only confirmed numeric evidence with unique IDs, bounded sources, units, and
periods is accepted. Missing required inputs produce an explicit unavailable
result that names the missing records; no savings, profit, variance, or cash
claim is fabricated. Provider outputs must cite supplied evidence IDs and are
rejected safely when their schema or citations are invalid.

### Files changed

- `services/ai/boundary.py` — `RetailEvidence`, `RetailInsightRequest`,
  `RetailInsight`, validators, and `StructuredAI.retail_insight`.
- `services/ai/__init__.py` — public exports.
- `services/ai/test_boundary.py` — confirmed cost increase, missing monthly
  COGS/expenses, unconfirmed/missing values, and unsafe savings tests.

### Tests

- `python -m pytest test_boundary.py test_muse.py test_image.py test_social.py -q`
  from `services/ai` — **32 passed**.

### Hwaro handoff

Hwaro should map purchase capture and monthly-analysis records into
`RetailEvidence` with stable evidence IDs and `confirmed=True` only after the
corresponding repository/ledger record is committed. Supply `missing_data` for
COGS, expenses, supplier comparisons, stock counts, or cash-close inputs that
are not present; do not substitute inferred values.

## 2026-10-31 — W5-VOICE-TEXT-PARSE-001 — completed

### Diagnosis

The sale boundary accepted only one `item` and `quantity` pair. A provider
response using a multi-line `items`/`lines` shape therefore failed strict
validation, and schema details could leak as the raw rejection reason.

### Changes

- `services/ai/boundary.py` — added bounded `SaleLine` support, catalogue
  canonicalization, explicit multi-item parsing, Apo/Napo wrapper handling,
  safe `items`/`lines` provider normalization, and a user-readable fallback.
- `services/ai/__init__.py` — exported `SaleLine`.
- `services/ai/test_boundary.py` — added tests for `1 coke 2 sugar`, the Apo
  script, unknown items, provider shape mismatch, and safe error handling.

Explicit commands are resolved against supplied catalogue names; unknown or
ambiguous products fail closed. Provider schema failures return the generic
`invalid_or_unsafe_provider_response` reason and do not expose raw provider
fields.

### Tests

- `python -m pytest test_boundary.py test_muse.py test_image.py -q` from
  `services/ai` — **22 passed**.

### Integration note

This assignment changed only `services/ai`. The existing voice/API adapters
still expose a single-line intent shape, so multi-line basket posting requires
the owning voice/API agents to consume `SaleIntent.items` in a follow-up task.

## 2026-10-31 — W5-FILM-READY-IMAGE-001 — completed

### Live evidence

- Added `MUSE_IMAGE_MODEL=muse-image-1.0` to the server `.env`.
- Real request to Meta returned HTTP 200 with `data[0].b64_json`.
- Real request through `generate_social_image` returned `source=provider`,
  `status=draft`, `provider=meta_muse_image`, `model=muse-image-1.0`, and a
  validated `data:image/...;base64,...` preview reference. No payload was logged.
- The returned image remains draft-only and is not published to Facebook.

### Fix and tests

The boundary previously rejected real base64 previews because its image-ref
limit was 4,096 characters. It now permits bounded image data URLs up to the
existing 12 MiB safety limit.

- `python -m pytest services/ai/test_image.py -q` — 9 passed.
- `python -m pytest services/api/test_social_data.py -q` — 6 passed.
- Hwaro's existing route maps the validated image reference to `output_url` and
  persists the draft record; no backend route file was changed in this task.

### Required runtime action

Restart the running API so it reloads `.env`, then use the social image route.
If the restarted runtime returns 401/403/model-access denied, the Meta project
or key needs Muse Image permission; the local configuration is otherwise ready.

## 2026-10-31 — W6-SOCIAL-SCHEMA-IMAGE-001 — completed with runtime blocker

### Schema fix

- `services/ai/boundary.py` — added `normalize_social_draft_payload` to safely
  pad a provider `shot_list` of one or two valid strings to the required
  three-to-eight range using deterministic product-grounded shots. Empty,
  malformed, or overlong lists still fail closed through the existing strict
  validator. The social prompt now explicitly requires three-to-eight shots.
- `services/ai/test_social.py` — added focused tests for safe short-list
  normalization and rejection of empty/malformed shot lists.

### Tests

- `python -m pytest test_social.py test_boundary.py test_muse.py test_image.py test_invoice.py -q`
  from `services/ai` — **40 passed**.

### Native-LAN runtime evidence

Requests were sent to `http://192.168.10.213:8000` with the demo shop and
selected catalogue products. The API listener was confirmed on `0.0.0.0:8000`.

- Social draft: HTTP **200**, public response `status=unavailable`,
  `provider=none`, `model=null`, warning `timeout`; no fabricated draft was
  returned.
- Image generation: one live call returned HTTP **200**, `status=draft`,
  `provider=meta_muse_image`, `model=muse-image-1.0`, with an output reference
  present and the existing draft-only warning. A subsequent live call returned
  HTTP **200**, `status=unavailable`, warning `image provider request failed`,
  and no output URL. The image payload was never logged or fabricated.

### Blocker / next action

The remaining demo blocker is runtime provider reliability/configuration, not
the shot-list schema: the social text call timed out and the image call is
intermittent. Hwaro should inspect the running API's provider timeout/upstream
error logging and restart/configure the runtime, then repeat both native-LAN
smoke tests and record stable HTTP 200 draft/output references.

## 2026-10-31 — FAST-TRACK W6-POINTS-AI — verified invoice vision and social generation

### Provider access evidence

- Authenticated `GET https://api.meta.ai/v1/models` returned HTTP **200** and
  included both configured model IDs: `muse-spark-1.3` and `muse-image-1.0`.
- Direct Muse Spark invoice-image request used
  `POST https://api.meta.ai/v1/chat/completions` with
  `model=muse-spark-1.3`, an image content part, and JSON response format. It
  returned HTTP **200**, `status=review_required`, `review_only=true`, zero
  extracted lines for the unreadable safe fixture, and one warning. No stock or
  cost mutation occurred.
- Direct image request used
  `POST https://api.meta.ai/v1/images/generations` with
  `model=muse-image-1.0`, `n=1`, `size=1024x1024`, and `output_format=png`. It
  returned HTTP **200**, one data item, and a real `b64_json` reference. The
  payload was not logged.

### Fixes

- `services/ai/muse.py` — passes trusted catalogue/evidence context into the
  Meta request, raises the bounded hosted-chat timeout to 20 seconds, and
  safely handles list content plus a single `{"text": "<json>"}` envelope.
- `services/ai/boundary.py` — social drafts now safely remove only a redundant
  provider `text` field when the required structured fields are present,
  normalize the same safe envelope inside claims, pad valid short shot lists to
  3–8, and continue rejecting malformed/unknown fields.
- `services/ai/test_muse.py` and `services/ai/test_social.py` — focused tests
  for trusted context, text-envelope normalization, social claim cleanup, and
  shot-list safety.

### Native-LAN final smoke evidence

- `POST http://192.168.10.213:8000/api/v1/shops/{demo_shop}/social/draft`
  returned HTTP **200**, `status=draft`, `source=provider`,
  `provider=meta_muse_text`, and **3** shot items. The route does not expose
  the model field; the authenticated provider request verified
  `muse-spark-1.3`.
- `POST http://192.168.10.213:8000/api/v1/shops/{demo_shop}/social/image-generation`
  returned HTTP **200**, `status=draft`, `provider=meta_muse_image`,
  `model=muse-image-1.0`, and a real `data:` preview reference of 3,245,754
  characters. The response retained the draft-only warning and was not
  published.

### Tests

- `python -m pytest services/ai/test_invoice.py services/ai/test_image.py services/ai/test_social.py services/ai/test_muse.py -q`
  — **30 passed**.


## 2026-10-31 — W6-DEMO-AI-001 — verification complete; API OCR integration blocked

### Assignment and scope
Verify current LAN invoice OCR and social/image generation; fix only proven AI
provider/schema defects. Scope: services/ai/ and own brain. No implementation
changes were justified. Existing uncommitted work was preserved.

### Fresh live evidence
- LAN http://192.168.10.213:8000/healthz: HTTP 200, status=ok.
- Live demo catalogue: HTTP 200, six products; demo shop ends 000001.
- Social draft: HTTP 200, id=cdcb8252-41f6-4c2f-9476-2a5aaf08d8af,
  status=draft, source=provider, provider=meta_muse_text, draft_only=true,
  three shots, no warnings; 16.0 seconds. Public route does not return model.
- Social image: HTTP 200, id=744bcb7e-5799-4c83-9ddc-14a45b636be1,
  status=draft, provider=meta_muse_image, model=muse-image-1.0,
  draft_only=true, output_url present; 14.4 seconds. Image payload not logged.
- Synthetic PNG invoice uploaded: HTTP 201,
  id=070a9112-c316-4f3d-a750-4f98a4d60946,
  extraction_status=provider_unavailable, zero lines. Warning says no OCR
  provider configured. No review/confirm endpoint was called.
- Direct configured invoice adapter: model=muse-spark-1.3,
  source=provider, status=review_required, review_only=true; accurately
  extracted Coca-Cola 300ml, quantity 2, line_total_minor=200,
  unit_cost_minor=100, no warnings, from a generated synthetic image.
- First social attempt had WinError 10054 connection reset; independent fresh
  connections then succeeded. This does not establish sustained reliability.

### Repository evidence and blocker
services/api/app.py upload_invoice stores bytes and hardcodes
extraction_status=provider_unavailable without invoking the working invoice
adapter. Current LAN OpenAPI exposes upload/review/confirm, no extraction
route. API wiring belongs to Hwaro; no API file was modified. Do not claim
end-to-end invoice OCR readiness from direct adapter success.

### Tests
python -m pytest services/ai/test_invoice.py services/ai/test_image.py
services/ai/test_social.py services/ai/test_muse.py -q — 30 passed in 0.30s.

### Next-session handoff
Hwaro should connect upload/extraction to the configured review-only adapter,
preserve human confirmation before stock/cost changes, and test the LAN upload
end to end. Chengetai should validate the resulting integration and provider
reliability. No credentials or image payloads were recorded.

## 2026-11-01 — DEMO-MUSE-TRACE-001 completed in AI scope
- Activation: read AGENTS.md, own role and all six brain files, architecture/API docs and master board. Confirmed write ownership services/ai and own brain only. Parent and Hwaro were sent the trace integration contract; no other product scopes edited.
- Assignment: keep sanitized durable Muse request/response records for investigation of online APK voice-sale MVP.
- Files changed: services/ai/tracing.py (new SQLite event store, sanitizer, correlation context, traced_call); services/ai/test_tracing.py (new disk/reopen, redaction, failure, bounds, worker-context tests); services/ai/muse.py (traced provider JSON requests/responses); services/ai/boundary.py (copy ContextVars into provider worker); services/ai/test_muse.py (isolated trace DB fixture); services/ai/test_boundary.py (repair existing bare import so root pytest can collect).
- Contract: trace_context(correlation_id, shop_id=None, operation=None); SQLiteTraceStore(path=None).record(mapping), .read(correlation_id=None, limit=100); sanitize_trace(value, secret_values=()); traced_call(operation=...,model=...,request=...,call=...,secret_values=(),store=None). call returns original provider JSON unchanged.
- Storage: STREET_CEO_TRACE_DATABASE or data/muse-traces.sqlite3; separate from shop DB to prevent nested-writer deadlock. Started event commits before call, completed/failed event afterward, shared trace_id and API correlation_id, UTC timestamps/model/operation/duration. HTTP exceptions preserve sanitized JSON error response/status; exception messages and non-JSON response text omitted. A completed provider response is not a business-success claim; API must log validation/commit outcome separately.
- Security: bounded/depth-limited JSON, credential keys/Bearer tokens/known provider key values/email/international phone/data URLs/binary content redacted or omitted. No raw audio or auth headers retained. Trace write errors fail the provider call; no untracked result proceeds. No credentials/PII in brain.
- Fresh verification: first root AI suite revealed pre-existing test_boundary bare import collection error; repaired within scope. Final python -m pytest services/ai -q -p no:cacheprovider: 51 passed in 0.63s. python -m py_compile tracing.py/muse.py/boundary.py: PASS. git diff --check -- services/ai: PASS (line-ending warnings only). Earlier focused tracing+Muse run: 11 passed.
- Outstanding: Hwaro owns API middleware correlation/request-response traces; root/Inzwi must wrap services/voice/meta_llama.py and meta_voice.py HTTP calls using traced_call. These files were inspected read-only. Root must ignore runtime data/*.sqlite3* files. Image/invoice-specific HTTP providers are outside exact voice-sale MVP trace integration unless parent expands scope.
- Limits: injected HTTP tests and real local trace-file reopen only; no live Meta/API/phone calls or claims. Parent must exercise actual API-to-provider correlation and read back persisted logs after backend restart. No production access/retention policy implemented; local logs are operational investigation artifacts, not agent memory.

## 2026-11-01 — SPRINT90-TRACE-003 completed
- Assignment/activation: loaded current AGENTS, own role/six brain files, architecture and master board/task; confirmed services/ai and own-brain write scope. Re-read prior trace handoff before starting.
- Bug: oversized SQLiteTraceStore.record payload fallback retained correlation but dropped shop_id; shop-filtered investigation endpoint could omit large events.
- Files changed: services/ai/tracing.py, services/ai/test_tracing.py plus own memory. Oversized fallback now preserves sanitized scalar metadata bounded to 256 characters: shop_id, operation, model, phase, source, provider_called, trace/correlation IDs, timestamps, HTTP status/duration. Arbitrary metadata objects cannot bypass sanitizer. UTF-8 prefix bounded by bytes, and SQL correlation index uses sanitized correlation value.
- Tests: python -m pytest services/ai/test_tracing.py -q -p no:cacheprovider: 8 passed. python -m pytest services/ai -q -p no:cacheprovider: 53 passed in 0.51s. git diff --check -- services/ai/tracing.py services/ai/test_tracing.py: PASS. New real-file reopen/shop-filter regression confirms oversized events remain discoverable; Unicode/credential/size-bound regression passes.
- Outstanding: root owns integrated API/host verification and release assessment; no API edits, live restart, provider call or escalation performed here. No full device/release approval implied.
- Next session: keep bounded envelope independent of payload truncation in any new trace store/export adapters; confirm API shop investigation route with an oversized synthetic event at integration level.

### SPRINT90-TRACE-003 final envelope follow-up — 2026-11-01
- Parent requested API diagnostic fields status_code and error_type also survive oversized event truncation. Added both to the existing sanitized bounded envelope in services/ai/tracing.py and asserted their preservation in existing oversized regression.
- Fresh focused evidence: python -m pytest services/ai/test_tracing.py -q -p no:cacheprovider — 8 passed in 0.37s. No new features, API changes, live actions or escalations. Root final integrated tests remain parent-owned.

## 2026-11-01 — CATALOGUE-VOICE-MUSE-001 completed in AI scope
- Activation: loaded updated AGENTS, own role/six brain files, current demo acceptance/architecture/API context and latest board/task. Read prior handoff; confirmed write scope services/ai plus own brain. Coordinated exact interface with Hwaro and Runako, no API/UI/voice writes.
- Files: services/ai/catalogue_voice.py (new), services/ai/test_catalogue_voice.py (new). Implements resolve_catalogue_voice(transcript, products, *, provider=default_actual_Muse, timeout_seconds=8.0) -> CatalogueVoiceResolution(status, lines tuple[CatalogueVoiceLine(product_id,quantity)], question, provider_called, source, reason, requires_confirmation=True). Passing provider=None explicitly selects unavailable/local clarification; injectable provider.complete(ProviderRequest) seam supports backend tests.
- Actual default: build_muse_ai().provider (MetaMuseProvider) receives bounded catalogue IDs/names/SKUs and locally derived explicit-quantity item segments. Existing provider tracing captures actual request/response/model and copied API correlation context. Prices/stock intentionally excluded from matching prompt because API remains price/stock authority. No model-generated question/prices consumed.
- Safety: require every segment exactly once; known IDs only; positive explicit integer quantities preserved, missing quantities remain null; extra fields, changed quantities, duplicate IDs/slots, unknown/unrelated substitutions, incomplete item coverage and ambiguous lexical ties yield no proposal lines. Empty trailing quantity is not dropped. Independent lexical floor rejects model mapping unrelated product to a real ID. All successful nonexact matches are confirmation-only; deterministic spoken question comes from validated catalogue names and explicit quantities.
- Samples via injected provider: '1 bread glove number' -> proposed 1 Bread loaf, confirmation required; '1 coca-cola nabo marble' -> proposed 1 Coca-Cola 300ml, confirmation required; 'coca-cola' -> How many question/no lines even if provider guesses quantity; '1 coke 1 unicorn' omitted/substituted/invented output -> no partial proposal. No actual provider smoke performed by this specialist; parent owns real provider sample investigation with no sale.
- Bounds: transcript <=1000 chars, catalogue <=200, <=20 segments, timeout (0,20] default8; shared 2-worker executor with 2-inflight semaphore bounds lingering timed-out calls and rejects additional work as provider_busy. No executor context manager waits through timeout. Explicit local/unavailable provenance never claims Muse success.
- Fresh tests: python -m pytest services/ai -q -p no:cacheprovider — 65 passed in 1.05s (includes 12 catalogue tests). py_compile new module PASS; scoped git diff --check PASS. Fake-provider tests cover hallucinated IDs, changed/bool/missing quantity, ambiguity, all-item coverage, failure/timeout, unfinished second item; real MetaMuseProvider with injected HTTP test covers durable correlated/redacted request/response.
- Outstanding: Hwaro must integrate API review statuses and match_confirmed commit gate; Runako must voice-confirm proposals before payment, ask clarification and never auto-post these proposals. Root owns live actual-provider smoke and physical-phone acceptance. No live calls, sale mutation, API restart or escalation performed here.

## 2026-11-02 — MUSE-OUTAGE-001 completed in AI scope
- Activation: read current AGENTS, own role/six brain/task, demo acceptance/architecture/API context and latest board. Read previous catalogue handoff. Scope confirmed services/ai plus own brain only; dependencies are root runtime activation and Chengetai independent QA. No API/UI/voice changes.
- Root cause independently verified by read-only metadata query of data/muse-traces.sqlite3, correlation e08ea619-ee82-4984-b5c6-eb31bad92f29: actual provider start 07:26:42.074 UTC; API returned needs_clarification with clarification_code timeout at 07:26:50.085 (~8058ms); provider eventually completed 07:27:01.591, duration19506.928ms. This proves an 8s local deadline discarded a later response, not provider outage. No raw user/provider content printed.
- Source finding: catalogue resolver default8s; MetaMuseProvider HTTP read budget20s; frontend interpretation request30s. API uses resolver default with no override. A late result remains non-actionable after the response; extending time alone does not make an unknown/ambiguous product match valid.
- Files changed: services/ai/catalogue_voice.py and services/ai/test_catalogue_voice.py. Default catalogue deadline24s, validated maximum25s; existing shared2worker/2inflight capacity gate, no retries and confirmation/quantity/all-item safeguards preserved. Timeout/busy/not-configured/general-error questions now distinct and state no sale recorded instead of declaring an outage. No framing/product alias changes: Apple ambiguity remains unresolved safely.
- Fresh evidence: focused catalogue suite16passed in0.37s; full AI suite69passed in1.81s; py_compile module PASS; scoped diff-check PASS. Added deterministic fake-future test asserts timeout24 without real waiting; busy test asserts no submission/retry, provider config/error/timeout copy tests and unknown Apple-framed no-partial regression. Existing missingqty/hallucinatedID/changedqty/ambiguity tests remain green.
- Handoff: sent stable checkpoint/controls to Chengetai (module _EXECUTOR/_CAPACITY, provider injection, timeout_seconds override). Root owns independent combined tests, actual-provider smoke if needed, and coordinated backend restart. Backend source repair alone does not require APK rebuild; no runtime activation performed by this specialist.
- Limits: no live calls, restarts or escalation. Twenty-second HTTP read timeout is not a strict end-to-end provider budget;24s outer deadline leaves nominal6s before client30s but connection/logging/DB overhead may consume it. Longer wait does not guarantee semantic resolution or responsiveness for every request. Late provider completion stays audit evidence only; no automatic commit/retry.

## 2026-11-02 — FAST-VOICE-001 AI scope complete
- Activation: reloaded current AGENTS, own role/six brain files, current demo acceptance/board/task and previous outage handoff. Write scope services/ai plus own brain; root approved design before matching semantics changed. Coordinated API/UI provenance with root/Runako and stable checkpoint with Chengetai.
- Design approval: immediate local proposal only exact unique catalogue alias plus exact bounded observed ASR suffix, every explicit quantity/item retained, mandatory spoken Yes/server match approval. Root latest decision deferred one-edit matching; no typo guessing implemented. No Apple/fruit stripping or arbitrary stop words.
- Files changed: services/ai/catalogue_voice.py, services/ai/test_catalogue_voice.py. Added allow_local_proposals=True optout for provider investigations. Proposed nonexact lines use source local_catalogue_proposal/provider_calledFalse/requires_confirmationTrue and existing proposed status; API must retain needs_match_confirmation and match_confirmed gate. No new API fields, no prices/tender inference.
- Local eligibility: exact alias from supplied catalogue only; suffix exactly empty/glove number/nabo marble/nabo/number/napo. If any discarded suffix could reference any catalogue item (lexical plausibility check), no immediate proposal. Ambiguous aliases, duplicate IDs, unknown/unexplained/Apple words, mixed unknown basket, missing second item and unfinished and/plus do not yield a local partial proposal. Exact single known product without quantity asks immediate local How many question, no lines.
- Provider path: remaining uncertainty gets one real Muse attempt default6s/max6s, replacing24s critical-path wait; same shared2workers/2inflight gate, no retries, no late result commit. Compact matching instruction preserves strict segment/known-ID/explicitqty validation. Cached provider keyed by immutable settings (max2, first-build lock) reuses existing HTTP/TLS pool; credentials remain process-memory only and existing traces redact outbound request/response.
- Fresh tests: focused catalogue21passed (final guard rerun0.36s); full AI74passed1.47s before final conservative and/plus guard, compile/scoped diff PASS. Existing provider schema/tracing tests now explicitly allow_local_proposalsFalse so they still exercise actual provider boundary. Added local immediacy/no-provider, strict mandatory-confirmation/provenance, exact missingqty, Glove/Number/Nabo/Marble catalogue collision, ambiguity/unknown/typo/no-partial and connection reuse tests. Root/Chengetai own independent integrated acceptance.
- Limits/dependencies: no live calls/restart/escalation. Root must activate backend and test ASGI/synthetic flow with no unwanted sale. Runako must label local proposal honestly rather than Muse. Connection reuse/compact prompt can reduce overhead but Meta generation latency remains variable; no guaranteed-fast model claim. Provider HTTP call may continue past6s; gate bounds lingering work and late results remain non-actionable audit only.

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
