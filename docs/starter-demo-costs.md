# Starter catalogue costs — STARTER-COGS-001

These are illustrative USD demo assumptions, not supplier invoice costs.

| Product | Selling price | Unit cost |
|---|---:|---:|
| Coca-Cola 300ml | 1.50 | 1.00 |
| Bread loaf | 1.80 | 1.20 |
| Sugar 1kg | 2.40 | 1.80 |
| Milk 500ml | 1.30 | 0.90 |
| Potato chips | 1.00 | 0.60 |
| Bath soap | 2.20 | 1.50 |

Canonical values: `services/api/demo_catalogue.json`. The frontend starter
fixture is checked against this file. Costs use integer millionths of a currency
unit; selling prices continue to use cents.

Fresh demo shops receive all six costs. Existing exact default demo identities
receive only missing costs, with `demo_seed` audit provenance and zero quantity
received. Existing costs (including zero), invoice provenance, prior cost audits,
renamed/custom products, selling prices and stock are preserved. No purchase,
payment or invoice is invented.

New sales snapshot the cost then in effect. Earlier receipts and unknown COGS
remain unchanged, including on retry. Historical profitability may therefore
still report missing data. Actual supplier costs can replace these assumptions
through the existing reviewed cost correction or purchase flow.

Evidence and activation status: `docs/demo-mvp-verification.md`; advisory review:
`docs/finance/review-STARTER-COGS-REVIEW-001.md`; independent QA:
`infra/starter-cogs-qa-001.md`.
