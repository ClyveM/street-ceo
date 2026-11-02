# Fambai — Current State

Updated 2026-10-30 for W2-FAMBAI-001.

## Status

Implemented the offline queue, cache contracts, sync engine, and service-worker shell under `apps/web/`.

## Work in progress

- `apps/web/src/offline/` contains the storage, queue, sync, cache, and tests.
- `apps/web/service-worker.js` provides install/activate and network-first shell caching.

## Latest verified results

- `npm run test:offline` from `apps/web`: 4 passed.
- Repository `python tests/run_checks.py`: 5 passed, 1 pre-existing backend import error (`No module named 'services'`) outside Fambai scope.

## Known blockers

- Hwaro still needs to expose/confirm the expense endpoint and response shape. The client transport is intentionally endpoint-agnostic and sends the documented idempotency key contract.

## Next immediate action

Mutungamiri should review the offline interface and coordinate Runako integration; Chengetai should include `npm run test:offline` in the web quality gate.

## 2026-10-31 — W6-DEMO-APK-ONLINE-001

Assignment: rebuild online-only Android demo after current web handoff; Android packaging and own brain scope. Offline sync excluded.
Fresh verification: npm run build passed (73 modules); copy-web-assets and Capacitor sync passed; Gradle assembleDebug passed (85 tasks, 21 executed). Initial restricted Gradle cache access failed; approved build succeeded.
Artifact: apps/android/android/app/build/outputs/apk/debug/app-debug.apk; 7167699 bytes; SHA-256 4F4E0762A980CB495E94869212E740B5D1611D6B89688EDECA2B0987ED0BE77C. Same hash/timestamp as previous Quick Sale APK: rebuilt inputs produce unchanged artifact.
Signing: apksigner verification passed, v1/v2 true, one signer; metadata protection warnings emitted. No claim of production release signing.
Files: regenerated web dist and Android copied/synced build outputs; no application source edits. This entry persists evidence in own brain.
Phone checklist: transfer exact APK; install/update com.streetceo.app; allow install from selected source and microphone permission; same Wi-Fi as API host 192.168.10.213:8000; open Today/Stock; test Quick Sale with Cash/Bank, receipt/change and stock update; test undo and voice microphone; verify invoice upload/review. Use synthetic demo transactions. Physical installation and runtime checks remain unverified; no phone test claimed.
Next: Chengetai release review and connected-phone validation; no offline acceptance criterion.

Device discovery limitation: fresh adb devices -l could not start/connect to the ADB daemon; connected-device inventory could not be established. APK archive inspection confirms assets/public/assets/shop-CnODwLyw.js.

## 2026-10-31 — W6-APO-HANDSFREE-001 checkpoint
User explicitly requested hands-free Apo start, Napo end, pronunciation setup, and APK rebuild. Coordinated Runako frontend scoped worker and Chengetai read-only QA under AGENTS coordination; parent owns Android shell/build and Fambai brain. No offline changes.
Android native ApoSpeechPlugin added with foreground SpeechRecognizer, microphone permission/availability checks, main-thread lifecycle cleanup, speech/speechError/speechEnd plus native pause/resume events. MainActivity registers plugin; manifest adds RecognitionService visibility. Initial native assembleDebug passed; final frontend integration/build and phone testing pending. Speech recognition may depend on Android provider/network; pronunciation setup matches user-confirmed ASR text aliases, not acoustic model training. Background/locked-screen wake is not implemented.

## 2026-10-31 — W6-APO-HANDSFREE-001 final handoff
Assignment: user-requested Apo wake/Napo end, pronunciation setup, APK rebuild. Offline excluded.
Files: Android ApoSpeechPlugin.java, MainActivity.java registration, AndroidManifest.xml recognition-service query; generated Android assets. Runako owns frontend changes and persisted own handoff (HandsFreeVoice/speechRecognition/wakePhrase/VoiceCapture/quickSale/App and focused tests). Chengetai completed source review and persisted own handoff.
Evidence: Runako frontend suite 98 passed, final TypeScript/Vite build passed (76 modules, shop-BUM9vkav.js); Chengetai fresh focused wake suite 5 passed after decimal fix. Parent copy-web-assets and cap sync exit0; final Gradle assembleDebug BUILD SUCCESSFUL (85 tasks, 27 executed). apksigner verify passes v1/v2, one signer. APK archive contains final shop-BUM9vkav.js with hands-free and pronunciation controls.
APK: apps/android/android/app/build/outputs/apk/debug/app-debug.apk; 7186139 bytes; SHA256 BB0F7D95EBA1351253C3C0F0D46F1923C730178C9359A3EE5EAE1F0398998420.
Usage/checklist: install updated debug APK, open Sell, allow microphone; Teach my Apo/Napo pronunciation > Pronounce Apo then check/save heard phrase, repeat Napo; Enable hands-free; say Apo 1 Coke Napo, then answer payment using Apo Cash 100 Napo or controls. Confirm receipt and authoritative stock. Test off switch, background/resume, permission denial, setup reset and spoken prompt echo suppression on phone.
Limitations: foreground sale-screen only, not closed-app or screen-off wake; requires Android recognition service (may use network). Enrollment stores confirmed ASR aliases locally, does not train acoustic model. Final-result recognition depends on provider finalization. ADB daemon unavailable in prior fresh check; no physical phone validation claimed. QA found no unresolved reviewed source blocker; device checks remain pending.
Next: phone installation/recognition validation. No unrelated files edited or git commit made.

## 2026-10-31 — W6-VOICE-ERROR-001 checkpoint
User screenshot reports generic unknown-outcome warning outside basket. Fresh code inspection: quickSale call wraps all fetch failures as uncertain, including read-only interpretation; recovery UI is modal-only. Runako assigned frontend correction and regression tests. Approved native GET local API health returned status ok; phone reachability and screenshot root network cause unverified. No sale/reset performed.

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
## 2026-11-01 — W6-VOICE-COCA-COLA-001

Fresh online debug APK packaged after the web voice-framing fix. Build, asset
copy/sync, and Gradle passed. Device and microphone validation remain pending.

## 2026-11-01 — APK-DOWNLOAD-INVESTIGATION checkpoint
User reports website download incomplete. Fresh approved LAN full GET http://192.168.10.213:8081/street-ceo.apk returned200,7205492bytes, matching artifact.json size and SHA256. No download server/API changes or restart. Phone URL/network/failure stage clarification requested; actual phone download unverified. Server currently lacks Range resume support by source inspection; no evidence yet that this caused user failure.
