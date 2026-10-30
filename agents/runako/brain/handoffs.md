# Runako — Handoffs

Handoff history initialized 2026-10-29.

## 2026-10-30 — Priority wave: PWA install slice and tool entry points

### Assignment summary

Implement the installable PWA shell and add presentation entry points for
Social Update and Profitability Analysis, while staying out of Fambai's
service-worker sale integration.

### Files changed

- `apps/web/manifest.webmanifest`, `apps/web/icon.svg`, `apps/web/index.html` —
  Street CEO install manifest, branded icon, and browser/mobile metadata.
- `apps/web/src/main.tsx`, `apps/web/src/InstallPrompt.tsx`, `pwa.css` —
  registration of the existing `/service-worker.js` and browser install prompt.
- `apps/web/src/App.tsx`, `apps/web/src/pwa.css` — offline status wording and
  Social Update/Profitability Analysis Today entry points with safe pending
  states.
- `apps/web/README.md` — install, ownership, offline wording, and tool notes.
- Runako brain files — task/state/handoff evidence.

### Verified results

- `npm run build` passed: TypeScript completed and Vite transformed 26 modules,
  emitting the production bundle plus manifest/icon assets.
- Source inspection confirms `navigator.serviceWorker.register('/service-worker.js')`
  is the only worker action added; `apps/web/service-worker.js` itself and its
  sale/caching behavior were not modified by Runako.
- Manifest includes Street CEO name, standalone display, portrait orientation,
  theme/background colors, and the branded SVG icon.
- Install prompt is event-driven and safely absent when the browser does not
  offer installation. Social Update and Profitability Analysis are reachable
  from Today and display service-pending states without invented API calls.
- Offline copy says local screens remain available and avoids claiming sale
  queue/sync behavior owned by Fambai.

### Outstanding issues

- Browser install prompts require HTTPS or localhost plus browser PWA
  criteria; direct file-open previews cannot register a worker.
- Fambai remains responsible for service-worker sale integration and sync.
- Social/content and finance/analytics services still need to define their
  contracts before the two UI entry points become functional tools.

## 2026-10-30 — W3-VOICE-INPUT-001A: browser microphone capture UI

### Assignment summary

Add Runako-owned microphone/push-to-talk capture UX to `apps/web/`, keep
provider credentials out of the browser, integrate through a bounded backend
boundary when available, preserve text fallback, and never post an unconfirmed
voice sale.

### Files changed

- `apps/web/src/VoiceCapture.tsx` — browser `MediaRecorder` capture with
  press-and-hold pointer/keyboard controls and listening, transcribing,
  confirmation, success, and failure states. Includes a text command fallback.
- `apps/web/src/voice.ts` — optional `VITE_VOICE_INPUT_URL` multipart audio
  client; no provider SDK or key; validates a `{ transcript }` response.
- `apps/web/src/App.tsx` — mounts the voice capture panel on Sell and sends only
  confirmed command text to the existing manual sale review notice; Hwaro's
  existing sale client remains the transaction writer.
- `apps/web/src/voice.css`, `apps/web/src/main.tsx` — voice UI styling/import.
- `apps/web/README.md` — setup, boundary, fallback, and safety documentation.
- Runako brain files — assignment status and evidence updated.

### Verified results

- `npm run build` passed: TypeScript completed and Vite transformed 24 modules,
  emitting the production bundle.
- Source inspection confirms browser capture uses `navigator.mediaDevices` and
  `MediaRecorder`; no provider key, secret, or provider SDK is present.
- Permission denial, unsupported browsers, missing configured voice endpoint,
  empty recordings, non-2xx responses, and malformed transcripts reach a
  visible failure state with text fallback.
- A voice command is displayed for confirmation first; confirmation only
  marks it ready for manual sale review. It does not directly post a sale.
- The task stays within `apps/web/`; no backend, voice service, offline layer,
  API contract, or other agent-owned path was changed.

### Outstanding issues

- Hwaro/Inzwi must provide and configure the actual transcription URL and
  response contract before live transcription can be demonstrated. Until then,
  the UI intentionally reports the unavailable provider boundary and keeps text
  fallback available.
- The generated tracked `apps/web/tsconfig.tsbuildinfo` may receive a
  newline-only update during builds; a targeted cleanup was previously blocked
  by the workspace Git index-lock permission.

## 2026-10-30 — W3-LIVE-TEAM-001B: live Team Monitor client

### Assignment summary

Poll a configured local team activity endpoint, make live/fallback state
visible, and feed the existing 2D Team Monitor and simulated 3D Command Room
from one typed snapshot without implying private agent streams.

### Files changed

- `apps/web/src/teamActivity.ts` — shared `TeamSnapshot`/agent/stat types,
  deterministic fallback dataset, strict response parsing, configured endpoint
  fetcher, and Vite URL detection.
- `apps/web/src/App.tsx` — 10-second polling lifecycle, abort/cleanup, visible
  live/fallback/error/last-refresh metadata, and shared snapshot props for both
  Team views.
- `apps/web/src/room-overrides.css` — live/fallback badge and refresh/error
  styling.
- `apps/web/README.md` — `VITE_TEAM_ACTIVITY_URL`, polling cadence, response
  shape, and fallback behavior.
- Runako brain files — task/state/handoff evidence updated.

### Verified results

- Source inspection confirms `VITE_TEAM_ACTIVITY_URL` is the only live activity
  configuration, initial fetch plus 10-second polling are implemented, and
  abort/interval cleanup is present.
- Invalid HTTP responses, malformed payloads, and fetch errors visibly switch
  to the deterministic fallback with an error message and refresh timestamp.
- No URL keeps the app working in clearly labeled `Local fallback` mode.
- Both 2D and 3D views receive the same `TeamSnapshot` and activity metadata
  from `App`; the 3D wall and desk planners therefore update with the same
  live/fallback snapshot as the 2D lanes.
- UI copy continues to describe task metadata as a simulation boundary and
  explicitly rejects private thoughts and line-by-line generation claims.
- `npm run build` passed after the change: Vite transformed 21 modules and
  emitted the production bundle under `apps/web/dist/`.
- The build left a newline-only change in tracked `apps/web/tsconfig.tsbuildinfo`.
  A targeted Git restore was attempted but blocked by a workspace `.git/index.lock`
  permission error; this generated metadata change has no source semantics.

### Outstanding issues

- Re-run `npm install` and `npm run build` once npm certificate/registry access
  is repaired.
- The local activity producer must expose the documented `TeamSnapshot` JSON
  shape at the configured URL for live mode.

## 2026-10-30 — W2-RUNAKO-001 extension: dependency-free design preview

### Assignment summary

Add a browser-openable static design artifact while npm/Vite verification is
blocked, without replacing the React application.

### Files changed

- `apps/web/design-preview.html` — standalone HTML/CSS/JavaScript preview of
  Today, Sell, Stock, the 2D Team Monitor, and the simulated 3D Command Room.
- `apps/web/README.md` — direct-open instructions and clear distinction between
  the static preview and the React app.

### Verified results

- The file has no package imports, network assets, or Vite dependency; it can be
  opened directly from a browser as a local file.
- Inline preview navigation switches between all five requested designs. Team
  opens the existing 2D monitor and links to the simulated room, which links
  back to the 2D fallback.
- The preview is visibly marked `DESIGN PREVIEW`, `Preview mode`, and
  `SIMULATION ONLY`; it does not claim access to private thoughts or a real
  line-by-line generation stream.
- React app files were not replaced. npm build remains unavailable because the
  environment cannot install dependencies due to its certificate/registry
  error; this artifact avoids that dependency path.

## 2026-10-30 — W2-RUNAKO-001 extension: simulated 3D command room

### Assignment summary

Add a dependency-light simulated 3D Street CEO command room inside the existing
`apps/web/` scope, preserve the 2D Team Monitor, document both views, and keep
simulation/privacy boundaries explicit.

### Files changed

- `apps/web/src/App.tsx` — added optional injected team snapshot support,
  command-room toggle, CTO and specialist desk markup, planner cards, and wall
  board metrics.
- `apps/web/src/command-room.css`, `room-overrides.css` — dependency-light CSS
  perspective scene, desks, monitors, desk details, planner cards, wall board,
  warning chips, and mobile fallback layout.
- `apps/web/src/main.tsx` — imports command-room styling.
- `apps/web/README.md` — documents opening the 3D room, returning to the 2D
  fallback, and the optional local activity injection contract.
- Runako brain files — task, state, and handoff evidence updated.

### Verified results

- Source inspection confirmed a CTO desk, six specialist desks (Hwaro,
  Verengai, Dura, Runako, Fambai, Inzwi), adjacent planner/task cards with
  status and last activity, and wall stats for completed tasks, active tasks,
  commits, total/passing unit tests, and warnings/blocked items.
- The 2D Team Monitor remains the default Team view and has an explicit `Open
  3D room` action plus `Back to 2D monitor` fallback.
- UI copy labels the scene and activity as simulated and explicitly disclaims
  private thoughts and a true line-by-line generation stream.
- Deterministic fallback data is used unless a host injects
  `window.__STREET_CEO_TEAM_ACTIVITY__` before app load.
- Full build remains unverified because the earlier npm registry lookup failed
  with `ENOTFOUND`; no new dependency was added for this extension.

### Outstanding issues

- Re-run `npm install` and `npm run build` when registry access is available.
- A future integration may populate the documented window snapshot from a
  trusted local activity source; no backend endpoint or private agent stream is
  assumed by this UI.

## 2026-10-30 — W2-RUNAKO-001: mobile-first shell, manual sale UI, and Team Monitor

### Assignment summary

Build the first visible PWA slice in `apps/web/` excluding Fambai's offline
layer, then extend it with a local Team Monitor view on user request.

### Files changed

- `apps/web/package.json`, `index.html`, `tsconfig.json`, `vite.config.ts` —
  local React/Vite development shell.
- `apps/web/src/App.tsx` — Today/Sell/Stock views, manual basket and tender
  actions, responsive navigation, and six-lane Team Monitor with local activity
  model plus simulated typing preview.
- `apps/web/src/api.ts` — small documented-contract API boundary with labeled
  demo catalogue fallback and sale request shape.
- `apps/web/src/main.tsx`, `styles.css`, `monitor.css` — app entry and styling.
- `apps/web/README.md` — local dev command, API configuration, Team Monitor
  entry point and simulation disclosure.

### Verified results

- Source inspection via `rg` confirmed `Today`, `Sell`, `Stock`, and `Team`
  navigation; `apiClient` boundary; cash/bank tender controls; and six lanes:
  Hwaro, Verengai, Dura, Runako, Fambai, Inzwi.
- The Team Monitor exposes each lane's status, current task, changed-file
  count/list, and last activity. Its terminal panel says `SIMULATION` and
  explicitly says it is not a live line-by-line subagent stream.
- No IndexedDB, service-worker, or sync implementation was added by Runako.
- `npm install --no-audit --no-fund` and `npm run build` were attempted. The
  environment could not resolve `registry.npmjs.org` (`ENOTFOUND`), leaving no
  installed dependencies and preventing a production build. This is an
  external verification blocker, not a claimed passing test.

### Outstanding issues

- Re-run dependency install and production build when npm registry access is
  available. Chengetai should run the broader quality gate afterward.
- Fambai owns the existing offline layer and should integrate its queue/sync
  states without changing this UI boundary.

### Next-session instructions

- Read this handoff and `brain/current-state.md`, then run the documented local
  command from `apps/web/` after dependencies are available.

## 2026-10-29 — TEST-MEMORY-001: summarize agreed React PWA frontend architecture

### Assignment summary

Read-only task from Mutungamiri: follow AGENTS.md activation protocol, read
docs/architecture.md and docs/product-requirements.md, summarize the agreed
frontend architecture. No application code or shared-doc changes; write only to
own brain files under agents/runako/brain/.

### Findings summary

Agreed frontend architecture, sourced only from the repository docs read:

- Stack: React + TypeScript Progressive Web App, mobile-first, responsive. No
  native Android/iOS app for the MVP. Users are street vendors and
  micro-retailers on low-cost Android phones with intermittent connectivity.
- Ownership: Runako owns Web UI (`apps/web/`); Fambai owns the offline layer
  inside it (service worker, IndexedDB schema, sync engine). Runako consumes
  Fambai's offline/online state hooks and queued-transaction UX states.
- Backend: Python FastAPI + PostgreSQL. Contract-first APIs owned by Hwaro;
  Runako consumes `docs/api-contracts.md` and never invents endpoints.
- Data flows Runako renders: sale recorded via UI / offline queue / voice;
  one auditable transaction decrements stock (Dura) and updates ledger
  (Verengai); offline sales replay via idempotent sync with deterministic
  conflict resolution; reconciliation, reporting, and insights read from the
  same ledger and stock truth.
- UX surfaces: record a sale (UI, offline-capable, voice), stock tracking
  (catalog, purchases, decrements, adjustments, counts), cash/bank
  reconciliation for non-accountants, financial reporting (sales, P&L,
  cashflow), Meta-powered business insights (run-out warnings, margin
  highlights). Voice: "Apo" starts listening, "Napo" ends the command; short
  commands only, and voice never posts an unconfirmed sale (Inzwi pipeline,
  Ungwaru/Chiono insight services wired into Runako's UI).
- Binding constraints affecting UI: no undocumented endpoints; schema-validated
  AI outputs with tested fallbacks; Chengetai gates releases; Ruzivo reviews
  financially significant features. Demo bar: Apo greeting, voice sale via
  Napo, stock and cash update, offline sale, clean reconnect reconciliation,
  one credible insight.
- Status: agreed plan only; no code implements it yet (`apps/web/` not
  scaffolded).

### Files changed

- agents/runako/brain/tasks.md — marked TEST-MEMORY-001 complete with
  acceptance evidence.
- agents/runako/brain/current-state.md — recorded completed work, verified
  results, next action.
- agents/runako/brain/handoffs.md — this entry.
- No application code or shared docs created or modified.

### Tests run

None — read-only task. No code exists to test and none was written. Nothing to
verify beyond confirming the cited docs were read and the summary matches them.

### Outstanding issues

- None for this task. Standing dependency: UI implementation awaits Hwaro's
  API contracts and `apps/web/` scaffolding decision.

### Instructions for next session

- Read this entry plus brain/tasks.md and brain/current-state.md before
  starting. Activation context (role, ownership, constraints) is unchanged.
- Await Mutungamiri's next task assignment; confirm file scope per
  agents/runako/role.md before writing anything outside agents/runako/brain/.
