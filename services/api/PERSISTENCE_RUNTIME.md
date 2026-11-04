# Local SQLite demo and PostgreSQL runtime boundary

## Shop-only bootstrap

Install `python -m pip install -r services/api/requirements.txt`, then run
`python -m uvicorn services.api.app:app --host 0.0.0.0 --port 8001 --workers 1`
from the repository root. `tzdata` is declared so `Africa/Harare` works on
Windows without an operating-system timezone database. SQLite needs no separate
database server. For isolated tests, set `STREET_CEO_STORE=memory` and
`STREET_CEO_SEED_DEMO=false` before importing the module-level app.

The shop starts without local team/office code. Those preserved machine-local
modules and their tests are excluded from delivery. Explicit
`STREET_CEO_LOCAL_TEAM_ENABLED=1` enables them only where the optional local files
exist; missing files produce a clear configuration error. The legacy activity
flag alone does not enable team endpoints. Default shop OpenAPI contains no
team/office endpoints, and agent brains/project documentation remain separate
tracked development records.

The connected demo defaults to SQLite when `STREET_CEO_STORE` is unset.
Set `STREET_CEO_STORE=sqlite` explicitly for a reproducible launch and optionally
set `STREET_CEO_SQLITE_PATH` to override the default, `data/demo-mvp.sqlite3`
in the repository. Run exactly one
Uvicorn worker. Existing `.env` configuration may override the default and must
be checked without exposing credentials. There is no silent memory fallback.

The SQLite demo stores explicitly versioned shop-state JSON and asset BLOBs.
Requests are serialized, load and mutate detached state, and commit atomically
before returning success. Failed responses or writes roll back. Catalogue,
manual/voice sale receipts, stock, COGS, cash/change, reviews and retry bindings
are covered by real-file reopen tests in `test_sqlite_store.py`. Seeding preserves
existing state. The separate project-office store is outside this persistence
boundary. This is a small single-worker demo adapter, not a production database
architecture or accounting certification.

Starter unit costs are explicit illustrative assumptions in `demo_catalogue.json`.
`seed_demo_shop` fills only missing costs on exact default shop/product identities;
known costs (including zero), invoice-linked products and existing cost audits win.
The `demo_seed` cost audit has source `STARTER-COGS-001`, zero received quantity,
unchanged stock and no invoice or payment. SQLite applies this inside the existing
startup seed transaction when demo seeding is enabled. Selling prices, stock and
historical sale COGS snapshots are never rewritten; an old unknown COGS stays
unknown. Only future sales use a newly established illustrative opening cost.

The six starter products also have bundled PNG illustrations with editable SVG
sources in `demo_product_images/`. Demo startup fills only missing images for
the exact default shop/product identities, preserving any existing uploaded
image metadata. SQLite commits their metadata and bytes inside the existing
startup seed transaction; repeat startup does not duplicate images. No network,
provider key or rendering tool is required, and stock, prices and receipts are
unchanged. Non-demo and renamed catalogue identities are left alone.

Voice and Muse API traces use a separate SQLite file, default
`data/muse-traces.sqlite3`, configurable through `STREET_CEO_TRACE_DATABASE`.
Trace payloads are bounded and sanitized; raw audio and credentials are excluded.
Correlation IDs link API outcomes to provider calls. Deterministic catalogue
parsing is not a provider call. A pre-commit trace/write failure returns 503 and
rolls back; a final trace failure after commit returns an uncertain-outcome 503
instructing the caller to retry the same idempotency key.

## Connected demo API additions (SPRINT90-API-002)

- `POST /shops/{shop_id}/sales`: optional `amount_received_cents` is a strict
  nonnegative integer. Cash received below total returns `409` with
  `detail.code=insufficient_cash`; server computes change. Bank amounts, when
  supplied, must equal the total (`409 invalid_bank_amount` otherwise), and
  change is zero. Omission/null preserves the legacy sale behavior and its
  existing idempotency fingerprints. Changing a supplied amount with the same
  key conflicts. Cash-detail persistence is supported in SQLite/memory demo
  mode; PostgreSQL rejects it explicitly rather than losing payment details.
- `GET /api/v1/shops/{shop_id}/investigations/requests?limit=20&correlation_id=...`:
  requires the existing matching `X-Shop-ID`. Returns `{shop_id, events}`,
  newest first. `limit` is 1–100 and optional correlation length is 1–120.
  SQL filters by shop before limiting; global or other-shop events are excluded.
  Events are sanitized again on read. Missing trace file returns an empty list;
  unreadable/corrupt logs return safe `503`. This is local demo shop scoping,
  not production authentication.
- `GET /api/v1/demo/runtime`: returns `store_backend`, `database_name`,
  `database_identity`, `process_id`, and `single_worker_demo`. SQLite identity
  is SHA-256 of UTF-8 `str(Path(store.path).resolve())`. The full path and
  credentials are never returned. Launcher must verify identity/PID before
  reusing an existing listener.

## Catalogue voice clarification (CATALOGUE-VOICE-API-001)

Exact complete catalogue commands keep `status=needs_confirmation` and
`resolution_source=catalogue_parser`. Nonexact commands call the configured
catalogue resolver, which receives actual shop IDs/names/SKUs and explicit
transcript quantity slots; sale prices and stock remain server authoritative.

Validated proposals return `status=needs_match_confirmation`, grounded `lines`,
`requires_match_confirmation=true`, and a `clarification_question` constructed
from validated catalogue names/quantities. Nothing posts at this stage.
`POST .../voice/commit` requires strict boolean `match_confirmed=true` for such
reviews, or returns `409 detail.code=match_confirmation_required`. Payment
questions and durable commit/retry rules then follow the existing contract.
Omitted/false new flags preserve prior paid-commit fingerprints.

Unresolved products or missing quantities return `status=needs_clarification`,
empty lines, `clarification_question`, `clarification_code`, `resolution_source`
and `provider_called`. For `clarification_code=missing_quantity`, a transcript
follow-up can supply explicit quantity plus optional `clarification_of` equal to
the prior response request ID. Context is shop-scoped and stored only in existing
voice request records. A grounded contextual proposal still requires explicit
match approval; quantities are never defaulted. Invalid context returns `409`.

Response `provider_called` describes resolution provenance. Completed API trace
events separately derive actual provider calls from model-start events under
the current correlation, so replays are not falsely counted as fresh model calls.
`resolution_provider_called` retains the original response provenance.

Tests can pass `create_app(..., voice_catalogue_resolver=None)` to explicitly
disable model fallback, or inject a callable `(transcript, products) -> resolution`.
The default sentinel enables the configured real resolver for application use.

### Scoped quantity-only replies

A safely grounded single-item missing-quantity response can include optional
`clarification_product_id`, `clarification_product_name` and
`clarification_product_sku`. The existing `clarification_of` request field then
allows a bare positive quantity (digits 1–9999 or words one–twenty, with optional
terminal sentence punctuation). The server reuses the stored product ID without
another model call and still requires spoken match approval before payment.
Current stock is checked; deleting or renaming the item/SKU invalidates context.

The target is supplied only for a unique exact catalogue alias or the narrowly
qualified observed chips phrase after a completed validated Muse match. Generic
plausibility, provider failure, extra unknown words and multi-item baskets do not
gain a single-product shortcut. Older responses without the optional fields keep
their full prior transcript and validated resolver fallback; no product is inferred
from question text. New fields default to null when reading older SQLite state.

## Deferred PostgreSQL adapter

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

## Ask Muse jobs

Use `POST /api/v1/shops/{shop_id}/muse/jobs` with the same JSON question as
the synchronous `POST /api/v1/shops/{shop_id}/muse` and an `Idempotency-Key`
of up to 128 characters. Poll `GET /api/v1/shops/{shop_id}/muse/jobs/{job_id}`.
Both routes require the existing matching `X-Shop-ID` header. Submissions
return 202 and both routes return `{job_id, status, result, error}`. Statuses
are `queued`, `running`, `succeeded`, `failed`, and `expired`. A successful
job contains the normal Muse response, including its own answer status.
The job ID is also returned as `X-Correlation-ID`. Reuse the same key and
question for an uncertain submission. A changed question conflicts with 409.

The local SQLite worker executes the same reasoning path as the synchronous
route, using the committed shop snapshot available when it claims the job.
Model work runs outside the shop transaction. An interrupted job can resume
once at the next startup. This deployment supports one API worker per file.
Other repository modes use an ephemeral queue. The pending question and
completed answer are private job data in the shop database. The question
is cleared at completion, and the answer expires after 24 hours. The
expired job and hashed key binding are removed after another 24 hours.
The separate investigation database holds bounded, sanitized events keyed
by job ID. Raw idempotency keys are excluded from events.
