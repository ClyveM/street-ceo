# Street CEO web app

Updated 2026-11-02. The default build publishes only the Street CEO shop at `/`.
The connected demo covers catalogue, manual/Apo sale, tender/change, stock,
saved sales history and sanitized request investigations. See the root README
and `docs/demo-mvp-acceptance.md` for current scope; older feature notes below
are historical implementation context, not expanded demo acceptance.

## Develop and verify

From `apps/web` run `npm ci`, then `npm run dev` (normally localhost:5173).
`npm run build` typechecks shop sources and emits `dist/index.html` with the
shop bundle only. `npm run test:frontend` runs the tracked shop tests on
Node 22.18+. No ignored office or team files are needed by these commands.
Set `VITE_API_BASE_URL` to a reachable API root before building for the phone.
Fixtures under `tests/` are synthetic and never shipped as business data.

The optional local team workspace is preserved under ignored `local-office/`.
On machines that already have it, `npm run dev:office` opens
`/local-office/office.html`; `npm run build:office` writes `dist-office/` and
`npm run test:office` runs its separate tests. Those optional commands require
the local files and are intentionally unavailable in a clean shop checkout.
The backend also requires its explicitly enabled local-team adapter.

`design-preview.html` is an archived mockup, not a build entry.

## Shop connection and Ask Muse

`VITE_API_BASE_URL` sets the backend root and `VITE_SHOP_ID` can override the
shop ID. Saved Shop Connection values take precedence. A pasted `/api/v1`
suffix is normalized off the backend root. On a phone, use the computer's
reachable network address rather than the phone's `localhost`.

Hwaro's seed implementation and API contracts confirm the local demo shop ID
`00000000-0000-0000-0000-000000000001`. It is distinct from the fully zero nil
UUID. The default is centralized in `src/muse.ts`; valid explicit overrides
are preserved. Missing/nil/malformed shop IDs and missing/invalid backend URLs
are shown before an Ask Muse request. Settings offers an explicit demo-ID
choice and validates before saving. PostgreSQL deployments do not seed demo
records automatically.

Ask Muse uses `POST /api/v1/shops/{shop_id}/muse` with `{question}` and
`X-Shop-ID`. It renders loading, error/retry, answered, needs-data, and
unavailable states. Editing/changing tools/leaving aborts an outstanding
request; requests time out after 20 seconds. Period labels come from returned
evidence IDs, not guessed dates. The backend does not return exact date bounds
or verified completeness. Missing COGS and expenses remain explicit; sales do
not become invented profit. Loan help remains unavailable.

Provider credentials stay on the backend. The browser never holds AI keys.

## Product photos and Social Update

Stock and Social Update share optional, page-session product-photo previews.
JPEG, PNG, and WebP are allowed up to 10 MiB. MIME type, size, file signature,
and browser decoding (where supported) are checked. Preview URLs are revoked
when replaced or on unmount. Previewing a photo does not upload it.

Upload uses the verified multipart field `image` at
`POST /api/v1/shops/{shop_id}/products/{product_id}/image`, with `X-Shop-ID`.
Unsafe filenames are normalized before submission. Receipts must match the
shop/product. Current API storage is in memory and resets on restart; it returns
metadata, not a fetchable image URL. The displayed preview remains local.
Uploads are disabled while the catalogue is only starter/demo data.

Social Update replaces the old placeholder with product/photo selection,
optional shop-photo metadata, source-brief verification, image request,
loading/error/provider-unavailable states, and explicit manual draft/brief
exports. Choose at most twelve products. The source-data route is
`POST /api/v1/shops/{shop_id}/social/brief`; it verifies repository product
facts and optional photo metadata, not AI copy or image bytes. The shop-photo
picker is labelled local preview/metadata only.

Verified social generation now uses the updated source contracts:

- `POST /api/v1/shops/{shop_id}/social/draft`: caption, voiceover, shot list,
  product claims, provider/source/model/warnings, and `draft_only`. Returned AI
  text can be edited before explicit export; fallback text is never inserted
  as a successful draft.
- `POST /api/v1/shops/{shop_id}/social/image-generation`: selected product IDs,
  optional uploaded image ID, brief and aspect ratio. Status is `draft`,
  `provider_not_configured`, or `unavailable`. Verified safe HTTP(S)/PNG/JPEG/WebP
  data refs can preview/download; unresolved provider refs are not fabricated
  into URLs. Regeneration and export are separate clicks. Provider access is
  server-configured, not implied by a text-model connection.

Image warnings/errors stay visible. Manual copy can also be edited/exported.
No Facebook publishing, scheduling, or Reel video rendering occurs automatically.

## Retail control, costs and expenses

Stock → expand a product's recorded cost → Edit recorded cost opens the
cost-only correction flow. Enter up to six decimal places, effective date,
reason, source reference and recorder; save a draft, review, then explicitly
confirm. The verified `/products/{id}/cost-corrections` and
`/cost-corrections/{id}/confirm` routes replace cost without receiving stock.
The product cost audit uses `/products/{id}/cost-history`. Uncertain confirmation
is blocked from automatic replay; the current API has no correction-draft GET
or idempotency contract. Corrections do not reconstruct historical profit.

Stock → Open retail control is the central guided workspace. Purchase entry
supports manual purchases without a document or a PDF/JPEG/PNG/WebP source
upload (10 MiB). Upload alone does not receive stock or invent extracted lines.
An uploaded invoice ID can be reopened, and extraction status refreshed.
Pending/unavailable/manual/provider evidence has distinct wording. Returned
source lines and suggestions are visible for review; every purchase product
match must still be selected explicitly. The current upload service returns
provider_unavailable with no inferred lines, so the demonstrated path is manual
entry from the original document. No fake OCR or guessed product match is used.
Add multiple existing/new products, whole base-unit quantities, exact unit costs
(up to six decimals), new selling prices, date, recorder, supplier/reference and
Cash/Bank/Unpaid metadata. Save a purchase draft, review every line and total,
then explicitly acknowledge and confirm. This creates products/receives stock
and shows server-returned weighted-average costs and baseline/cost-change insights.
Paid purchases feed recorded cash/bank movement totals for close; this does not transfer funds or prove external settlement. Paid totals must resolve to whole cents; sub-cent amounts are rejected rather than silently truncated.

Purchase routes are POST /api/v1/shops/{shop_id}/purchases, GET
/purchases/{id}, and POST /purchases/{id}/confirm. Reopen a saved ID after an
uncertain outcome; confirmation replay returns the original result. Invoice
references are unique within this purchase service. The old invoice-confirm UI
is no longer mounted in the shop, avoiding two visible receipt paths; its
reusable code/API is preserved. All retail records currently reset on restart.

Monthly/on-demand stock takes save counted quantities with a server-captured
expected snapshot. Blank counts remain uncounted; explicit zero is accepted.
Review the adjustments and explanation before confirmation. A changed baseline
returns409 without posting; reload/recount in a new draft. GET recovery and
replayed confirmation receipts are supported. Stock refreshes after confirmation.

Daily close reads the shop-timezone breakdown of opening balances, sales,
confirmed paid purchases/expenses, refunds and signed adjustments. The full
recorded-movement total is validated before review. Enter actual cash and bank
counts, review differences and notes, then explicitly confirm a locked close.
The UI rechecks movements before posting, retains a stable request reference for
uncertain retries, and validates the returned audit/count/variance receipt.
Older sales_only responses stay gated. Missing transactions and external bank
settlement are not certified, and variances never auto-post a correction.

Operating expenses preserve the seven-category guided draft/review/confirm
workflow, one-off/recurring period, notes and payment status. Recurrence records
the supplied period, without scheduling charges. Invoice/product costs use micros;
expenses/sales use cents. No floating-point rounding is used for amount entry.

Sell now has explicit Cash/Bank review and confirmation, a pending guard, and
one request key per logical basket retained across uncertain retries in this
mounted session. Authoritative stock_after updates Stock immediately; transaction
errors remain errors rather than false empty histories. No durable offline queue
or bank settlement is claimed. Ruzivo/Chengetai review remains required.

See DEMO-READINESS.md and APK-MOBILE-CHECKLIST.md for demo/phone constraints.
## Optional local office

The preserved local workspace and migration notes live under ignored
`local-office/`, outside the shop build and shop test glob. Use the optional
commands above only when those files are present. It is not part of the APK
or published Street CEO product. Team routes are disabled by default.

## APK-first shop interface

The shop no longer mounts `InstallPrompt`, including its install/help/download
banners. Existing manifests and service-worker files/registration are preserved
for development and Fambai's offline integration. No Android files were edited.
Voice capture remains in Sell, with explicit confirmation and text fallback.
Offline queue/service-worker logic stays owned by Fambai.
