# Street CEO Android APK — local development

## Decision

Street CEO will use a Capacitor Android shell around the existing Vite build.
This preserves the mobile UI and lets us add Android permissions and plugins
without rewriting the application in native Android UI.

## Configuration

- Application id: `com.streetceo.app`
- Web entry: `apps/android/web-assets/` copied from `apps/web/dist/`
- Local API: `http://192.168.10.213:8000`
- Development transport: cleartext HTTP enabled in Capacitor
- Release transport: HTTPS required; cleartext must be removed

## APK workflow

1. Build the web app in `apps/web` with `npm run build`.
2. In `apps/android`, run `npm install` and `npm run copy-web-assets`.
3. Run `npx cap add android` once, then `npm run sync` after each web build.
4. Open the generated Android project in Android Studio.
5. Build `app` → `Build APK(s)` for a debug APK.
6. Install the APK on a phone connected to the same Wi-Fi as the API host.

## Acceptance checks

- The app opens the bundled Street CEO web build without a browser address bar.
- The Android package is `com.streetceo.app`.
- The app can reach the local API over HTTP during development.
- `RECORD_AUDIO` is declared and requested at runtime by the native activity.
- Capacitor's WebView permission bridge grants `AUDIO_CAPTURE` only after the
  Android microphone permission is granted.
- Microphone and file-upload flows are tested on a real Android device.
- No API keys are bundled in the APK.

## Microphone permission troubleshooting

The debug APK requests microphone access when it starts. The voice screen then
uses the normal WebView `getUserMedia({ audio: true })` flow; no provider key is
stored in the APK. If microphone access was previously denied, open Android
Settings → Apps → Street CEO → Permissions → Microphone and choose Allow, then
restart the app. The first voice attempt must also be made from the bundled
Capacitor app, not a remote browser page.

The native shell declares both `RECORD_AUDIO` and `MODIFY_AUDIO_SETTINGS`. The
Capacitor `BridgeWebChromeClient` receives the WebView `AUDIO_CAPTURE` request,
asks Android for any missing permission, and calls `request.grant(...)` only
when permission is granted.

## Handoff — Android microphone permission fix — 2026-10-30

### Assignment

Fix the APK screenshot error where the Capacitor WebView reported that
microphone permission was blocked. Scope was limited to the Android shell and
Android packaging documentation; no `apps/web` source was changed.

### Files changed

- `apps/android/android/app/src/main/AndroidManifest.xml`
  - Declares `MODIFY_AUDIO_SETTINGS` alongside `RECORD_AUDIO`.
- `apps/android/android/app/src/main/java/com/streetceo/app/MainActivity.java`
  - Requests `RECORD_AUDIO` at Android runtime on app startup for Android 6+
    devices.
  - Leaves Capacitor's `BridgeWebChromeClient` in place to handle WebView
    `AUDIO_CAPTURE` and grant it only after Android permission is available.
- `docs/mobile/android-apk-local-development.md`
  - Documents the runtime permission flow and recovery steps after a previous
    denial.

### Validation

- `apps/android/android/gradlew.bat assembleDebug`: **BUILD SUCCESSFUL**.
- APK: `apps/android/android/app/build/outputs/apk/debug/app-debug.apk`.
- Package remains `com.streetceo.app`.

### Remaining device check

Install this newly built APK over the previous debug APK, accept the Android
microphone prompt, then press and hold **Press and hold to talk**. If the old
APK had already been denied, manually enable Street CEO → Permissions →
Microphone in Android Settings before retrying. A physical-device microphone
test was not available from the build environment, so that final check remains
with the APK tester.

## Handoff — W6-DEMO-APK-001 — 2026-10-31

### Assignment

Rebuild the Android debug APK from the latest verified web bundle after the
demo MVP changes. Android files and packaging only.

### Commands and evidence

- `npm run copy-web-assets` from `apps/android`: passed; copied `apps/web/dist`
  into `apps/android/web-assets`.
- `npm run sync` from `apps/android`: passed; Capacitor copied the web assets
  into the Android project.
- `gradlew.bat assembleDebug` from `apps/android/android`: **BUILD SUCCESSFUL**.
- APK timestamp: `2026-10-31 10:56:51 +02:00`.
- APK size: `7,106,762` bytes.
- APK SHA-256:
  `AE01A4214DFB56C37D5F0B4D8D501B1EC7A9307193F182108B39CAC3258ED810`.

### Bundle verification

The APK archive contains the current bundle entries:

- `assets/public/index.html`
- `assets/public/office.html`
- `assets/public/assets/office-BGvT3A7-.js`
- `assets/public/assets/shop-DLDHkwXl.js`
- `assets/public/assets/styles-DOyUzLqI.js`

These match the latest copied web assets generated on October 31, confirming
the APK includes the current Street CEO web changes present in `apps/web/dist`
at build time.

### Download/install path

No phone-reachable dev server was active during this build, and no web source
or public download route was changed because this assignment is Android-only.
Transfer this exact file to the phone by USB, WhatsApp/Telegram, Drive, or a
local file-share:

`apps/android/android/app/build/outputs/apk/debug/app-debug.apk`

Open the file on Android, allow installation from the chosen file manager when
prompted, and install it over the previous debug build. No physical-phone
installation or runtime test is claimed here.

## Handoff — W6-APK-PHONE-001 — 2026-10-31

### Build and LAN delivery

- Latest `apps/web/dist` copied with `npm run copy-web-assets`.
- Capacitor assets synchronized with `npm run sync`.
- `gradlew.bat assembleDebug`: **BUILD SUCCESSFUL**.
- Temporary LAN download server started on the PC at port `9001`.
- Verified from the PC with HTTP status `200`:
  `http://192.168.10.213:9001/app-debug.apk`

### Current APK evidence

- File: `apps/android/android/app/build/outputs/apk/debug/app-debug.apk`
- Timestamp: `2026-10-31 14:06:18 +02:00`
- Size: `7,137,873` bytes
- SHA-256:
  `96C8F560070D394784DB2F4B5849B20C16DFF749A13B7EAB37C9EF3D9F3BAE5D`

### Physical-device test status

- ADB was started successfully, but `adb devices -l` returned no devices.
- Physical APK installation: **not tested**.
- Physical viewport/responsive check: **not tested**.
- Physical microphone check: **not tested**.
- Physical sale smoke test: **not tested**.

The LAN URL is ready for the phone if it is on the same Wi-Fi network. Opening
it on the phone downloads the debug APK; Android may require enabling install
permission for the browser or file manager. The temporary server must remain
running on the PC for the download to work.

## Handoff — W6-POINT-2-APK — 2026-10-31

- Fresh `npm run build` completed successfully in `apps/web`.
- `npm run copy-web-assets` and `npm run sync` completed successfully.
- `gradlew.bat assembleDebug` completed successfully.
- APK: `apps/android/android/app/build/outputs/apk/debug/app-debug.apk`.
- Timestamp: `2026-10-31 16:12:33 +02:00`.
- Size: `7,139,989` bytes.
- SHA-256: `5181AC49138410B4A9474B95AF90F5736BE6F42355094F117733F4E7E328C265`.
- `apksigner verify --verbose`: v1 and v2 signatures valid; one signer.
- Offline sync was not added or treated as a release criterion for this APK.
- ADB reported no connected device; physical installation and phone smoke tests
  were not performed.

## Handoff — W6-APK-QUICK-SALE-001 — 2026-10-31

- Fresh `npm run build` completed successfully in `apps/web`.
- `npm run copy-web-assets` and `npm run sync` completed successfully.
- `gradlew.bat assembleDebug` completed successfully.
- The APK contains the latest `shop-CnODwLyw.js` bundle.
- Compiled-bundle evidence includes `Quick Sale`, receipt, and undo UI strings.
- APK: `apps/android/android/app/build/outputs/apk/debug/app-debug.apk`.
- Timestamp: `2026-10-31 21:37:00 +02:00`.
- Size: `7,167,699` bytes.
- SHA-256: `4F4E0762A980CB495E94869212E740B5D1611D6B89688EDECA2B0987ED0BE77C`.
- `apksigner verify --verbose`: v1 and v2 signatures valid; one signer.
- Online-only demo packaging; offline sync is explicitly out of scope.
- No physical-phone installation or testing was performed.

## Blocker recorded

The Android SDK and generated Gradle wrapper are present. The first debug
build was blocked by the machine Java certificate configuration while Gradle
tried to download `gradle-8.11.1-all.zip` (`PKIX path building failed`). The
cached offline Gradle fallback did not contain the Android Gradle Plugin
artifact. Fix the Java/Gradle certificate trust or open the generated project
in Android Studio, then run `android\gradlew.bat assembleDebug`.
