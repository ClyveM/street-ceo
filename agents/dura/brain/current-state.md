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
