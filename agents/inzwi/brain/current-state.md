# Inzwi — Current State

Updated 2026-10-30 after W2-INZWI-001.

## Status

W2-INZWI-001 implemented in `services/voice/` and verified. Ready for API/UI integration.

## Work in progress

- Provider-neutral session state machine and focused tests are complete.

## Latest verified results

- `python -m unittest discover services/voice -p 'test_*.py' -v`: 6 passed.
- `PYTHONPATH=. python tests/run_checks.py`: 6 repository checks passed; compilation passed.

## Known blockers

- Integration still requires a concrete catalog resolver and API gateway in the
  consuming layer; this task intentionally supplies protocols and no HTTP client.
- Tender remains operational recording only; no settlement verification is done.

## Next immediate action

Next: coordinate Runako/Hwaro integration against the protocols and documented
sale request shape; preserve the generated idempotency key across safe retries.
