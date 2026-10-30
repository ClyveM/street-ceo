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

## Local team activity

`GET /api/v1/team/activity` is a read-only, local-development-only snapshot
for the Team page. It is enabled by `STREET_CEO_TEAM_ACTIVITY_ENABLED` and
reads only the configured `STREET_CEO_REPOSITORY_ROOT` (defaulting to the
working repository in local mode). The response includes task IDs/statuses
from `tasks/master-board.md`, a Git commit count and latest short subject,
safe changed-file summaries, agent brain-file timestamps, and numeric test
evidence parsed from handoffs. It never returns file contents, repository
paths, secrets, private prompts, or arbitrary request-supplied paths.

The response has `{enabled, available, generated_at, tasks, commits,
changed_files, agents, test_evidence, warnings, error}`. When disabled the
route returns `404`; when the configured root is absent it returns a clear
unavailable state. Neither case affects production API behavior.

## Shops

`POST /shops` accepts `{name, currency?, timezone?}` and returns `201` with
`{id, name, currency, timezone}`. `GET /shops/{shop_id}` returns the same shape
and requires the shop scope header.

## Products

`POST /shops/{shop_id}/products` requires scope and accepts
`{sku, name, unit_price_cents, opening_stock_qty?}`. It returns `201` with
`{id, shop_id, sku, name, unit_price_cents, stock_qty}`. SKU uniqueness is
per-shop. `GET /shops/{shop_id}/products` returns the shop's product list.

## Shop summary

`GET /shops/{shop_id}/summary` returns live local metrics for the Today screen:
`{sales_total_cents, transaction_count, low_stock_count,
sales_change_percent, insight}`. A missing prior-day comparison is returned as
`null`; the client must not invent a percentage.

## Sales

`POST /shops/{shop_id}/sales` requires scope and `Idempotency-Key`. It accepts
`{lines: [{product_id, quantity}], tender?}`. Each product may appear once,
quantity is a positive whole number, and `tender` defaults to `cash`.

On success it returns `201` with `{id, shop_id, lines, tender, total_cents,
created_at}` and decrements stock in the same operation. If any line lacks
sufficient stock, the request returns `409` and no stock is changed; negative
stock is never silently created.

Reusing a key with the exact same canonical request returns the original sale
with `201` and does not decrement stock again. Reusing a key with a different
request returns `409` (`idempotency key payload mismatch`). The key is scoped
to the shop.

## Persistence boundary

The API's repository seam is in `services/api/persistence.py`. PostgreSQL
schema starting point `services/api/migrations/0001_initial.sql` stores shops,
shop-scoped products, sales, sale lines, and the canonical idempotency
fingerprint. PostgreSQL implementations must preserve shop scoping, auditable
sale timestamps, and atomic stock validation/decrement semantics. PostgreSQL
mode never silently falls back to memory; `/readyz` checks the selected store.
