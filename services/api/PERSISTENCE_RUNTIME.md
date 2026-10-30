# PostgreSQL runtime boundary

Set `STREET_CEO_STORE=postgres` and provide
`STREET_CEO_DATABASE_URL=postgresql://...` to activate the PostgreSQL
repository. The application does not fall back to `InMemoryStore` in this
mode.

The existing `/shops`, `/shops/{shop_id}`, product, and sale routes use the
repository methods for PostgreSQL mode. Sale writes run in one transaction:
the idempotency row is checked, product rows are locked with `FOR UPDATE`,
stock is validated, the sale/lines are inserted, and stock is decremented.

`GET /readyz` returns `503` with a safe error when the database is unavailable
or the migration has not created `public.shops`. Apply
`migrations/0001_initial.sql` before serving traffic. No connection strings,
credentials, or customer data belong in source control.
