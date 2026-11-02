# Mobile UI/UX Handoff

**Date:** 2026-10-30  
**Owner:** Mobile UI/UX design  
**Target:** Immediate Capacitor Android implementation

## Deliverable

The first Android mobile experience is specified in [mobile-ui-spec.md](../mobile-ui-spec.md). It defines the five-tab shell, the five MVP screens, voice confirmation states, invoice review states, profitability analysis, team filtering, typography, spacing, brand usage, and local APK constraints.

## Implementation order

1. Wrap the existing mobile-first web build with Capacitor and establish the app shell.
2. Confirm Today and Sell work end to end, including a multi-item basket and manual confirmation.
3. Add the Apo/Napo voice states on top of the same basket and sale endpoint.
4. Add Stock invoice upload/review, then Profitability question/result states.
5. Replace the Team room as the default mobile status view with the readable filtered task list; keep the room as an optional visual view.
6. Test debug APK against the local FastAPI address over the LAN, then prepare a signed build separately.

## Product decisions carried forward

- The real logo asset is `apps/web/public/street-ceo-logo.png`; it must be reused, not replaced by text or an `SC` placeholder.
- Voice must never post an unconfirmed sale.
- Profit answers must show their period, inputs, and assumptions.
- Invoice upload must not imply stock changed until line items are reviewed and posted.
- Team progress is repository evidence, not simulated typing or private agent activity.
- Local debug APK may use HTTP and a LAN IP; release distribution should use HTTPS.

## Open implementation dependencies

- Capacitor Android project is now scaffolded under `apps/android/android/` with
  application id `com.streetceo.app`.
- Debug APK signing configuration is intentionally not committed yet; the
  first local build can use Android's default debug signing.
- The backend API base URL needs a debug/release configuration mechanism.
- Full multi-item Apo/Napo basket completion remains a functional dependency for the voice acceptance checklist.
- Invoice line-item extraction and live profitability analysis remain product dependencies.

## Handoff note

The Android shell and local packaging documentation are now present. The web
build was validated with `npm run build`, copied into `apps/android/web-assets`,
and synced into the native Capacitor assets. The debug APK build was attempted;
Gradle could not download its distribution because the machine Java truststore
reported `PKIX path building failed`. The next owner should fix that trust
configuration or open `apps/android/android/` in Android Studio and build the
debug APK.
