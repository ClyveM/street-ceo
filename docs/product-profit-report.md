# Product gross-profit report

Owner-requested Reports extension, 2 November 2026. Reports provides Sales and
Profit views sharing the same selected inclusive shop-local period.

Profit means **recorded gross profit before shop expenses**, not net profit,
cash generated or verified bank settlement. Show sales, recorded cost of goods,
gross profit and gross margin for the whole selected range and each product.
Product rows retain quantities sold and make losses visible.

Use receipt-saved revenue and COGS. Exact formula in millionths of currency:
`gross_profit_micros = revenue_cents * 10000 - cogs_micros`.
Only report this as complete when both revenue and COGS are complete. A partial
known-cost subtotal is not complete COGS, and unknown profit is not zero. Margin
is undefined for zero revenue. Current catalogue costs must not reconstruct
missing historical costs. No arbitrary allocation of shop expenses to products.

Margin is returned as nullable integer basis points: gross profit divided by
revenue, multiplied by 10,000, rounded to the nearest integer with ties away
from zero (`ROUND_HALF_UP`). Signed losses are not clamped. Aggregate exact
amounts first; do not sum rounded per-product display amounts.

Historical single-product receipts may use their exactly attributable saved
totals. Multi-product receipts without saved line amounts remain incomplete.
Stock-only Undo remains separate and does not imply a financial refund or reduce
these gross recorded figures. Seed costs are illustrative demo data.

Keep the mobile presentation concise. Use a clear Sales/Profit selector, shared
date controls, a prominent gross-profit result and readable product details.
Keep a concise incomplete-data warning visible. Detailed cost/coverage and
reversal explanations remain available in secondary disclosures.

Acceptance: validate complete and missing costs, incomplete revenue, zero sales,
zero revenue, negative profit, current-price/cost edits, deduplicated receipts,
local-day boundaries and read-only behaviour. The frontend validates server
arithmetic rather than deriving historical profit from current stock. Finance
review and independent QA precede activation and APK packaging.
