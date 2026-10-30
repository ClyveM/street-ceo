# Street CEO — MVP Accounting Policy Memo

**Date:** 2026-10-30  
**Owner:** Ruzivo — CFO & Business Strategy Advisor  
**Task:** W1-RUZIVO-001  
**Status:** Approved for MVP implementation, subject to the conditions and open questions below

This is internal advisory guidance for the hackathon MVP, not statutory accounting, audit, or tax certification. Verengai should implement the rules below in the auditable ledger; production release requires the open production/tax questions to be resolved with the Owner and an appropriately qualified local adviser.

## 1. Confirmed MVP policy

### 1.1 Basis, currency, and source records

- Use a simple cash-oriented operational ledger: record a sale when the vendor confirms it, record stock cost when goods are received, and record an expense when it is entered as paid/owed. The MVP does not promise full accrual accounting or supplier-credit management.
- Use one configured trading currency and shop timezone. Store money as exact minor units/decimal values; never use binary floating-point for ledger arithmetic.
- Every posting must have a date/time, shop, actor/source, currency, amount, and source transaction. Corrections use reversal entries; sales, purchases, expenses, and tender records are never silently edited or deleted.
- A sale is posted only after confirmation. A voice or offline request that is not confirmed remains unposted.

### 1.2 Sales and returns

- On a confirmed sale, record gross sales revenue at the agreed selling price and quantity, record tender separately as cash or bank, reduce stock, and record cost of sales (COGS) using the current weighted-average unit cost.
- Selling price overrides are allowed only when explicitly captured on the sale; the override is evidence, not a change to stock cost.
- A return reverses the original sale revenue and its tender/refund when a refund is recorded. If the goods are resalable, return the original quantity to stock at the original COGS amount. If damaged, missing, or not resalable, do not increase sellable stock; post a separately identified stock-loss adjustment and warning.
- A return must reference the original sale where possible. A standalone return without enough evidence is allowed only as an exception flagged for review; it must not be treated as new revenue.

### 1.3 Weighted-average stock cost

- Weighted-average cost (WAC) is the MVP valuation method. For a receipt, calculate:

  `new average cost = (old quantity × old average cost + received quantity × received unit cost) ÷ new quantity`

- Received unit cost should include directly attributable purchase costs known to the MVP. Unknown freight, discounts, tax treatment, and landed-cost allocation are production questions and must not be silently guessed.
- Each sale uses the WAC in force immediately before the sale. COGS equals quantity sold × that WAC. The sale does not recalculate WAC.
- Keep sufficient decimal precision for ledger calculations and round only for display/reporting according to the configured currency precision. Never let display rounding make inventory, COGS, and the ledger disagree.
- Negative stock, missing cost, or a stock count that cannot be tied to a source movement is a warning/exception, not an automatic hidden adjustment.

### 1.4 Purchases and supplier amounts

- When stock is received, increase inventory by quantity and WAC value. If paid immediately, decrease the selected cash/bank tender balance and record the purchase payment.
- The MVP may record an unpaid supplier amount as a visible payable/incomplete-data item, but it must not imply that the bank or cash was paid. Supplier-credit ageing and settlement are outside the MVP unless separately implemented and reviewed.
- A purchase must identify product, quantity, unit cost, receipt date, tender/payment state, and source. Cancelled or incorrect purchases are reversed, not deleted.

### 1.5 Cash and bank tender

- Cash and bank are separate operational balances. A sale tendered in cash increases cash; a sale tendered by bank/wallet increases the bank-tender balance. A purchase or expense reduces the selected tender balance.
- “Bank” means recorded bank/wallet tender only. The MVP does not verify settlement, bank statements, fees, reversals, or wallet provider status.
- Transfers between cash and bank are neither revenue nor expense; they need a transfer source and must affect both balances in equal and opposite amounts. A cash count or bank confirmation must not be manufactured from a sale total.

### 1.6 Expenses

- Record operating expenses separately from inventory purchases and COGS, with category, amount, tender, date, description, and source evidence where available.
- A paid expense reduces the selected cash/bank balance and increases the expense total for the reporting period. An expense with no tender/payment state is incomplete and must be shown as such rather than assumed paid.
- Owner withdrawals are not expenses; inventory bought for resale is not an operating expense at purchase. Tax deductibility, VAT treatment, depreciation, payroll, and accruals are production/tax questions.

### 1.7 Owner drawings, injections, and opening balances

- An owner injection increases the relevant cash/bank balance and owner-capital/injection total. It is not sales revenue.
- An owner drawing decreases the relevant cash/bank balance and owner-drawing total. It is not an expense or COGS.
- Opening cash and opening bank are explicit, dated opening-balance entries for the shop. They are not backdated sales. If the source is an owner contribution, the user may classify it as opening capital, but the system must preserve the distinction and show an incomplete-data warning when the source is unknown.
- Opening stock quantity and cost must likewise be entered as an opening stock balance or supported receipt; do not fabricate historical purchases.

### 1.8 Daily close

At the end of each configured shop day, the vendor should close each tender separately:

1. Confirm the day boundary in the shop timezone.
2. Show opening balance, sales tender, refunds, purchases, expenses, transfers, drawings/injections, and expected closing balance by tender.
3. Capture an actual cash count and, where available, a bank/wallet confirmation. Record the variance and explanation; never auto-hide or auto-post a correction.
4. Confirm that sales, returns, stock movements, COGS, and tender postings reconcile to the same source transactions.
5. Lock the close as a snapshot. Later corrections use dated reversals and appear in the correction trail.

The close is operational, not proof of bank settlement or statutory compliance.

## 2. Worked MVP demo treatment

Assume the configured currency has two decimal places, opening cash is 20.00, opening bank-tender balance is 20.00, and opening stock is zero.

1. Receive and pay 10 units at 1.00 in cash: inventory = 10 units at WAC 1.00; cash = 10.00.
2. Confirm a cash sale of 2 units at 1.50: revenue = 3.00; cash = 13.00; inventory = 8; COGS = 2.00.
3. Receive and pay 10 units at 1.40 by bank: inventory = 18; bank = 6.00; WAC = 1.222222… (40.00 inventory value ÷ 18 units).
4. Confirm a bank sale of 3 units at 1.60: revenue = 4.80; bank = 10.80; inventory = 15; COGS = 3.666666… using the pre-sale WAC.
5. Return 1 unit from step 4 and refund 1.60 by bank: revenue reverses by 1.60; bank = 9.20; inventory = 16; COGS reverses by the original sale cost of 1.222222… because the unit is resalable.

The resulting visible totals before any other activity are net revenue 6.20, COGS 4.444444…, gross profit 1.755555…, cash 13.00, bank 9.20, and sellable stock 16 units. Reports may display currency-rounded values, but the underlying ledger must retain enough precision to reconcile.

## 3. Assumptions used for this memo

- Wave 1 is a Zimbabwean tuckshop, one shop per account, one configured currency/timezone, packaged goods sold in whole base units, and tender recorded operationally without settlement verification.
- Weighted-average cost is the agreed initial valuation method.
- The MVP needs a credible end-to-end demo and does not implement multi-branch accounting, payroll, statutory tax filing, or open supplier-credit management.
- Offline replay may submit a transaction later, but its original event time/source and sync time must remain distinguishable; conflict resolution must not silently duplicate a sale or tender.

These are product and demo assumptions, not findings about a particular retailer’s legal or tax position.

## 4. Incomplete-data warnings and production/tax questions

The product must visibly warn, and reports must disclose, when any of the following is present: missing or conflicting tender; missing purchase cost; unknown opening-balance source; negative stock; unlinked return; unpaid supplier amount; unclassified expense; unexplained cash/bank variance; backdated or offline event with uncertain event time; currency mismatch; duplicate/idempotency conflict; or stock count without a source.

Before production, resolve at minimum: Zimbabwe tax/VAT registration and invoice requirements; whether prices are tax-inclusive; treatment of VAT, levies, discounts, and supplier tax; acceptable retention and audit-trail rules; local accounting basis and financial-year close; bank/wallet settlement and fees; landed-cost allocation; supplier credit/payables; stock-loss and expiry policy; materiality and rounding policy; and who may approve reversals, opening balances, and drawings.

**Implementation verdict:** approve for the MVP demo with the warnings and reversal controls above. Do not market the resulting reports as statutory accounts, tax returns, audited figures, or verified bank reconciliation.
