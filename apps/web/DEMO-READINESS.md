# Street CEO demo audit and storyboard

2026-10-31 · W5-DEMO-READINESS-UI-001 · Runako · frontend audit

**The requested end-to-end story is not ready to record as a working demo.**
This audit distinguishes rendered UI, current repository contracts, and the
running server. No generated result, posted sale, OCR, profit, or physical-phone
test is invented. The demo deadline supplied by the project is November 4.

## Superseding verification after the first audit snapshot

The older-LAN failures below were reproduced, then isolated: the configured LAN
root exposes **13 routes**, while `http://localhost:8000` exposes **32 routes**,
including current cost/Social contracts. A browser-only connection override to
the current local service loaded the live catalogue and returned **USD 0.25**
profit from **USD 1.50** sales, **USD 1.00** COGS and **USD 0.25** confirmed
expenses. These are synthetic seeded-demo records, not real business results.
The APK default was not changed to localhost: a phone needs a reachable address
serving the same current backend.

The now-implemented invoice UI uploaded a synthetic fixture, reported OCR
unavailable, saved a manual explicitly matched line, and confirmed **1 base unit**
received. Catalogue refreshed to **20 units**, average unit cost **0.975000**.
A synthetic **0.10** unpaid airtime expense was saved as draft and explicitly
confirmed. No payment transfer occurred. New cost files: `src/costs.ts`,
`src/Invoices.tsx`, `src/ExpenseGuide.tsx`, `src/CostsWorkspace.tsx` and
`src/costs.css`; Stock/App/API integrate these workflows. Direct cost-only
correction remains unsupported by the source contract.

A subsequent local UI sale of **2 demo Coke units for USD 3.00** succeeded.
It also reproduced the refresh defect: Stock still showed **20**, then **18**
after reload. That defect is an identified next fix, not hidden by the audit.
Synthetic QA receipts must be reset/prepared by the demo owner before filming.

Social adapters were updated after the original matrix snapshot to the newly
verified text-draft and image-output contracts. They can render editable returned
drafts, provider-unavailable outcomes, safe image previews, regeneration and
explicit export. Live provider readiness is a separate test, not established by
schema/unit tests. The office remains a separate entry and local planning rooms
remain clearly disconnected from the initial legacy room adapter.

Actual local Social tests verified catalogue facts (Coke stock 18). Text draft
returned `unavailable` / `fallback` / `timeout`; image request returned
`provider_not_configured`, no preview, and disabled download. No AI success or
Facebook publication is claimed. Browser-only local override was restored to
the original LAN root after QA; its old-listener errors remain visible.

At this integration checkpoint, **52 frontend tests passed** and the production
build passed with **60 modules** and both shop/office entries. The matrix below
preserves the first audit's findings; use this section for subsequent verified
improvements, and keep the remaining P0 fixes/go-no-go checks.

## Evidence at the audit checkpoint

- Actual shop entry: `/`; pages are local React view states, not `/sell` or
  `/stock` URL routes. Standalone office entry: `/office.html`.
- Browser: actual desktop viewport 1280x720; actual narrow widths 320 and 390
  were measured in the page. A requested 430 width measured 431; it is not
  reported as an exact 430 test. No physical phone was connected/tested.
- The running `/openapi.json` listed shop/product/sale/Muse/invoice-upload and
  older team routes, but no new social, product-image, member-chat, or office
  routes. New source contracts do not establish running-server availability.
- Read-only Swagger execution: `GET /shops/00000000-0000-0000-0000-000000000001`
  with matching `x-shop-id` returned **404**, body `{"detail":"shop not found"}`.
  The configured UUID is non-nil; changing it arbitrarily would not fix this.
- Shop displayed starter catalogue/demo fallback and unavailable Today values.
  A one-item USD 1.50 basket was assembled; clicking Complete sale produced
  **Could not record sale**. No successful sale is claimed.
- Ask Muse profit submission produced **404**, with explicit unavailable
  source-period/data-coverage text. The route itself exists on the listener.
- Local synthetic product PNG decoded, previewed, and remained visible when
  switching between Social and Stock. No real image upload was performed.
- Latest pre-audit full suite: **41 passed**; production build **55 modules**,
  both HTML entries. Those tests use synthetic contract fixtures and do not
  prove a running integration works. Audit CSS fixes require a new build check.

## Demo-step matrix

| Story step | State now | Exact UI/API and source evidence | Smallest demo-safe action |
|---|---|---|---|
| Shop setup | **Partial; create UI missing** | `/` → Shop Connection; `src/App.tsx` `ApiSettings`, `src/api.ts` `getApiConfig/saveApiConfig`, `src/muse.ts`. Valid override/default handling and invalid-ID error work. No shop-create/name/currency/timezone form. Backend `POST /shops` exists. | Restore/verify intended demo shop on the running listener, then use its exact ID. Add a small setup form only if creating a shop is mandatory in the recorded story; otherwise disclose preconfigured demo shop. |
| Add products | **Missing frontend flow** | `/` → Stock; `src/StockCatalog.tsx`, `src/api.ts`. Product list exists, no create-product form/client. Backend `POST /shops/{shop_id}/products` exists. | Build one minimal product form against that contract, or explicitly prepare the catalogue before recording. Do not narrate listing seed products as adding them. |
| Add product images | **Partial; live upload blocked** | Stock/Social → optional photo; `src/ProductImageControl.tsx`, `src/useProductImages.ts`, `src/productImages.ts`. Local preview verified. Source-defined `POST /api/v1/shops/{shop_id}/products/{product_id}/image` absent from running OpenAPI at checkpoint. API returns metadata, not a durable retrievable image URL. | Update/verify listener, upload one non-sensitive demo photo, verify receipt. Label local preview and in-memory storage honestly; add byte retrieval only under a verified contract. |
| Record a sale | **Partial UI; live operation blocked** | `/` → Sell; `src/App.tsx` `Sell`, `submitSale`, `src/api.ts` `createSale`; `POST /shops/{shop_id}/sales`. Basket/tender working locally; real submit failed in audit. | Restore backend/shop first. Disable repeated pending submissions and retain one logical idempotency key across retry. Only show success after server receipt. |
| Stock and transactions | **Partial; trustworthy live state blocked** | Stock and Today → Sales; `src/App.tsx` `Transactions/submitSale`, `src/api.ts` `listSales/listProducts`. Post-sale handler refreshes summary/history but **does not reload products**, so successful-sale stock can remain stale. `listSales` catches errors as `[]`, producing a false empty-history state. | Reload catalogue after confirmed sale; distinguish failed history from a verified empty list. Capture stock-before/after and the returned transaction ID. |
| Ask Muse profit | **Blocked in current runtime; honest UI exists** | `/` → Ask Muse; `src/AskMuse.tsx`, `src/muse.ts`; `POST /api/v1/shops/{shop_id}/muse`. Actual 404. Source now has cost/expense-dependent profit support, but these inputs were not recorded or verified in this audit. | Verify seed/runtime and confirmed cost/expense inputs first. Film missing-data response if inputs are absent; never call revenue profit. Avoid the separate manual Profitability card as proof of AI analysis. |
| Facebook post draft | **Partial manual draft/export; AI not integrated at checkpoint** | `/` → Facebook Reel → Social Update; `src/SocialUpdate.tsx`, `src/social.ts`. Product selection, photo inputs, source brief, manual copy/export exist. UI still says AI text drafting is not connected. Source **subsequently added** `POST /api/v1/shops/{shop_id}/social/draft`; adapter update and runtime verification remain. | Wire the newly verified text-draft schema, then test one fact-backed draft with explicit provider/source. If provider is unavailable, show manual draft as manual. |
| Facebook post image | **Blocked generated output** | Social → Muse image request; `src/SocialUpdate.tsx`, `src/social.ts`. Current UI only accepts old unavailable-only response. Source **subsequently expanded** `/social/image-generation` to draft/provider-not-configured/unavailable with image refs. Running route absent at checkpoint. | Adapt parser/UI to new verified response and test one provider result. Without provider access, show unavailable and omit generated-image-success footage. No automatic publication. |
| Separate Project Operations Office | **Partial working frontend** | `/office.html`, `src/OfficeApp.tsx`, `src/CommandRoom.tsx`, `src/AgentWorkbench.tsx`. Office shell, workstream/task/evidence views and eleven desks verified. Repository feed works; per-member history returned404. Additional rooms are local planning only. | Update listener, verify chat receipt/history, and keep local planning distinct from backend records. Film as a separate operations tool, not a shop Team page. |

## Smallest fixes in order

1. **P0 — runtime:** backend owner brings listener/seed/schema to verified source
   and demonstrates shop lookup, catalogue, sale receipt, and new route inventory.
   Reuse the existing confirmed ID, or explicitly configure a different real ID.
2. **P0 — trust in sale flow:** post-sale product refresh, pending-submit guard,
   stable logical retry key, and visible history-read errors.
3. **P0 — costs:** user has now prioritized W5-COSTS-INVOICES-UI-001. Implement
   reviewed invoice/product matching and guided confirmed expenses against new
   contracts; make receipt stock changes explicit. No fake OCR or opening-cost
   correction disguised as a stock receipt.
4. **P1 — story entry:** minimal real shop/product setup if it must be filmed;
   otherwise explicitly start with a prepared demo shop/catalogue.
5. **P1 — source-backed social draft:** update current adapter to newly added
   text/image contracts, test provider availability, retain explicit export/review.
   A real image provider is a go/no-go dependency, not a CSS fix.
6. **P1 — presentation:** replace the hardcoded welcome date/name before capture,
   make the Facebook Reel label match the actual post/brief capability, and
   avoid showing the manual monthly calculator as verified monthly results.

Only narrow responsive CSS fixes were made during the audit: remove the body
minimum-width overflow, fit the chat modal inside its backdrop, and enlarge
the optional photo file target. No broad feature was added for this audit.

## Four-minute storyboard (conditional, not a claim of capability)

| Time | Shot and action | Narration/evidence gate |
|---|---|---|
| 0:00–0:20 | Shop/connection and real catalogue | “This is our prepared demo shop” unless the create flow actually exists and is used. Show the actual currency and connected state. |
| 0:20–0:45 | Add one real product, then choose a photo | Only show add-product success after implementing/testing it. Otherwise start from existing catalogue and say so. Distinguish local preview from verified upload receipt. |
| 0:45–1:25 | Review a supplier invoice/manual lines, match products, confirm | Await W5 cost UI/API verification. State “manual review” when OCR is unavailable. Show stock units/cost impact before confirmation. |
| 1:25–2:00 | Build a small basket, choose tender, confirm once | Requires actual sale receipt. Show the same ID in Transactions and changed stock quantity after refresh. Record tender, not bank settlement. |
| 2:00–2:30 | Ask Muse about profit | Show real period/evidence and cost/expense coverage. Missing data is a legitimate limitation, not a fabricated profit. |
| 2:30–3:10 | Review post draft and optional generated image | Use only actual returned draft/provider result. Otherwise show manual draft or provider-unavailable state explicitly. Export is a separate user action; do not publish. |
| 3:10–3:45 | Open `/office.html`, select room and member | Show repository timestamps and current assignment separately. Only demonstrate successful chat if the server actually stores/returns it. No private thoughts or live typing. |
| 3:45–4:00 | Close with proven result and known limitations | Mention only capabilities actually captured. Do not hide failed steps by cutting to fixture responses. |

## Video capture checklist

- [ ] Correct running API, seed ID and intended data set verified before capture.
- [ ] Record app build/version, test count, API mode and whether storage resets.
- [ ] Use non-sensitive demo products/photos/invoices/expenses; close unrelated
      apps, notifications, credentials and developer logs before recording.
- [ ] Validate every required shot once continuously: upload/review, sale receipt,
      stock refresh, transaction ID, Muse sources and draft/image result.
- [ ] Choose portrait for APK footage; keep controls/text readable and avoid
      fast scrolling. Capture a separate office-browser segment if it is not
      packaged as an independent APK entry.
- [ ] Preserve real loading/error/unavailable states. Mark prepared data,
      manual review, manual draft, or browser emulation plainly.
- [ ] Never claim OCR, AI image generation, monthly profit, payment settlement,
      offline replay, durable history or physical-phone testing without evidence.
- [ ] Do not trigger Facebook publication or external messaging during capture.
- [ ] Export the final draft only on an explicit click; verify the downloaded
      file on the target phone if that behavior appears in the video.
- [ ] Recheck the final footage against this matrix; remove unsupported narration.
