# Ungwaru — Handoffs

## 2026-10-30 — W1-UNGWARU-001 — completed

### Assignment summary

Defined a provider-neutral, schema-first boundary for sale intent and
evidence-backed business insights, including prompt-injection boundaries,
timeouts, provider error handling, and tested fallbacks. Recorded the
Meta/Llama capability evidence without claiming live access.

### Files changed

- `services/ai/__init__.py` — public exports.
- `services/ai/boundary.py` — provider protocol, request contracts, validators,
  prompt boundary, timeout/error handling, typed fallbacks.
- `services/ai/capability_matrix.py` — verified-vs-unknown capability register
  with official evidence URLs.
- `services/ai/test_boundary.py` — six dependency-free tests.
- Own brain files: `memory.md`, `current-state.md`, `decisions.md`,
  `lessons.md`, `tasks.md`, and this handoff.

### Tests and results

- `python -m unittest discover -s services\\ai -p 'test_*.py' -v` — 6 passed.
- `python -m py_compile services\\ai\\__init__.py services\\ai\\boundary.py services\\ai\\capability_matrix.py services\\ai\\test_boundary.py` — passed.

### Outstanding issues

- No live Meta/Llama credentials, installed provider SDK, deployment target,
  smoke test, latency measurement, or cost measurement was available.
- The provider adapter and API endpoint remain to be selected and wired by the
  owner agents; this task intentionally did not implement API, voice, UI, or
  finance logic.

### Next-session instructions

- Obtain Mutungamiri approval for the provider and budget before adding an SDK.
- Hwaro should map the typed results to a documented API contract.
- Inzwi should pass bounded transcript text and retain confirmation before any
  sale endpoint call.
- Chiono should provide stable evidence IDs and consume only validated insights.
- Chengetai should include these tests in the repository-wide quality gate.
