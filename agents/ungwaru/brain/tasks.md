# Ungwaru — Tasks

## Assigned by Mutungamiri

### W1-UNGWARU-001 — Meta/Llama capability spike — completed 2026-10-30

- Scope: `services/ai/` only; record findings in this agent's brain and propose updates to shared docs through handoff rather than editing another owner's files.
- Read `AGENTS.md`, this role, all six brain files, `docs/architecture.md`, `docs/product-requirements.md`, `docs/voice-design.md`, and `tasks/master-board.md` before investigating.
- Define a provider-neutral boundary for structured sale-intent and business-insight responses, with schema validation, timeout/error fallback, prompt-injection boundary, and a capability matrix for the available Meta/Llama route. Do not claim live model access without evidence.
- Do not implement voice capture, API endpoints, UI, or financial logic.
- Acceptance: a small testable module or design artifact in `services/ai/`, explicit verified-vs-unknown findings, and a handoff naming integration dependencies.

- Evidence: `services/ai/boundary.py`, `services/ai/capability_matrix.py`,
  `services/ai/test_boundary.py`; six unittest cases and py_compile passed.
- Dependencies for integration: Hwaro must expose a versioned AI insight
  request boundary; Inzwi must provide transcript text only; Chiono must supply
  evidence snapshots with stable IDs; Chengetai must add the module to the
  repository-wide quality gate; Mutungamiri must approve provider/credentials,
  timeout, and cost envelope.

No tasks assigned yet. Initialized 2026-10-29.

### W3-VOICE-INPUT-001D — Meta understanding review — assigned 2026-10-30

- Review the Meta Llama transcript-to-intent prompt/schema for short noisy-shop
  commands, injection resistance, and structured output failures.
- Propose test utterances and acceptance criteria for Apo/Napo understanding.
- Scope: `services/ai/` and Meta-owned docs/tests only; do not modify voice or API
  implementation files.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.
