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


### W6-DEMO-VOICE-001 — completed voice-side fixes, 2026-10-31
Direct Mutungamiri assignment: Quick Sale/tender/change/undo verification and fix.
Scope services/voice/ and own brain. Voice 24 passed; API voice 12 passed.
See handoff for integration dependencies and remaining device/demo validation.

### W6-DEMO-VOICE-001 follow-up — completed 2026-10-31

- Verified the existing Quick Sale, spoken tender, cash/change, and undo paths.
- Fixed punctuated ASR tokens in `services/voice/state_machine.py`.
- Added regression coverage in `services/voice/test_state_machine.py` for
  `Apo.` automatic close and `Cash, 500.` amount parsing.
- Evidence: pytest 25 passed; unittest discovery 22 passed; diff check clean.
## W6-VOICE-COCA-COLA-001 — 2026-11-01

Urgent integration fix completed. Exact segmented Apo/Napo flow now preserves
`coca-cola` through web framing and resolves the seeded catalogue locally.
Focused backend/frontend regressions passed; see handoff.

## Assigned by Mutungamiri — 2026-11-01 — DEMO-VOICE-TRACE-001
Implement provider trace wrappers in services/voice/ only plus own brain. Follow AGENTS full activation load. AI module services.ai.tracing is ready: traced_call(*,operation,model,request,call,secret_values=(),store=None), returns provider JSON mapping; trace_context propagation is in API. Wrap _MetaModelChatClient.create and MetaVoiceTranscriber.transcribe outgoing calls preserving behavior, statuses/errors/response JSON, excluding auth/audio from request trace. Use operation voice_intent / voice_transcription and request metadata/transcript messages as appropriate. Add focused tests verifying actual wrapper redaction/failure capture. No API/AI/UI changes or live calls/restarts. Fix existing voice test imports only if needed for normal root pytest. Persist structured handoff. Coordinate root; no other agents.

### DEMO-VOICE-TRACE-001 — completed 2026-11-01
Implemented provider wrappers and isolated disk-backed trace regression tests in services/voice. Evidence: 29 voice tests passed; compileall and scoped diff check passed. See handoff; no live provider/device claim.
