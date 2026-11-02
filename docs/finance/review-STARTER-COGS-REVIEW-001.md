# Illustrative starter unit costs — 2026-11-02

Task: STARTER-COGS-REVIEW-001. Ruzivo. Internal advisory review, not statutory
certification. Owner requested starter catalogue costs for the connected demo.

## Approved demo assumptions

These are deliberately illustrative USD values for synthetic starter products.
They are not researched market prices, actual supplier invoices or verified
historical acquisition costs.

| Seed SKU | Product | Unit selling price (existing demo) | Illustrative unit cost | Cost in micros |
|---|---|---:|---:|---:|
| COKE-300 | Coca-Cola 300ml | 1.50 | 1.00 | 1000000 |
| BREAD-700 | Bread loaf | 1.80 | 1.20 | 1200000 |
| SUGAR-1KG | Sugar 1kg | 2.40 | 1.80 | 1800000 |
| MILK-500 | Milk 500ml | 1.30 | 0.90 | 900000 |
| CHIPS-100 | Potato chips | 1.00 | 0.60 | 600000 |
| SOAP-175 | Bath soap | 2.20 | 1.50 | 1500000 |

Selling prices above describe the original seed definition, not an instruction
to overwrite a persisted price. If the owner has changed a selling price, retain it.

## Required implementation controls

- New demo seeds may initialize these unit costs. Existing records may receive a
  cost only where the seeded demo shop and exact seed product identity match and
  `unit_cost_micros` is absent/null. Every non-null cost, including zero, is known
  and must remain unchanged.
- Preserve existing stock, selling price, supplier/invoice source links and all
  sales, receipts, replay keys and historical sale COGS. Do not recreate deleted
  products or silently revalue other shops or user-created catalogue products.
- Record a clearly labelled demo-seed cost audit with source reference
  `STARTER-COGS-001`, the illustrative assumption and unchanged stock before/after.
  Quantity received is zero. No supplier invoice, cash/bank payment or stock receipt
  should be invented to justify these demo assumptions.
- Persist the upgrade atomically and make repeated startup idempotent. No duplicate
  cost audit for an unchanged already initialized product.
- The new opening cost supports COGS for future sales using the existing pre-sale
  unit-cost snapshot. Old sales whose COGS was unknown remain unknown. Supplying a
  current cost cannot establish historical cost or retrospective profit.
- Clearly distinguish cost-based gross margin from net profit: no expenses,
  settlement, tax or full balanced-journal approval is implied by this initialization.

## Review status

The values and treatment above are approved for implementation. Product-code
verification and regression evidence are pending Hwaro/Chengetai handoff. No live
database mutation or application test has been performed by Ruzivo for this review.

Hwaro confirmed the intended design: default demo shop UUID/name/currency/timezone
and product UUID/SKU/name/shop ID guards; preserve all non-null costs including zero;
skip invoice-linked or previously cost-audited products even when current cost is
missing, to avoid replacing a deliberate unknown. Use `demo_seed` audit provenance
rather than a permanent product-source flag which could become stale after a real
purchase. That conservative design is approved, subject to actual implementation
and tests. Runako was given the exact final six values for fallback fixture parity.

Future demo COGS derived from these assumptions must be described as illustrative
demo cost. A report saying a value is saved/confirmed does not turn the assumption
into supplier evidence. No existing receipt, quantity, tender, selling price or
historical profit is amended by this approval.

## Implementation review — 2026-11-02

**Verdict: approve with conditions for the illustrative starter-cost feature.**
Actual source now implements the approved treatment. Final activation remains
subject to Chengetai/root regression and safe runtime verification.

Inspected `seed_demo_shop` and `_backfill_demo_costs` in `services/api/app.py`,
`services/api/demo_catalogue.json`, the `demo_seed` audit enum in `costs.py`, the
existing SQLite startup transaction, `test_starter_costs.py`, and frontend fallback
cost parity. The initializer checks the complete default shop model and exact
product ID/shop ID/SKU/name. It touches only null costs with neither invoice link
nor prior cost audit. It does not replace price, quantity, known zero/other cost,
historical sale, receipt or retry bindings, and does not recreate removed products.

Each initialized cost has explicit `demo_seed`/`STARTER-COGS-001` provenance,
illustrative reason, zero quantity received and unchanged stock. Repeated startup
does not append a new audit once cost is present. No fake supplier invoice or
payment is created. Seed initialization runs inside the existing SQLite startup
transaction. The current sale path still snapshots its pre-sale unit cost; the
initializer never traverses historical sales to fill missing COGS.

Authored backend regressions inspected cover fresh six-product/audit parity,
repeat initialization, future COGS, legacy known-zero and unknown receipt JSON
preservation across reopen, changed prices, existing costs, renamed/SKU-edited
products, and invoice/audit/non-demo skips. Root/QA are running those tests; no
backend pass is invented here. Runako reports 141 frontend tests and production
build passed including canonical fixture parity; this is attributed evidence,
not a Ruzivo execution.

No application test, live mutation, provider call or product source edit was
performed by Ruzivo. Scope remains illustrative demo costs, with the prior full
financial review and physical APK acceptance separate. Re-review if the fixture,
backfill guards, audit provenance or historical-sale treatment changes.
