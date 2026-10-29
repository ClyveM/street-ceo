# Dura — Memory

Initialized 2026-10-29. No prior sessions; no work performed yet.

## Project facts (confirmed)

- Street CEO hackathon MVP; deadline November 4, 2026.
- Inventory scope: catalog, purchases, receiving, sales, adjustments, counts.
- No application code exists yet; inventory model not yet designed.

## Stable context

- Role: `agents/dura/role.md`. Activation protocol: `AGENTS.md` section 2.
- Invariant: every stock movement has a source document; no silent negative stock.
- Every adjustment needs reason + actor; supplier invoices link to received goods.
- Feeds cost-of-sales data to Verengai for margins and P&L.
