# Sales reports and counted-cash close

All routes require the existing matching `X-Shop-ID` and shop scope. This is a
connected local demo contract; bank settlement and a complete accounting ledger
are not asserted.

## Saved sales reports

`GET /api/v1/shops/{shop_id}/reports/sales` accepts either inclusive `start_date`
and `end_date` (YYYY-MM-DD, 1–366 days), `preset=last1|last20|last90`, or
`preset=month&month=YYYY-MM`. Default is current month to date. Presets include
today plus the preceding 0/19/89 shop-local calendar days. Local midnight bounds
become a half-open UTC interval. Future-only periods are rejected; future parts
of a selected range are explicitly observed-to-date coverage, not forecasts.

Response contains `start_date`, `end_date`, `coverage_end_date`, `coverage`,
`as_of`, `shop_timezone`, `currency`, `summary`, `daily`, `monthly`, `products`,
`stock_reversal_count`, `warnings`. Summary has `sales_total_cents`,
`transaction_count`, `cash_sales_cents`, `bank_sales_cents`,
`other_tender_sales_cents`, nullable `cogs_micros`, `known_cogs_micros`,
`missing_cogs_sale_count`, `unallocated_product_revenue_cents`.

Product rows have `product_id`, `product_name`, nullable `sku`, `label_source`,
`quantity_sold`, nullable `revenue_cents`/`cogs_micros`, `known_revenue_cents`,
`known_cogs_micros`, and unknown revenue/cost line counts. Label source is
`latest_receipt_snapshot`, `current_catalogue` or `product_id`. Known subtotals
are partial when any line is unknown. Receipt IDs are deduplicated.

New `Sale.receipt_lines` output snapshots trusted product ID/name/SKU, quantity,
unit price, line total, unit cost and line COGS; clients cannot choose input
prices. Older sales default to empty snapshots. A legacy single-product total
is exactly attributable; legacy multi-product amounts are not estimated from
current prices or prorated. Gross receipts and sold quantities stay gross:
stock-only voice undo is disclosed separately and is not proof of a refund.

## Cash-close flow

1. `GET /api/v1/shops/{shop_id}/cash-close/preview?business_date=YYYY-MM-DD`.
   Omitted date resolves to the server's current shop-local date. Fields include
   `business_date`, `shop_timezone`, nullable `opening_cash_cents`,
   `opening_source`, `opening_source_id`, `requires_opening`,
   `requires_payment_review`, `sales_cash_cents`, `paid_expenses_cash_cents`,
   nullable `paid_purchases_cash_cents`, `refunds_cash_cents`,
   `adjustments_cash_cents`, nullable `expected_cash_cents`, `source_ids`,
   `preview_version`, `warnings`, and nullable `saved_close`.
2. If opening is missing, explicitly confirm
   `POST .../cash-close/opening` with `{business_date, opening_cash_cents,
   actor, reason, confirmed:true}` and `Idempotency-Key`. Zero is allowed; cents
   must be nonnegative integers. This may retrospectively declare a **missing**
   opening after trading, with a late-declaration reason and creation timestamp.
   It never derives opening from the end count or replaces a known anchor.
   Response is `CashMovementRecord`: `id`, `shop_id`, `kind:opening_balance`,
   UTC day-start `occurred_at`, `amount_cents`, `tender:cash`, actor/reason,
   `created_at`. Exact retry replays; conflicting payload/known opening/closed
   date/future declaration returns `409`.
3. Obtain a fresh preview, count actual cash, review the variance, then explicitly
   confirm `POST .../cash-close` with `{business_date, cash_counted_cents, actor,
   notes, confirmed:true, preview_version}` and `Idempotency-Key`.
   Confirmation is strict JSON boolean; actor/reason cannot be whitespace.
   A stale version gives `409 stale_preview`. Missing opening or unverified
   fractional purchase payment gives `409 opening_or_payment_required`.
4. Success returns a frozen `CashCloseRecord`: all breakdown fields plus `id`,
   `audit_id`, `shop_id`, `cash_counted_cents`, `cash_variance_cents` (counted
   minus expected), actor/notes, `confirmed_at`, `as_of_cutoff`, `source_version`.
   `bank_card_counted_cents` and `bank_card_variance_cents` are **null**;
   `bank_status=not_counted`. Exact retry returns the saved receipt even after
   later activity; changed payload conflicts. A second key gives
   `409 already_closed`. Recover through `GET .../cash-close/{business_date}`.

Opening is a balance anchor, not the sum of past openings. Latest prior counted
cash close carries its counted amount (with unresolved-variance warning), plus
subsequent cash activity. A later explicit opening replaces an earlier anchor;
normal opening declaration refuses replacement. Expected cash adds saved cash
sales totals (change already netted), subtracts confirmed paid expenses/purchases
and explicit refunds, and includes signed adjustments. Fractional-micros purchase
valuation without actual minor-unit payment evidence blocks closing instead of
silently flooring/rounding cash. Stock-only reversal never reduces expected cash.

SQLite persists source IDs/hash, reviews and idempotency bindings. Later/backdated
activity is flagged in the preview without rewriting saved close amounts; a prior
close's late activity carries into the next opening. Legacy closes lacking source
cutoff evidence disclose ordering uncertainty. The old full day-close route uses
the common corrected cash basis and refuses unknown opening/payment evidence;
its legacy bank figures carry an explicit recorded-estimate warning.

Month-end stock take is an optional separate reviewed inventory workflow. It is
not required for cash close and does not invent sales, refunds or cash movements.

## 2026-11-02 — Product gross profit (PRODUCT-PROFIT-API-001)
Existing GET reports/sales adds these fields to summary and every products row:
- gross_profit_micros: integer|null; exact historical revenue_cents * 10,000 minus saved COGS micros, only when both are complete.
- margin_bps: integer|null; ROUND_HALF_UP(gross_profit_micros * 10,000 / revenue_micros), nearest basis point with symmetric ties away from zero. 100 bps = 1%. Undefined (null) at zero revenue or incomplete evidence. Losses are signed and never clamped.
Summary uses exact aggregate recorded revenue/COGS before computing its margin, never an average of product margins. Existing known subtotals are not promoted to complete profit. A product with missing legacy revenue or cost has both new fields null; another fully known product remains reportable. Complete aggregate sale COGS can support summary gross profit even when a legacy mixed receipt lacks per-product allocations. No-sales complete summary has gross profit zero and undefined margin.
Gross profit excludes operating expenses; this is not net profit or a stock valuation. Existing stock-only Undo disclosure and gross revenue treatment remain. Product names/costs/prices come from saved receipt evidence where available, with existing legacy label warnings, never repriced from current catalogue.
