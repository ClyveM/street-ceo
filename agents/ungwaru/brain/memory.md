# Ungwaru — Memory

Initialized 2026-10-29. No prior sessions; no work performed yet.

## Project facts (confirmed)

- Street CEO hackathon MVP; deadline November 4, 2026.
- Meta models / Llama integrations for business insights and reasoning.
- No application code exists yet; no model selected yet.

## Stable context

- Role: `agents/ungwaru/role.md`. Activation protocol: `AGENTS.md` section 2.
- Rule: structured, schema-validated outputs for every AI feature consumed by code.
- Serves Inzwi (NLU options) and Chiono (reasoning over metrics).
- Model choices need Mutungamiri approval with cost/latency envelope.

## Verified implementation facts (2026-10-30, W1-UNGWARU-001)

- `services/ai/boundary.py` exposes a provider-neutral `Provider` protocol and
  `StructuredAI` facade. Providers return mappings only; callers receive typed
  results or explicit fallbacks.
- Sale intents and business insights reject unknown fields and invalid values.
  Insight responses must cite IDs from the supplied evidence snapshot.
- No live Meta/Llama credentials, SDK installation, deployment target, or
  successful model request was observed in this workspace.
- Official evidence recorded in `services/ai/capability_matrix.py` supports
  Llama 3.1/4 structured tool-call formats and the official Llama API Python
  client's timeout/error/retry behavior. This is capability evidence, not live
  availability evidence.

## Verified implementation facts (2026-10-30, W3-MUSE-001)

- `services/ai/muse.py` sends structured requests to the configured
  `https://api.meta.ai/v1/chat/completions` endpoint without exposing the key
  to the browser.
- `POST /api/v1/shops/{shop_id}/muse` returns period-filtered repository
  evidence and validated Meta output for non-financial questions.
- Profit/margin questions return `needs_data` until COGS and operating expenses
  are present; sales revenue is never treated as profit.

## Verified implementation facts (2026-10-31, W4-SOCIAL-001)

- `StructuredAI.social_draft` accepts only explicit `SocialProduct` inputs and
  validates selected product IDs and factual claim source fields.
- The social provider prompt is draft-only and prohibits unsupported discounts,
  stock, popularity, location, customer-result, and availability claims.
- An optional `shop_image_ref` is passed as visual context metadata only; the
  current boundary does not claim to inspect or infer facts from the image.

## Verified implementation facts (2026-10-31, W4-MUSE-IMAGE-001)

- The configured repository path currently uses `LLAMA_MODEL` with the text
  chat-completions adapter; no `MUSE_IMAGE_MODEL` setting is present.
- Official Meta documentation identifies `muse-image-1.0` and separate image
  generation/edit endpoints. This capability is recorded as verified by docs
  but unavailable in this workspace until explicitly configured and smoke-tested.
- `SocialImageRequest` accepts selected products and URL/data/file image refs;
  local filesystem paths are rejected. `SocialImageDraft` is always draft-only.

## Verified implementation facts (2026-10-31, W6-MUSE-PROVIDER-WIRING-001)

- `MetaInvoiceVisionProvider` now preserves both `file-` and `file_` invoice
  references as Meta `file_id` content parts for PDF extraction.
- This environment had no active LAN listeners on ports 8000, 5173, or 9001;
  no live LAN API result was observed during this checkpoint.
