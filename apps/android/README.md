# Street CEO Android APK

The native Capacitor project and Gradle wrapper are included. Do not run
`cap add android` again. Generated web assets, SDK paths, Gradle caches, signing
keys and APKs remain local and ignored.

## Prerequisites

- Node.js22.18+ and npm; Python backend dependencies from the root README.
- Android Studio, Java17+ (Android Studio's bundled runtime works), Android SDK35.
- Configure your SDK through Android Studio or a local ignored `local.properties`.
- Internet for the first Gradle/dependency download. Later offline builds work
  only when the required artifacts are already cached.

## Build

Start the API on a reachable PC interface, port8001, with SQLite and one worker.
Keep the phone and PC on a reachable network. Use your own PC's LAN address;
`localhost` on the phone refers to the phone, not the PC.

From `apps/web`, set these variables before `npm run build`:

```powershell
# PowerShell example; replace the address with your PC
$env:VITE_API_BASE_URL='http://192.168.1.20:8001'
$env:VITE_SHOP_ID='00000000-0000-0000-0000-000000000001'
npm ci
npm run build
```

On macOS/Linux, use `export VITE_API_BASE_URL=...` and `export VITE_SHOP_ID=...`.
Then:

```sh
cd ../android
npm ci
npm run copy-web-assets
npm run sync
cd android
```

Build with `.\gradlew.bat assembleDebug` on Windows or
`sh ./gradlew assembleDebug` on macOS/Linux. Set JAVA_HOME if necessary.
The APK appears at `app/build/outputs/apk/debug/app-debug.apk`.
Install using Android Studio, `adb install -r` or the device's installer.
Grant microphone permission and check Profile > Shop connection.

Local HTTP is enabled for this connected demo. A public release needs HTTPS
and deployment hardening. The API must be reachable through the host network
policy; these scripts do not change firewall rules.

## Rehearse on a real phone

Open Sell, say Apo/items/Napo, answer confirmation/payment, and start a second
sale by Apo. Check totals/change, stock/history and persistence. Check upward
swipe system-navigation reveal, keyboard, rotation and background/resume.
Build success is not physical-device acceptance. See `docs/demo-runbook.md`
and `docs/demo-mvp-verification.md` from the repository root.
