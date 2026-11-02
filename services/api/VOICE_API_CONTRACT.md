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
intent always has `status: "needs_confirmation"`; this endpoint never posts a
sale. A typed command containing multiple quantity/name pairs, such as
`2 coke 2 sugar`, is resolved only against the shop catalogue: `coke` maps to
`Coca-Cola 300ml` and `sugar` maps to `Sugar 1kg` in the seeded demo catalogue.
No price or stock fact is invented. The response remains confirmation-only.

## Confirmed voice sale

`POST /api/v1/shops/{shop_id}/voice/commit` is the commit boundary. It requires
`X-Shop-ID`, `Idempotency-Key`, `{review_id, lines, tender?, amount_received_cents?}`.
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
binding is process-local in the current demo and does not claim restart durability.

Closing Apo is the confirmation action; there is no second confirmation
endpoint. The commit is accepted only for a prior `needs_confirmation` review,
with the same product IDs and quantities, a shop-scoped catalogue, sufficient
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
reversal of the same sale returns `409`. The in-memory MVP stores the reversal
audit until restart; no refund or financial ledger posting is inferred.

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
