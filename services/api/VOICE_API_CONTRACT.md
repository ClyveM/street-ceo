# Backend-local voice input contract

These endpoints are the browser microphone boundary. They are shop-scoped,
read-only with respect to sales, and require `Idempotency-Key` so retries do
not create competing interpretation requests.

## Transcript

`POST /api/v1/shops/{shop_id}/voice/transcript` requires `X-Shop-ID` matching
the path and accepts `{ "transcript": "..." }` with a maximum of 1,000
characters. The response is a bounded object containing `request_id`,
`shop_id`, `input_kind`, `status`, optional transcript, optional normalized
intent, and an error code. A `record_sale` intent always has
`status: "needs_confirmation"`; this endpoint never posts a sale.

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
returned in a response. Provider failures are bounded to safe error codes.
