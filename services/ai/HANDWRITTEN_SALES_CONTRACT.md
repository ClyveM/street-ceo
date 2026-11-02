# Handwritten daily sheet OCR (review only)

`extract_handwritten_sales(image_bytes: bytes, content_type: str,
catalogue: Sequence[Mapping], *, provider=_DEFAULT) -> HandwrittenSalesDraft`

Catalogue entries: `product_id` (or `id`), `name`, `sku`. No prices or costs are
used to fill OCR amounts. At most 200 unique catalogue IDs. A provider injection
implements `extract(image_bytes, content_type, catalogue)` returning the JSON
object below; `_DEFAULT` builds the configured Meta adapter, `None` explicitly
disables it. MIME and decoded format must match PNG/JPEG/WebP, <=5 MiB, <=16 MP,
one frame. Invalid input raises ValueError before any provider call. Missing
Pillow raises RuntimeError (deployment dependency missing).

Returned frozen dataclasses:

- HandwrittenSalesDraft: `status` (`review` or `unavailable`), `lines` tuple,
  `warnings` tuple[str], `image_sha256` (digest of original validated bytes),
  `source` (`meta_handwritten_sales` or `none`), `reason` nullable str,
  `provider_called` bool, `model` nullable str. A review is never confirmed.
- HandwrittenSalesLine: `raw_label` str, `product_id` str|null, `quantity` int|null,
  `unit_price_cents` int|null, `line_total_cents` int|null. Use dataclasses.asdict
  for serialization. Unknown/illegible fields remain null and require correction.

Provider JSON: exactly `{"lines":[{"raw_label":"Bread", "product_id":"known-id",
"quantity":2,"unit_price_cents":null,"line_total_cents":null}],"warnings":[]}`.
<=100 lines, <=20 bounded warning strings; no dates/payment/COGS/receipt/tender
fields. Positive whole quantities only; prices/revenue nonnegative integer cents.
When quantity, unit price and line revenue are all present their arithmetic must
agree. Unknown catalogue IDs, extra fields, malformed types and contradictory
amounts reject the whole extraction, returning unavailable/invalid_response.

The seller must review all lines, amounts, date, stock overlap and payment
allocation through the API's separate draft/confirmation workflow. No customer
receipts, quantity guessing, cash inference, current-cost valuation or mutations.
No token/key/raw image is persisted in the tracing payload. Image content is
sent externally only when the caller explicitly invokes extraction.

Configuration reuses server-only `LLAMA_VISION_MODEL` + `LLAMA_API_KEY` and verified
TLS, with no text-model fallback. Missing config returns unavailable/
provider_not_configured. Catalogue/voice timing is unchanged. OCR has a separate
24s outer deadline, HTTP25s, two bounded in-flight calls and no automatic retry.
Allow at least35s for the frontend request including image transfer/validation.
Timeout/busy/error return no lines; late results cannot mutate anything.

Actual vision capability depends on the account/model and is not established by
fake-provider tests. Deployment must set a genuinely image-capable model; unavailable
or rejected image support must be presented honestly, with manual review available.
