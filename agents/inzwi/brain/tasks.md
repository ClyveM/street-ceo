# Inzwi — Tasks

No tasks assigned yet. Initialized 2026-10-29.

### W3-VOICE-INPUT-001B — Apo/Napo audio adapter — assigned 2026-10-30

- Define the audio-to-transcript adapter contract and connect its transcript to
  the existing `VoiceSession` state machine.
- Preserve confirmation-before-posting, safe retry idempotency, and text/push-
  to-talk fallback. Document the chosen speech-to-text seam and limitations.
- Scope: `services/voice/` and voice-owned docs/tests only.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W2-INZWI-001 — Apo/Napo voice interaction adapter — completed 2026-10-30

- Scope: `services/voice/` only.
- Read AGENTS.md, this role, all six brain files, `docs/voice-design.md`, `docs/product-requirements.md`, `docs/api-contracts.md`, and `tasks/master-board.md`.
- Implement a provider-neutral foreground state machine for ready → Apo → item capture → Napo → quote → payment → validating → committed/failure, plus push-to-talk/text fallback mappings. Route interpreted intents to existing API contracts; never commit from voice alone and preserve baskets through clarification/errors.
- Do not implement microphone UI, AI provider internals, backend, finance, inventory, or offline code. Record provider assumptions and unknowns honestly.
- Acceptance: two sequential customer cycles, missing tender, ambiguity, insufficient cash, provider outage and safe retry are covered by tests or explicit contract fixtures; handoff lists integration dependencies.

#### Evidence

- Implemented `services/voice/state_machine.py` and `services/voice/__init__.py`.
- Added `services/voice/test_state_machine.py` covering all listed scenarios,
  including insufficient stock (the API's available stock failure shape).
- Focused suite: 7 passed. Repository checks: 6 passed and compilation passed.
