# Street CEO — API Contracts (v0, 2026-10-30)

Status: Wave 2 persistence boundary. Local/test mode uses an explicit
credential-free in-memory repository; deployment mode uses PostgreSQL selected
with `STREET_CEO_STORE=postgres` and `STREET_CEO_DATABASE_URL`. Clients must
rely on the documented request/response rules, not the storage choice.

## Conventions

- Base URL is local deployment root; JSON endpoints use the paths below.
- Validation errors use FastAPI's standard `422` response. Resource conflicts
  use `409`; missing shop/product uses `404`; a missing or mismatched
  `X-Shop-ID` scope uses `403`.
- Every shop-scoped endpoint requires `X-Shop-ID` equal to the `{shop_id}` path
  parameter. This is the Wave 1 tenant boundary.
- Money is integer minor units (`*_cents`); product quantities are positive
  whole base units. Currency defaults to USD in the development fixture and is
  returned on the shop.
- Mutating sale requests require a non-blank `Idempotency-Key` header.

## Health

`GET /healthz` returns `{"status":"ok"}`. `GET /readyz` returns
`{"status":"ready"}` when the API dependencies are available.

## Product boundary

The separate local team-view application is excluded from this repository.
Normal shop startup exposes no team or office endpoints. See
`docs/repository-boundaries.md`.

## Shops

Local memory mode seeds the browser demo shop by default with stable ID
`00000000-0000-0000-0000-000000000001` and catalogue data only. Override with
`STREET_CEO_SEED_DEMO=false` to disable it. PostgreSQL mode never seeds demo
data from this setting. The seed creates no sales, COGS, expenses, profit, or
other financial records.

`POST /shops` accepts `{name, currency?, timezone?}` and returns `201` with
`{id, name, currency, timezone}`. `GET /shops/{shop_id}` returns the same shape
and requires the shop scope header.

## Products

`POST /shops/{shop_id}/products` requires scope and accepts
`{sku, name, unit_price_cents, opening_stock_qty?}`. It returns `201` with
`{id, shop_id, sku, name, unit_price_cents, stock_qty, unit_cost_micros?,
cost_source_invoice_id?}`. SKU uniqueness is
per-shop. `GET /shops/{shop_id}/products` returns the shop's product list.

## Shop summary

`GET /shops/{shop_id}/summary` returns live local metrics for the Today screen:
`{sales_total_cents, transaction_count, low_stock_count,
sales_change_percent, insight}`. A missing prior-day comparison is returned as
`null`; the client must not invent a percentage.

## Sales

`POST /shops/{shop_id}/sales` requires scope and `Idempotency-Key`. It accepts
`{lines: [{product_id, quantity}], tender}`. Each product may appear once,
quantity is a positive whole number, and `tender` is required and must be
`cash` or `bank`; the API no longer defaults or forces cash.

On success it returns `201` with `{id, shop_id, lines, tender, total_cents,
`cogs_micros?, stock_after, created_at}` and decrements stock in the same
operation. `stock_after` is the server-authoritative post-sale quantity by
product ID, so clients can update their local catalogue without a manual
reload. If any line lacks
sufficient stock, the request returns `409` and no stock is changed; negative
stock is never silently created.

Reusing a key with the exact same canonical request returns the original sale
with `201` and does not decrement stock again. Reusing a key with a different
request returns `409` (`idempotency key payload mismatch`). The key is scoped
to the shop.

For local demo recovery, `POST /api/v1/dev/demo/reset` is enabled only for the
in-memory seeded demo mode. It replaces the stable demo shop with the six
catalogue products and clears sales, invoices, expenses, cost corrections, and
cost audits. It is disabled in PostgreSQL mode and returns `404`; it is not a
production data-deletion endpoint.

## Purchases, stock takes, and day close

Purchases are review-first and shop-scoped:

- `POST /api/v1/shops/{shop_id}/purchases` creates a draft from one or more
  invoice or manual-purchase lines. Each line has a product reference or
  new-product SKU/name/unit price, quantity, purchase unit cost in micros, and
  line total. The declared total must equal the line-total sum; no stock or
  cost changes occur at draft time.
- `POST .../purchases/{purchase_id}/confirm` requires the draft to be
  confirmed. It creates a new product when a line has no product ID, or adds
  quantity to an existing product. It applies
  `(old_qty * old_cost + received_qty * purchase_unit_cost) / new_qty` using
  integer micros, records a cost audit, and returns per-line stock/cost
  results plus explicit baseline/increase/decrease/unchanged insights. All
  lines are validated and staged before any product, stock, cost, or audit
  mutation. A confirmed purchase replays its original confirmation response;
  invoice references are unique per shop and cannot be submitted twice.
- `POST /api/v1/shops/{shop_id}/stock-takes` creates a monthly or on-demand
  counted-quantity draft and captures an expected-stock baseline. `GET
  .../stock-takes/{id}` recovers the draft. `POST .../stock-takes/{id}/confirm`
  first checks that the baseline has not changed, then applies only the
  counted-vs-expected adjustments and records an actor/reason/timestamp audit.
  A changed baseline returns `409` without mutation; unchanged lines create no
  adjustment; confirmed results replay safely.
- `POST /api/v1/shops/{shop_id}/day-close` requires `confirmed: true`,
  `Idempotency-Key`, counted cash and combined bank/card totals, actor, and
  notes. It posts a locked audit record with shop timezone, opening balances,
  sales, confirmed paid expenses, confirmed paid purchases, refunds,
  adjustments, expected totals, counted totals, and both variances. A date can
  be closed only once; exact retries return the original record and changed
  retries return `409`. Card is currently included in the bank/card counted
  bucket because sale tender is limited to cash or bank.
- `GET /api/v1/shops/{shop_id}/day-close/preview?business_date=YYYY-MM-DD`
  returns the full recorded-movement breakdown before confirmation, the shop
  timezone, and `calculation_basis: "full_recorded_movements"`.
- `GET /api/v1/shops/{shop_id}/day-close/{business_date}` returns the locked
  posted close audit for readback, including counted totals and variances; it
  returns `404` when that date has not been posted.

`POST /api/v1/shops/{shop_id}/cash-movements` records an idempotent, audited
opening balance, refund, or signed cash/bank adjustment. It requires
`Idempotency-Key`; opening balances and refunds are positive, while an
adjustment may be positive or negative. These records feed the day-close
preview/posting. Unpaid expenses and unpaid purchases are excluded from paid
movement totals by design.

The current local implementation stores these drafts, confirmations, and
audits in process memory; an API restart clears them. PostgreSQL tables and
atomic purchase/stock-take/close transactions are required before calling the
retail-control path durable. No savings or accounting result is returned when
there is no prior cost basis; the response reports `baseline_established`.

## Invoice costs and operating expenses

`POST /api/v1/shops/{shop_id}/invoices` accepts one multipart `invoice` field
containing a PDF or JPEG/PNG/WEBP image, up to 10 MiB. It stores metadata and
bytes in the local MVP memory store and returns `extraction_status:
"provider_unavailable"` when no OCR provider is configured. The response
contains no invented line items. `GET` on the collection or
`/invoices/{invoice_id}` retrieves the review record.

`POST /api/v1/shops/{shop_id}/invoices/{invoice_id}/review` accepts explicit
review lines with description, quantity, line total, and optional product ID.
Exact SKU/name matches are suggestions only; a line is `accepted` only when a
product ID is explicitly supplied. The API calculates
`calculated_unit_cost_micros` from the line total and quantity. One currency
cent equals 10,000 micros. `POST .../confirm` is the only operation that adds
stock or updates product cost. It requires every line to be explicitly
accepted, updates a weighted average where prior cost is known, and records a
shop/product/invoice cost audit. `GET .../products/{product_id}/cost-history`
returns that audit. Re-reviewing a confirmed invoice is rejected.

### Direct product-cost correction

`POST /api/v1/shops/{shop_id}/products/{product_id}/cost-corrections` creates a
draft correction and requires either a non-negative decimal `unit_cost` with
at most six decimal places or a non-negative integer `unit_cost_micros`, never
both. It also requires `effective_date`, `reason`, `source_ref`, and `actor`.
The decimal is converted exactly to micros; binary floats and unrepresentable
precision are rejected. The endpoint is shop/product scoped and does not
change the product or stock while the correction is a draft.

`POST .../cost-corrections/{correction_id}/confirm` is required to apply the
correction. It changes only the product's unit-cost basis, appends a
`direct_correction` audit record with actor, reason, source, effective date,
and before/after stock values, and leaves stock quantity unchanged. It cannot
be applied twice. This is separate from invoice receipt confirmation and must
be reviewed by Verengai/Ruzivo for accounting treatment before production use.

`POST /api/v1/shops/{shop_id}/expenses` creates a draft operating expense;
`POST .../expenses/{expense_id}/confirm` is required before it contributes to
profitability. Categories are `electricity`, `transport`, `rent`, `wages`,
`airtime`, `supplies`, and `other`. Frequency is `one_off` or `recurring`;
recurring records require a period. Amounts are integer minor units, and each
record keeps date, tender, notes, status, and confirmation timestamp.
`GET /expenses` lists the shop-scoped records.

Muse profitability includes only confirmed sale COGS and confirmed expenses.
Sales without a confirmed product cost return `needs_data`; revenue is never
reported as profit. Invoice bytes, cost audits, and expenses are currently
in-memory and reset on API restart. PostgreSQL persistence needs additive
invoice, invoice-line, product-cost-audit, expense, and sale-cost columns.

## Social Update data

`POST /api/v1/shops/{shop_id}/social/brief` is the shop-scoped data boundary
for Social Update. It requires `X-Shop-ID` matching `{shop_id}` and accepts
selected product IDs plus optional image metadata:

```json
{
  "product_ids": ["product-uuid"],
  "shop_image": {
    "filename": "front.jpg",
    "content_type": "image/jpeg",
    "size_bytes": 2048,
    "width": 1200,
    "height": 800
  }
}
```

The response returns the selected products' exact repository values (`id`,
`sku`, `name`, `unit_price_cents`, and `stock_qty`), optional image metadata,
`shop_id`, `catalogue_source: "repository"`, and `created_at`. Unknown or
cross-shop product IDs return `404`; duplicate IDs and invalid image metadata
return `422`. The endpoint does not upload or store image bytes, generate copy,
or infer inventory, sales, or popularity. Ungwaru may consume this response for
generation, while Runako owns selection and upload UI. A future persistence
layer can add a shop-scoped image asset table and durable social briefs without
changing this selection contract.

### Product images and social image generation

`POST /api/v1/shops/{shop_id}/products/{product_id}/image` accepts one
multipart field named `image` and requires matching `X-Shop-ID`. The product
must belong to the shop. Allowed MIME types are `image/jpeg`, `image/png`, and
`image/webp`; the maximum size is 10 MiB; filenames must be a safe basename
containing only letters, numbers, `.`, `_`, and `-`. A successful `201`
response returns metadata only: `id`, `shop_id`, `product_id`, `filename`,
`content_type`, `size_bytes`, `sha256`, `storage_backend`, `storage_ref`, and
`uploaded_at`. `GET` on the same path returns the latest metadata for that
product. Unknown/cross-shop products return `404`; unsafe filenames, MIME
types, duplicate selection, and invalid metadata return `422`.

`POST /api/v1/shops/{shop_id}/social/draft` accepts selected `product_ids`, an
optional shop-scoped `source_image_id`, a bounded `brief`, and optional
`duration_seconds` (default 40). It calls the verified text social boundary
with repository-derived product facts and returns an editable, draft-only
response containing title, caption, voiceover script, shot list, and factual
claims. It never publishes or schedules content. With no text provider it
returns `status: "unavailable"` and an explicit warning.

`POST /api/v1/shops/{shop_id}/social/image-generation` accepts selected
`product_ids`, an optional shop-scoped `source_image_id`, a bounded `brief`,
and an `aspect_ratio` (`1:1`, `4:5`, `9:16`, or `16:9`). It validates that
every product and source image belongs to the shop, maps the ratio to the
verified `SocialImageRequest` size contract, and returns an editable,
draft-only response with `status` of `draft`, `provider_not_configured`, or
`unavailable`, plus `provider`, `model`, `image_refs`, `output_url`, and
`warnings`. `GET /api/v1/shops/{shop_id}/social/image-generation/{id}`
retrieves the stored response by shop scope. Image refs are provider URLs or
data-image refs suitable for a preview/download flow; no publishing occurs.

The no-provider response is intentional: image generation requires the
server-side `LLAMA_API_KEY` and an explicit `MUSE_IMAGE_MODEL` value of
`muse-image-1.0`. The existing text-only `LLAMA_MODEL` setting is not an image
provider and must not be treated as one. No credentials are accepted in the
browser request body. Runako owns upload/selection UI and Ungwaru owns provider
integration.

Product image bytes and generation requests are currently held in process
memory only and reset when the API restarts. No durable object storage is
available in this MVP. The persistence path is a future shop-scoped object
storage reference plus PostgreSQL metadata table; credentials and PII must
remain outside these API models.

## Persistence boundary

The connected demo uses `services/api/sqlite_store.py`, with atomic shop-state
snapshots and separate sanitized trace storage. One API worker per database file.
Existing state survives startup; PostgreSQL deployment is deferred. The adapter
notes below describe the broader persistence seam, not the current demo host.

The API's repository seam is in `services/api/persistence.py`. PostgreSQL
schema starting point `services/api/migrations/0001_initial.sql` stores shops,
shop-scoped products, sales, sale lines, and the canonical idempotency
fingerprint. PostgreSQL implementations must preserve shop scoping, auditable
sale timestamps, and atomic stock validation/decrement semantics. PostgreSQL
mode never silently falls back to memory; `/readyz` checks the selected store.
