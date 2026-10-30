# Dura — Tasks

No tasks assigned yet. Initialized 2026-10-29.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W2-DURA-001 — Inventory movements and weighted-average cost — active 2026-10-30

- Scope: `services/inventory/` only.
- Read AGENTS.md, this role, all six brain files, `docs/product-requirements.md`, `docs/accounting-rules.md`, `docs/finance/mvp-accounting-policy-2026-10-30.md`, `docs/api-contracts.md`, and `tasks/master-board.md`.
- Implement explicit receipt, sale, return, adjustment and stock-count movement primitives with pack conversion and quantity-weighted average cost. Reject ambiguous or negative outcomes and preserve source references.
- Do not implement finance/API/UI/offline/voice code. Expose integration-friendly interfaces and document assumptions in the handoff.
- Acceptance: two cartons of 24 yields 48 base units; WAC uses quantities; returns/restock behavior is tested; no silent negative stock.

### Evidence — 2026-10-30

- Added `services/inventory/movements.py`, `services/inventory/__init__.py`, and
  `services/inventory/test_movements.py`.
- Focused inventory suite: 5 passed. Compilation: passed.
- Whole-repository suite: blocked during collection by pre-existing top-level
  import failures in AI and voice test modules; see `current-state.md`.
