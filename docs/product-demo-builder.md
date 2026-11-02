# Street CEO — product and demo builder brief

Version: 2026-11-02. Audience: an AI app builder and developer. This is the target
demo specification. Actual implementation evidence and phone-test limits are
recorded separately in `docs/demo-mvp-verification.md`.

## Product promise and scope

**Your shop, in control.** Help a busy tuckshop owner serve a customer, record a
sale, hear total/change, and trust that stock and history update. The primary
surface is a low-cost Android phone. The demo is one Zimbabwean tuckshop, USD,
Africa/Harare time, with whole-unit packaged goods.

Build **catalogue → manual or hands-free Apo sale → stock → sales history**.
Use a connected API with SQLite on the backend host. The APK needs that backend
on a reachable network. The separate team-view/Project Operations Office is not
part of Street CEO. Do not add agent desks or development chat to the shop.

## Screens and visual direction

| Screen | Main purpose | Essential content |
|---|---|---|
| Today | Quick overview | Recorded sales summary and Sales history link |
| Sell | Serve the next customer | Ready/listening state, catalogue, manual basket, Type instead |
| Basket/payment | Finish a sale | Items, quantities, total, short question and voice-answer state |
| Saved receipt | Read at a glance | Total, Tendered and large Change; next-Apo hint |
| Stock/catalogue | Product availability | Name, SKU, selling price, stock; unit cost in details |
| Sales history | Inspect a saved sale | Items, quantities, total, tender, cash received, change, time and cost availability |
| Reports | Review trading | Monthly summary, product quantities/amounts, inclusive dates and Today/20/90-day presets |
| End my day | Count and compare cash | Counted cash, opening provenance, recorded expected cash, shortage/overage and explicit save |
| Profile | Configure and investigate | Shop connection, voice/pronunciation setup and recent request details |

Use the existing `apps/web/public/street-ceo-logo.png`. Carry its friendly market
character through navy text, green/teal controls and small warm gold accents.
Use a light background, clear sans-serif type, generous spacing, rounded cards
and large touch targets. Current navigation is Today, Sell, Stock, Reports and Profile.

Receipt hierarchy: saved state → items → Total/Tendered → large Change. Put IDs,
server addresses, build information, transcripts and long explanations under
Details & help. Keep errors and uncertain outcomes prominent. Keep stock-only
Undo limitations beside its action. Do not overload the main selling screen.

Android hides system navigation using transient swipe reveal and reserves stable
system/cutout/keyboard space. Shop buttons remain tappable when controls reappear.
Preserve permission dialogs and system gestures. Test small phones and rotation.

## Manual sale

1. Select products and whole quantities; show the basket total.
2. Choose Cash or Bank. Cash requires an explicit amount received.
3. Reject underpayment and invalid amounts with a short explanation.
4. Submit one idempotent request. Show success only after a durable server receipt.
5. Refresh stock and history. A preview is labelled as a preview.

Prices, totals, change and stock are server authoritative. Use integer cents.
Bank records tender type, not verified payment settlement.

## Whole-sale hands-free conversation

After microphone permission, keep one hands-free preference across the entire
sale and successive sales. Native Android arms by default unless explicitly
paused. Recognition is foreground-only, pauses during the app's speech, and
resumes after output. Typing temporarily pauses recognition without changing
the preference. Completion must never turn hands-free off.

Example:

> Owner: “Apo, one Coke and two sugar, Napo.”
>
> App: asks for product confirmation when uncertain, then payment.
>
> Owner: “Yes” when asked, then “Cash ten dollars.”
>
> App: “Sale saved. Total 6.30. Change 3.70.”
>
> Owner: “Apo…” — completed receipt closes; the next command begins.

Required behavior:

- Apo begins a command; a leading Apple is a supported recognizer alias. Napo,
  or terminal Nabo/Napple, ends it. Personal pronunciation setup remains available.
- During a question, simply accept Yes/No/Cancel, a quantity, Cash/Bank or an
  amount. No new wake phrase or enable button is required for each answer.
- A bare wake event can dismiss a completed receipt. Preserve following product
  words in the same utterance. Never discard pending tender or an uncertain sale.
- Unknown products receive a short spoken explanation. A mixed known/unknown
  basket never partially posts. Ask for missing quantities; do not assume one.
- Respect explicit Pause, Android permission and background suspension. Do not
  promise background wake listening. The APK is the full hands-free demo target;
  browser recognition availability varies and typing remains available.

## Fast interpretation and AI boundaries

Exact catalogue input uses the deterministic parser. Safe local proposals may
handle unique exact aliases and narrowly observed speech-noise tails. Preserve
every item and quantity, and never discard words that could name another product.
Every uncertain proposal requires spoken Yes and server-enforced approval.
Label local proposals honestly; they are not actual Muse calls.

Harder phrases use one real Muse catalogue request with a six-second bounded
wait, reusable connections and limited in-flight work. Never retry automatically
in a loop. The model receives product IDs/names/SKUs and explicit quantities;
it does not choose authoritative prices, payments or stock changes.

Validate IDs, quantities and complete item coverage. Timeout, malformed output,
unknowns and ambiguity return non-actionable questions. Distinguish slow, busy,
not configured and failed provider states. Do not promise sub-second external AI;
server benchmark timings exclude recognition and spoken output.

## Reports, day-end and month-end

Provide mobile reports for monthly recorded sales and sales by product. Accept
inclusive custom dates, a selected calendar month, or last1/20/90 days including
today in the shop timezone. Show resolved dates and Cash/Bank totals separately.
Keep legacy mixed-sale product amounts unknown when line-price snapshots are
absent; future sales save authoritative line prices/costs. Current catalogue
prices must not rewrite historical reporting. Stock-only Undo is not a refund.

From idle Sell or a completed receipt, “end my day” starts a hands-free cash-close
conversation. Ask cash counted on hand first and opening cash if no trusted
baseline exists. Zero is explicit, never assumed. Reuse one balance anchor and
carry forward recorded cash activity; never sum old opening balances. A first
late declaration of missing opening is explicit/audited, not inferred from the
closing count. Do not silently replace an established opening.

The server compares opening + cash sale totals + recorded cash in − recorded
cash out against counted cash. Sales contribute total after change, not gross
tendered cash. Include recorded paid expenses/purchases and explicit refunds.
Show and speak counted, expected and counted−expected shortage/overage; ask Yes
before saving. Bank is uncounted/unknown here. Never post a balancing adjustment
automatically. Revalidate stale previews, preserve retry keys and freeze saved
closes; flag subsequent activity rather than rewrite the original result.

Month-end is a guided monthly summary with optional Count stock or Skip. It does
not force a stock count or claim statutory/ledger period closure. Reports and
closing must not interrupt a pending or uncertain sale.

## Starter data and costs

Use `services/api/demo_catalogue.json`, not invented sample values:

| Product | SKU | Price USD | Demo unit cost USD | Opening units |
|---|---|---:|---:|---:|
| Coca-Cola 300ml | COKE-300 | 1.50 | 1.00 | 18 |
| Bread loaf | BREAD-700 | 1.80 | 1.20 | 11 |
| Sugar 1kg | SUGAR-1KG | 2.40 | 1.80 | 7 |
| Milk 500ml | MILK-500 | 1.30 | 0.90 | 15 |
| Potato chips | CHIPS-100 | 1.00 | 0.60 | 23 |
| Bath soap | SOAP-175 | 2.20 | 1.50 | 5 |

Costs are illustrative demo assumptions, not supplier invoices. Store integer
micros: one currency unit = 1,000,000 micros. New sales snapshot cost at posting.
Preserve known costs including zero. Never invent historical COGS or convert
unknown cost to zero. Gross margin is not net profit.

Minimum entities: shop, product, sale/lines, stock snapshot, voice review,
review-to-sale binding, idempotency record, cost audit and trace event. Scope IDs
to the shop. Atomically save sale, stock and retry binding. A failed write leaves
no partial change. Exact retry returns the same receipt; changed payload or
reused review conflicts. Startup preserves existing data. Unknown paid outcomes
freeze the original request/key until recovery establishes the result.

## API integration

Use existing contracts in `services/api/VOICE_API_CONTRACT.md` and
`docs/api-contracts.md`. Send `X-Shop-ID`; mutations use stable Idempotency-Key.

| Purpose | Endpoint |
|---|---|
| Readiness | `GET /readyz` |
| Catalogue | `GET /shops/{shop_id}/products` |
| Manual sale | `POST /shops/{shop_id}/sales` |
| History | `GET /shops/{shop_id}/sales` |
| Voice interpretation | `POST /api/v1/shops/{shop_id}/voice/transcript` |
| Voice approval/payment | `POST /api/v1/shops/{shop_id}/voice/commit` |

Voice commit submits reviewed lines and optional tender/amount. Send
`match_confirmed: true` only after actual approval when required. Missing payment
returns a question, not a sale. Only a durable sale response establishes success.

Persist sanitized, bounded request/response investigations separately from shop
state: correlation, time, operation, model/provider when called, latency, outcome
and review/sale references. Distinguish parsing, local proposals, actual model
calls and replay. Preserve failures and late events. Exclude keys, authorization
headers and raw audio. Keep databases, traces and customer data out of Git.

## Rehearsal and acceptance

1. Use a fresh test fixture, without resetting someone's existing shop.
2. Sell one Coke and two sugar for 6.30; Cash10.00 gives change3.70.
3. Test manual and hands-free in separate fresh fixtures. Stock changes once:
   Coke18→17, sugar7→5. New sale COGS4.60; gross margin1.70, not net profit.
4. “One bread glove number” proposes one Bread loaf; spoken Yes precedes payment.
   No allows correction; Cancel records nothing.
5. Test missing quantity, unknown product, mixed basket, underpayment, Cash then
   amount, Bank, typed entry and spoken cancellation.
6. Start the next sale with Apo/Apple and no tap; retain same-utterance words.
7. Recover a timed-out paid request with the same key, without duplicating a sale.
8. Restart the API: receipts, stock, saved costs and investigations remain.
9. On an actual phone test upward swipe, gesture/three-button modes, keyboard,
   rotation, background/resume and two consecutive voice sales.

Supply test evidence and screenshots with exact build identity. Package success,
animation and mocked receipts do not establish physical-device acceptance.

## Delivery and exclusions

Deliver runnable source, setup steps, key-free example configuration, starter
data, persistent backend, tests, Android build instructions and the product diagram.
Defer offline sync, PostgreSQL hosting, team management, lending, social,
forecasting, full ledger reconciliation and payment-provider settlement.

If the builder can only deliver a visual prototype, label it and list missing
backend/native capabilities. Never present simulated sales or voice as verified
integrations. Existing advanced tools are not the hero demo.
