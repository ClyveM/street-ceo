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
