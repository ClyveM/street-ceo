# Mobile reports and spoken close — 2026-11-02

Owner-approved addition to the connected demo. Preserve catalogue, manual/Apo
sales, stock, history, cash/change, SQLite durability and investigation traces.

## Reports

- Mobile entry for monthly sales summary and sales by product.
- Select a month, inclusive start/end dates, or last1/20/90 calendar days including
  today in the shop timezone. Last1 day means today. Show the selected dates.
- Receipt-based recorded sales totals, transaction count and Cash/Bank split.
- Product quantities and historical amounts where evidence exists. Never value
  old product sales using today's selling price. Future receipts snapshot prices;
  old mixed baskets without snapshots disclose unallocated/unknown product amounts.
- Missing historical COGS remains unknown; gross margin is not net profit.
- Stock-only Undo is not a refund; do not silently reduce financial sales from it.

## End my day

From idle Sell or a completed verified receipt, a spoken “end my day” starts the
close conversation, with Apo framing also supported. Never interrupt a pending
or uncertain sale. Replies do not need another Apo or per-question taps.

Ask counted cash on hand, then opening cash if no trustworthy baseline exists.
Zero opening is valid when explicitly recorded. Use one balance anchor, never
sum historical opening balances. Carry from a prior counted close only according
to the reviewed cutoff/movement policy and disclose any previous variance.

The server calculates expected cash from opening/baseline + cash sales + cash in
− recorded cash expenses/purchases/refunds/cash out. A cash sale contributes its
sale total, not cash tendered before change. Show counted, expected and
counted−expected difference: balanced, shortage or overage. Bank is separate and
unverified in a cash-only close; never fabricate a zero bank count.

Speak the comparison and ask confirmation before recording. A variance remains
visible and auditable; never auto-post a balancing adjustment. Keep the original
payload/key for uncertain outcomes and recover before retrying. Revalidation
protects against activity between preview and confirmation. A saved close is a
snapshot; later activity is flagged rather than silently rewriting it.

## Month-end

Provide a monthly review with sales summary and an optional stock-count step.
Offer Count stock or Skip. Skipping does not block the review or day-end cash
close. Do not claim a statutory/ledger period lock or turn stock adjustments into
cash, refunds or sales.

## Gate

Ruzivo reviews financial treatment; Chengetai independently validates date/time
boundaries, revenue/cost evidence, anchor and variance calculations, zero/unknown,
concurrency/idempotency/restart, and hands-free state safety. Root checks current
runtime, read-only live reports/preview, native compilation, exact APK assets,
signature and download. No live original-shop financial close is posted for tests.
Physical phone voice/report/date/month-end acceptance remains separate.
