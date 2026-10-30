# Inzwi — Handoffs

## 2026-10-30 — W2-INZWI-001 completed

### Assignment

Implement the provider-neutral foreground Apo/Napo state machine in
`services/voice/`, with push-to-talk/text fallbacks, API-contract routing,
basket preservation, and safe retries.

### Files changed

- `services/voice/__init__.py` — public voice boundary exports.
- `services/voice/state_machine.py` — session states, input mappings, protocols,
  catalog resolution, quote/payment/validation flow, failure preservation, and
  idempotent retry behavior.
- `services/voice/test_state_machine.py` — seven dependency-light contract tests.

### Tests run

- `python -m unittest discover services/voice -p 'test_*.py' -v` — 7 passed.
- `$env:PYTHONPATH='.'; python tests/run_checks.py` — 6 passed, compilation
  passed, quality checks passed.

### Integration dependencies and outstanding issues

- A consuming adapter must implement `Interpreter`, `CatalogResolver`, and
  `SaleGateway`; the latter must call `POST /shops/{shop_id}/sales` with the
  documented scope and `Idempotency-Key` headers.
- Runako supplies microphone/touch presentation and confirmation UI; Inzwi did
  not modify it. Hwaro/Verengai supply the real API gateway behavior.
- Ungwaru may implement an interpreter adapter later; its output must be mapped
  to `CommandIntent` and must not receive permission to post directly.
- No provider credentials, microphone code, backend, finance, inventory, or
  offline code was added.
- Cash amount is optional: when supplied, an amount below the quote fails safe;
  no amount is accepted as operational tender recording per MVP policy.
