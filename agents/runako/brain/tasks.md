# Runako — Tasks

No tasks assigned yet. Initialized 2026-10-29.

### W3-VOICE-INPUT-001A — Browser microphone capture — assigned 2026-10-30

- Add a visible microphone/push-to-talk control in the web app.
- Capture audio with the browser MediaRecorder API and show listening, recorded,
  transcribing, confirmation, success, and failure states.
- Do not place provider keys in the browser. Hand off a bounded audio request to
  Hwaro's backend contract; keep text fallback available.
- Scope: `apps/web/` voice UI only. Add focused tests or a manual verification note.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W2-RUNAKO-001 — Mobile-first web shell and manual sale UI — implementation complete, build verification blocked 2026-10-30

- Scope: `apps/web/` excluding the offline layer owned by Fambai.
- Read AGENTS.md, this role, all six brain files, `docs/product-requirements.md`, `docs/architecture.md`, `docs/api-contracts.md`, and `tasks/master-board.md`.
- Build the first visible PWA slice: branded shell using the supplied Street CEO logo where appropriate, Today/Sell/Stock navigation, responsive mobile layout, product search/catalogue, manual sale basket, cash/bank action states, and clear loading/empty/error/offline placeholders. Keep API calls behind a small client boundary so Fambai can add sync without rewriting screens.
- Do not implement IndexedDB/service worker/sync or backend/finance/voice code. Use mock data only where the API is unavailable and label it as demo data in the UI.
- Acceptance: local dev command documented, responsive preview can be opened, manual sale flow is demonstrable against the W1 API shape, and accessibility basics are covered.

#### Extension: local Team Monitor (2026-10-30)

- Added within the same `apps/web/` ownership: six local agent lanes (Hwaro,
  Verengai, Dura, Runako, Fambai, Inzwi), task/status/changed-file/last-activity
  details, and a clearly labeled simulated typing preview.
- The monitor is a local mock model only; it does not claim to be a real
  line-by-line subagent stream. It is opened through the `Team` bottom-nav item.
- Verification: source inspection confirmed all six lanes and README guidance;
  npm build remains blocked by unavailable registry resolution in this session.

#### Extension: simulated 3D command room (2026-10-30)

- Added a CSS/HTML 3D command room with CTO desk, specialist desks, planner
  cards, and a shared wall board for task, commit, unit-test, and warning stats.
- Uses optional local `window.__STREET_CEO_TEAM_ACTIVITY__` data with a
  deterministic fallback. 2D Team Monitor remains directly accessible.
- UI and README explicitly state that the scene/activity is simulated and does
  not expose private agent thoughts or a true line-by-line generation stream.

#### User-requested extension — local Team Monitor

- Add a Team Monitor view within the same `apps/web/` scope. Show the six Wave 2 lanes, task/status, last activity, changed files, and a code-activity panel.
- The code activity panel must be clearly labeled simulated/demo activity; it must not imply access to hidden line-by-line model generation. Prefer workspace-derived activity when available, with a deterministic mock fallback for local preview.
- Document how to open the monitor locally and preserve the core sale UI.

#### User-requested extension — simulated 3D Team Room

- Add a dependency-light simulated 3D command-room view: CTO desk, specialist desks, adjacent planners, and a shared stats board.
- Display task/status/last activity per desk and board metrics for completed/active tasks, commits, total tests, passing tests, and warnings. Use real repository-derived values when available and deterministic preview data otherwise.
- Keep the existing 2D Team Monitor available as a fallback. Label the 3D room and simulated code activity clearly; never imply private agent thoughts or a true hidden-generation stream.

### W3-LIVE-TEAM-001B — Live Team Monitor client — complete 2026-10-30

- Scope: `apps/web/` excluding Fambai's offline layer.
- Replace the hardcoded Team Monitor snapshot with polling of the local activity endpoint when `VITE_TEAM_ACTIVITY_URL` is configured. Display a live/local badge, last refresh time, and an explicit unavailable state; use the current deterministic snapshot only as a clearly labelled fallback.
- Keep the 2D monitor and simulated 3D room, but feed both from the same typed live snapshot. Do not claim live agent private streams or line-by-line generation.
- Acceptance: polling updates agents/stats, endpoint failure falls back visibly, no API configuration keeps demo preview working, and the build passes.

- Implementation evidence: `src/teamActivity.ts` owns the typed snapshot,
  response validation, deterministic fallback, and endpoint client. `App.tsx`
  polls every 10 seconds and passes one snapshot/meta state to both Team views.
  Live/fallback status, last refresh, and endpoint errors are visible.
- Build evidence: `npm run build` passed; Vite transformed 21 modules and
  emitted the production bundle under `apps/web/dist/`.

## Assigned by Mutungamiri

### TEST-MEMORY-001: summarize agreed React PWA frontend architecture — assigned 2026-10-29

- Description: read-only task. Load brain per AGENTS.md, read
  docs/architecture.md and docs/product-requirements.md, summarize the agreed
  frontend architecture. No code or shared-doc changes; write only to own brain.
- Dependencies: none.
- Status: complete (2026-10-29).
- Acceptance criteria: dated handoff in brain/handoffs.md; brain/current-state.md
  updated; task status recorded here; summary reported to Mutungamiri.
- Acceptance evidence (2026-10-29, TEST-MEMORY-001): read-only task, no code or
  shared-doc changes. Activation files loaded: AGENTS.md, role.md, all six brain
  files, docs/architecture.md, docs/product-requirements.md. Handoff entry dated
  2026-10-29 appended to brain/handoffs.md; brain/current-state.md updated;
  status marked complete here; summary reported to Mutungamiri in completion
  message.
