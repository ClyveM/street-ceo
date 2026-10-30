# Dura — Handoffs

## Handoff — W2-DURA-001 — 2026-10-30

### Assignment

Implement inventory receipt, sale, return, adjustment, and stock-count movement
primitives with pack conversion, quantity-weighted average cost, source
references, and safe negative-stock handling. Scope was `services/inventory/`
only.

### Files changed

- `services/inventory/__init__.py` — public exports.
- `services/inventory/movements.py` — `InventoryBook`, movement/value models,
  pack conversion, WAC, audit validation, and negative-stock protection.
- `services/inventory/test_movements.py` — five focused behavior tests.

### Verified tests

- `python -m pytest services/inventory/test_movements.py -q` — 5 passed.
- `python -m compileall -q services/inventory` — passed.
- `python -m pytest -q` — not green because collection fails in unrelated
  `services/ai/test_boundary.py` and `services/voice/test_state_machine.py`
  (`ModuleNotFoundError` for same-directory imports).

### Integration notes and outstanding issues

- `InventoryBook` is intentionally in-memory and transaction-neutral; Hwaro must
  persist stock and movement append atomically.
- Sales have negative `Movement.quantity`; receipts and resalable returns are
  positive. A sale movement records pre-sale WAC as `unit_cost` and COGS as
  `total_cost`.
- Resalable returns require `original_unit_cost`; non-resalable returns are
  rejected until represented by a separate stock-loss adjustment.
- No API, finance, UI, offline, or voice files were changed.
