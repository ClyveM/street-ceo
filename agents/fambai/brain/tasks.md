# Fambai — Tasks

No tasks assigned yet. Initialized 2026-10-29.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W2-FAMBAI-001 — Offline queue and sync contract — active 2026-10-30

- Scope: offline layer inside `apps/web/` only: service worker, IndexedDB, queue and sync modules.
- Read AGENTS.md, this role, all six brain files, `docs/architecture.md`, `docs/api-contracts.md`, `docs/product-requirements.md`, and `tasks/master-board.md`.
- Add an idempotent queue model for manual sales and expenses, cached catalogue/totals, visible pending/sync/conflict states, and deterministic replay/conflict contracts. Preserve captured inputs and never claim committed success before server confirmation.
- Coordinate with Runako through documented interfaces; do not modify Runako-owned presentation components or backend/finance/inventory/voice code.
- Acceptance: offline enqueue/replay/duplicate/conflict tests pass and local data is clearly separated from committed server data.

## W6-DEMO-APK-ONLINE-001 — 2026-10-31
Direct CTO assignment received in role chat. Packaging/signature/hash verification complete; physical-phone checks pending. Evidence: brain/handoffs.md.

## 2026-10-31 — W6-APO-HANDSFREE-001 checkpoint
User explicitly requested hands-free Apo start, Napo end, pronunciation setup, and APK rebuild. Coordinated Runako frontend scoped worker and Chengetai read-only QA under AGENTS coordination; parent owns Android shell/build and Fambai brain. No offline changes.
Android native ApoSpeechPlugin added with foreground SpeechRecognizer, microphone permission/availability checks, main-thread lifecycle cleanup, speech/speechError/speechEnd plus native pause/resume events. MainActivity registers plugin; manifest adds RecognitionService visibility. Initial native assembleDebug passed; final frontend integration/build and phone testing pending. Speech recognition may depend on Android provider/network; pronunciation setup matches user-confirmed ASR text aliases, not acoustic model training. Background/locked-screen wake is not implemented.

W6-APO-HANDSFREE-001: implementation and signed debug APK rebuild complete; physical-device acceptance pending. See final handoff.

W6-VOICE-ERROR-001: frontend fix and verified APK packaging complete; phone network/runtime validation pending.

W6-VOICE-PROFILE-001: UI/backend source fix+verified APK complete; API runtime activation pending user restart approval.

W6-VOICE-PROFILE-001 runtime restart approved and completed; live health/preflight/read-only transcript passed. Phone validation pending.
W6-VOICE-COCA-COLA-001: packaged the web voice-framing fix into a fresh online
debug APK; device validation remains pending.
