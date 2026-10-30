# Dura — Decisions

## 2026-10-30 — W2-DURA-001

- Use `Decimal` for unit and total costs; do not round internal WAC values.
- Store all movement quantities in whole base units. `PackQuantity` converts
  packs plus loose units before mutation (for example, 2 × 24 = 48).
- Represent sales as negative movement quantities and receipts/returns as positive
  quantities, while recording the unit cost and total cost on every movement.
- Require a non-blank source reference for every movement. Adjustments require
  both actor and reason. Resalable returns require the original COGS unit cost;
  non-resalable returns must be handled by a separate stock-loss adjustment.
- Reject any operation that would create negative stock before mutating the book.
