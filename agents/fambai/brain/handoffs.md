# Fambai — Handoffs

## Handoff — W2-FAMBAI-001 — 2026-10-30

### Assignment

Implement the mobile offline layer: idempotent manual sale/expense queue,
catalogue/totals cache, visible sync/conflict contracts, service-worker shell,
and tests. Scope stayed within `apps/web/` and Fambai's own brain files.

### Files changed

- `apps/web/src/offline/types.js`: queue statuses, source markers, payload validation, stable fingerprinting.
- `apps/web/src/offline/store.js`: IndexedDB store plus test-safe memory store and cache helpers.
- `apps/web/src/offline/queue.js`: idempotent sale/expense enqueue and ordered listing.
- `apps/web/src/offline/sync.js`: replay engine with pending/syncing/committed/conflict/failed state reporting.
- `apps/web/src/offline/index.js`: public exports.
- `apps/web/src/offline/README.md`: Runako-facing interface contract.
- `apps/web/src/offline/offline.test.js`: four automated tests.
- `apps/web/service-worker.js`: app-shell cache and offline GET fallback.
- `apps/web/package.json`: ES module mode and offline test script.

### Evidence

- `npm run test:offline` in `apps/web`: 4 tests passed, 0 failed.
- `python tests/run_checks.py` at repository root: 5 passed, 1 error in the pre-existing backend smoke test (`ModuleNotFoundError: No module named 'services'`); no Fambai test failed.

### Outstanding issues / next agent instructions

- Hwaro must confirm the expense endpoint and response shape; the transport boundary is ready but intentionally does not invent that endpoint.
- Runako should consume `SyncEngine.state`, `QUEUE_STATUS`, `SOURCE`, and cache helpers through `src/offline/index.js`.
- Chengetai should add the web test command to CI and validate service-worker behavior on the target device matrix.

## 2026-10-31 — W6-DEMO-APK-ONLINE-001

Assignment: rebuild online-only Android demo after current web handoff; Android packaging and own brain scope. Offline sync excluded.
Fresh verification: npm run build passed (73 modules); copy-web-assets and Capacitor sync passed; Gradle assembleDebug passed (85 tasks, 21 executed). Initial restricted Gradle cache access failed; approved build succeeded.
Artifact: apps/android/android/app/build/outputs/apk/debug/app-debug.apk; 7167699 bytes; SHA-256 4F4E0762A980CB495E94869212E740B5D1611D6B89688EDECA2B0987ED0BE77C. Same hash/timestamp as previous Quick Sale APK: rebuilt inputs produce unchanged artifact.
Signing: apksigner verification passed, v1/v2 true, one signer; metadata protection warnings emitted. No claim of production release signing.
Files: regenerated web dist and Android copied/synced build outputs; no application source edits. This entry persists evidence in own brain.
Phone checklist: transfer exact APK; install/update com.streetceo.app; allow install from selected source and microphone permission; same Wi-Fi as API host 192.168.10.213:8000; open Today/Stock; test Quick Sale with Cash/Bank, receipt/change and stock update; test undo and voice microphone; verify invoice upload/review. Use synthetic demo transactions. Physical installation and runtime checks remain unverified; no phone test claimed.
Next: Chengetai release review and connected-phone validation; no offline acceptance criterion.

Device discovery limitation: fresh adb devices -l could not start/connect to the ADB daemon; connected-device inventory could not be established. APK archive inspection confirms assets/public/assets/shop-CnODwLyw.js.

## 2026-10-31 — W6-APO-HANDSFREE-001 final handoff
Assignment: user-requested Apo wake/Napo end, pronunciation setup, APK rebuild. Offline excluded.
Files: Android ApoSpeechPlugin.java, MainActivity.java registration, AndroidManifest.xml recognition-service query; generated Android assets. Runako owns frontend changes and persisted own handoff (HandsFreeVoice/speechRecognition/wakePhrase/VoiceCapture/quickSale/App and focused tests). Chengetai completed source review and persisted own handoff.
Evidence: Runako frontend suite 98 passed, final TypeScript/Vite build passed (76 modules, shop-BUM9vkav.js); Chengetai fresh focused wake suite 5 passed after decimal fix. Parent copy-web-assets and cap sync exit0; final Gradle assembleDebug BUILD SUCCESSFUL (85 tasks, 27 executed). apksigner verify passes v1/v2, one signer. APK archive contains final shop-BUM9vkav.js with hands-free and pronunciation controls.
APK: apps/android/android/app/build/outputs/apk/debug/app-debug.apk; 7186139 bytes; SHA256 BB0F7D95EBA1351253C3C0F0D46F1923C730178C9359A3EE5EAE1F0398998420.
Usage/checklist: install updated debug APK, open Sell, allow microphone; Teach my Apo/Napo pronunciation > Pronounce Apo then check/save heard phrase, repeat Napo; Enable hands-free; say Apo 1 Coke Napo, then answer payment using Apo Cash 100 Napo or controls. Confirm receipt and authoritative stock. Test off switch, background/resume, permission denial, setup reset and spoken prompt echo suppression on phone.
Limitations: foreground sale-screen only, not closed-app or screen-off wake; requires Android recognition service (may use network). Enrollment stores confirmed ASR aliases locally, does not train acoustic model. Final-result recognition depends on provider finalization. ADB daemon unavailable in prior fresh check; no physical phone validation claimed. QA found no unresolved reviewed source blocker; device checks remain pending.
Next: phone installation/recognition validation. No unrelated files edited or git commit made.

## 2026-10-31 — W6-VOICE-ERROR-001 final handoff
User screenshot showed unknown-outcome alert without recovery control. Runako fixed frontend classification: transcript/audio connection failures are retryable and never claim submitted sale; mutation uncertainty retains same-key recovery. Recovery/retry controls available outside modal. Eleven focused tests passed; web build passed (76 modules). Parent copy/sync and Gradle assembleDebug passed; signature verification exit0; APK archive verified shop-vZn_ZBuN.js.
Artifact: apps/android/android/app/build/outputs/apk/debug/app-debug.apk; 7186373 bytes; SHA256 72FC0BEC17C666B1FC348E9B1007317DE39F66D80E2C94766ACAE3744EF54DD8.
Changed: generated packaging outputs and own memory; frontend changes and handoff by Runako. Approved GET API health status ok from PC; actual phone connection cause unverified. No sale/reset/phone test performed. Next: install APK, inspect Shop Connection API address and same-network reachability if connection failure persists; recover actual uncertain submissions with original reference.

## 2026-10-31 — W6-VOICE-PROFILE-001 final handoff
User requested actual voice error fix, Profile pronunciation placement, simplified UI. Runako moved enrollment to Profile/avatar/fourth nav tab; Sell compact handsfree, collapsed recording/type fallback, concise error with expandable connection detail, redundant greetings removed. Full frontend103passed; final77module build shop-BcOa5ydJ.js. Chengetai9scoped tests passed; no browser/phone visual QA.
Confirmed backend cause: approved LAN OPTIONS APK Origin http://localhost returns400 Disallowed CORS origin; GET health200. Hwaro exact-origin allowlist source fix +3approved-host preflight tests passed. Running uvicorn pid58820 no reload. Runtime fix NOT activated: restart approval requested due in-memory data loss, no answer received. No server restart/reset/sale performed.
Parent final copy/sync exit0; Gradle assembleDebug successful; full captured apksigner verify exit0 v1/v2 true one signer; archive final bundle verified. Earlier piped signer output was prematurely truncated by Select-Object and yielded nonzero pipeline, corrected by capturing entire output before selecting.
Artifact apps/android/android/app/build/outputs/apk/debug/app-debug.apk SHA256 FEB8CCC4218F9CC8FF0E9637576F5CD5E0C1FB5FAF6D0F8214ECDA363081D3BE.
Own changes packaging+memory only; web/backend changes and handoffs by owners. Next: obtain pending restart answer, restart API only if approved then verify live preflight, phone install/network/UI/recognition test. Offline unchanged.

## 2026-10-31 — W6-VOICE-PROFILE-001 runtime activation
User explicitly approved restarting demo server despite in-memory record loss. Verified old uvicorn PID58820 exact command, stopped it and started same Python module/host/port hidden with PID21264. Logs under agents/fambai/demo-api.stdout.log and stderr.log. Health GET ok; live APK-origin OPTIONS now200 and Access-Control-Allow-Origin http://localhost (previously400). Read-only transcript POST '1 coke' with APK origin returned200, needs_confirmation, one line and matching allow-origin. No commit/sale/reset invoked. Restart may clear previous in-memory records as approved. Latest APK remains FEB8CCC4218F9CC8FF0E9637576F5CD5E0C1FB5FAF6D0F8214ECDA363081D3BE. Runtime CORS fix verified; actual phone operation still untested. Next: user retries installed APK; retain no claims of phone/microphone verification.
## Handoff — W6-VOICE-COCA-COLA-001 — 2026-11-01

Packaged the updated web voice flow. `npm run build`, `npm run copy-web-assets`,
`npm run sync`, and Gradle `assembleDebug` passed. APK:
`apps/android/android/app/build/outputs/apk/debug/app-debug.apk`; 7,172,104
bytes; SHA-256
`14A30AC5521203426919031C6071488C0AD14729B96DF1D94036C5E5A6591B50`.
No connected Android device was exposed and `apksigner` was not on PATH, so
physical install, microphone recognition, and signer verification remain open.
