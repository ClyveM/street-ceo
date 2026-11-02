# Backend-local voice input contract

These endpoints are the browser microphone boundary. They are shop-scoped,
read-only with respect to sales, and require `Idempotency-Key` so retries do
not create competing interpretation requests.

## Transcript

`POST /api/v1/shops/{shop_id}/voice/transcript` requires `X-Shop-ID` matching
the path and accepts `{ "transcript": "..." }` with a maximum of 1,000
characters. The response is a bounded object containing `request_id`,
`shop_id`, `input_kind`, `status`, optional transcript, optional normalized
intent, optional resolved `lines`, `error`, and `error_code`. A `record_sale`
intent is confirmation-only; exact matches use `status: "needs_confirmation"`,
while uncertain proposals use `needs_match_confirmation`. This endpoint never posts a
sale. A typed command containing multiple quantity/name pairs, such as
`2 coke 2 sugar`, is resolved only against the shop catalogue: `coke` maps to
`Coca-Cola 300ml` and `sugar` maps to `Sugar 1kg` in the seeded demo catalogue.
No price or stock fact is invented. The response remains confirmation-only.

## Confirmed voice sale

`POST /api/v1/shops/{shop_id}/voice/commit` is the commit boundary. It requires
`X-Shop-ID`, `Idempotency-Key`, `{review_id, lines, tender?, amount_received_cents?, match_confirmed?}`.
Tender accepts only `cash` or `bank` when supplied. The `review_id` must refer to a preceding
confirmation-ready transcript response, and the submitted lines must match
that reviewed basket. The backend resolves every product ID inside the shop,
checks stock before mutation, persists through the configured sale repository,
decrements stock at that boundary, and returns the normal `Sale` response with
`total_cents`, authoritative `stock_after`, `amount_received_cents`, and
`change_cents`. A missing review,
changed basket, or insufficient stock returns `409`; a missing product returns
`404`; a reused key with a changed payload returns `409`. Exact retries return
the original sale without decrementing stock again. This route is separate
from transcript interpretation, so a UI confirmation must call it;
interpretation alone never posts a sale.

Each review permits one successful commit. A second key for that review returns
`409`; recovery must retry the original key and exact request. The original
receipt replays even if catalogue prices subsequently change. This review-to-sale
binding persists with the reviewed response and receipt in the selected SQLite demo store.

There is no separate match-confirmation endpoint. The commit accepts a prior
`needs_confirmation` review or a `needs_match_confirmation` proposal approved
with strict boolean `match_confirmed:true`. A proposal requires explicit spoken
yes before tender/payment; missing approval returns `409` with
`detail.code: "match_confirmation_required"`. Commit requires
the same product IDs and quantities, a shop-scoped catalogue, sufficient
stock, and an idempotency key. If tender is missing or ambiguous, the endpoint
returns a structured `needs_tender` response with the allowed modes and the
amount due; it does not post a sale. For cash, `amount_received_cents` is
required, must be at least the integer-cent total, and exact change is returned.
For bank, the amount is treated as the exact total (a supplied amount must
match). The normal sale receipt ID and authoritative `stock_after` are returned.

`POST /api/v1/shops/{shop_id}/voice/commit/{sale_id}/undo` is the explicit
reversal path. It requires `Idempotency-Key`, `{actor, reason, confirmed:true}`,
accepts only a sale created through the voice commit boundary, restores the
original quantities, and returns a separate `reversal_id`/`audit_id` receipt.
Exact retries replay the reversal; changed retries return `409`; a second
reversal of the same sale returns `409`. The demo stores the reversal
audit in the selected SQLite demo store; no refund or financial ledger posting is inferred.

## Scoped quantity-only clarification

`POST /api/v1/shops/{shop_id}/voice/transcript` also accepts optional
`clarification_of`, the request ID of a preceding `needs_clarification` response
inside the same shop. A safely grounded single-product missing-quantity response
includes optional `clarification_product_id`, `clarification_product_name` and
`clarification_product_sku` snapshots, plus `clarification_code: "missing_quantity"`.
Its question can ask for just the quantity; another Apo or complete basket is
unnecessary. Example follow-up: `{ "transcript": "one", "clarification_of": "<id>" }`.

Bare replies accept positive integers 1–9999 or words one–twenty, with optional
terminal sentence punctuation. The server reuses the stored product ID without
another resolution call, checks current stock and returns a grounded
`needs_match_confirmation` proposal. Explicit yes remains mandatory before any
payment/commit. No quantity is defaulted and no sale occurs during clarification.

Only a qualified unique exact alias or the narrowly qualified observed chips
phrase after a completed validated single-product Muse match can supply the safe
target. Generic plausibility, unknown extra words,
multi-item baskets and provider failure do not receive this shortcut. Missing
context or deleted/renamed product names/SKUs return `409`; insufficient stock
returns a clarification question without mutation. Use a new idempotency key for
each follow-up; exact retries replay, changed payloads conflict.

The three snapshot fields default to null for older persisted responses. Such
responses retain their original transcript and validated resolver fallback;
the server never extracts an assumed product ID from question text. Omitted or
false `match_confirmed` preserves existing paid-request fingerprints.

## Audio

`POST /api/v1/shops/{shop_id}/voice/audio` accepts JSON
`{ "audio_base64": "...", "media_type": "audio/webm" }`, limited to 5 MiB
decoded audio. The backend validates and fingerprints the bytes but does not
store or post them. Until the audio-to-transcript provider is available it
returns `status: "unavailable"` and `error: "audio_transcription_unavailable"`.

Both endpoints replay the original response for an exact key/payload match and
return `409` for a changed payload. Missing/mismatched shop scope returns
`403`; missing idempotency returns `400`; disabled voice input returns `404`.

Meta credentials are read only by the server-side Meta Llama adapter from
`LLAMA_API_KEY`/`LLAMA_MODEL`; they are never accepted from the browser or
returned in a response. Provider failures are bounded to a stable `error_code`
plus a human-readable safe `error`; raw provider exceptions and internal
validation text are never returned.

## 2026-11-02 — RETAIN-BASKET-API-001
- VoiceTranscriptRequest transcript budget is 16,000 characters; catalogue interpretation and actionable basket support at most 100 item segments/lines (catalogue at most 200 products). Over-limit input never posts partial items.
- VoiceResponse additive retained_lines: VoiceSaleLine[] and pending_items: [{slot_id:int 0..99, heard:string <=500, quantity:int>=0|null, product_id:UUID|null, product_name:string|null}]. Combined retained+pending <=100, unique slots. Retained lines have independently grounded catalogue IDs/explicit positive quantities, but are NOT actionable. On needs_clarification, actionable lines=[] and no voice review is registered. Existing/older clients cannot commit a partial retained basket.
- First pending item is the active question. Missing quantity with known product accepts a bare positive quantity. Unknown product with known quantity accepts just the corrected product name (original explicit quantity reused); a reply with explicit quantity may correct it. One focused item only, never a whole basket in this reply. Full repeats/multi-item replies remain non-actionable and preserve context.
- Send clarification_of=latest response.request_id using a stable Idempotency-Key. Server merges one resolved item with retained lines, asks next pending item, and persists the context in SQLite. Exact retry returns the original response. Different request key against an already-consumed retained parent context returns409; continue latest context, never fork silently. Pending duplicate replacement does not overwrite/add the same retained product or silently remove the slot.
- Once every pending slot resolves, server returns the complete merged lines[] with needs_match_confirmation and requires_match_confirmation=true. Full basket is displayed; explicit match_confirmed=true is required before tender/payment commit. Current catalogue existence/stock is rechecked and normal sale commit/idempotency guards remain. No partial sale is posted.
- Cancel abandons the entire client flow. No skip/remove command is offered or inferred; unmatched items remain pending. Deleted retained/target products or insufficient stock block with409 rather than dropping items. A new basket may be explicitly started after cancellation.
- Muse unavailable/failed checks preserve independent local matches and pending slots. Provider-derived retained matches still pass catalogue plausibility/uniqueness and exact independently extracted quantity validation. Invalid response never becomes an executable partial basket. Source/provider_called remain honest for each resolution step.

2026-11-02 QA amendment: exact 'remove this item'/'remove item' explicitly removes only the active pending slot; final retained basket still requires Yes, empty basket rejects without sale. No generic skip inferred. Trailing and/plus reply remains unresolved; pending quantity target now saves product_sku and enforces name/SKU stale guard. This supersedes the earlier no-remove-offered paragraph.
