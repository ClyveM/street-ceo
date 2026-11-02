# Dura — Current State

Updated 2026-10-30 for W2-DURA-001.

## Status

Implemented the inventory movement primitives in `services/inventory/`.

## Work in progress

- W2-DURA-001 implementation complete pending Mutungamiri integration review.

## Latest verified results

- `python -m pytest services/inventory/test_movements.py -q`: 5 passed.
- `python -m compileall -q services/inventory`: passed.
- Repository-wide `python -m pytest -q`: collection blocked by pre-existing import-path
  issues in `services/ai/test_boundary.py` and `services/voice/test_state_machine.py`.

## Known blockers

- Integration remains dependent on Hwaro's transaction boundary and Fambai's
  replay/idempotency ordering. The engine itself is storage- and API-neutral.

## Next immediate action

Mutungamiri should review the movement interface and connect it to the persistence
and API transaction boundary; Verengai should consume signed movement costs for COGS.

## 2026-10-31 — W6-DEMO-INVENTORY-001 checkpoint
Validation completed: 18 focused tests passed. Blocking invoice partial mutation/retry duplication reproduced; see handoffs. Await Hwaro fix and Chengetai release validation. No API/frontend edits.

W6 follow-up: fixed non-whole adjustment acceptance within inventory ownership; 23 focused tests passed in 15.40s. Invoice atomicity remains blocked on Hwaro. See handoff.

## 2026-10-31 — W6 inventory replay checkpoint

Added source/product replay protection to `InventoryBook`: a repeated purchase
line returns the original movement without changing stock, while changed data
for the same source/product is rejected. Multi-line purchase sources remain
valid across different products. Focused inventory tests: 12 passed; related
retail-control and cost tests: 25 passed. The API invoice partial-mutation
defect remains outside Dura ownership and unresolved.
