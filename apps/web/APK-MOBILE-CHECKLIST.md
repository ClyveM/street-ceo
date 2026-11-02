# APK install and phone test checklist

W4-MOBILE-QA-FINAL-001 · 2026-10-31 · Runako

## Browser checks completed

- Measured actual 320x740 and 390x844 viewports; a requested 430x932 measured
  431x932 and is recorded as that value. Desktop baseline: 1280x720.
- Synthetic product PNG decoded in the narrow browser and previewed. Social
  selection and Stock share the local preview; demo upload stays disabled.
- At 320, fixed body horizontal overflow: root client/scroll width now **305/305**.
- At 320, fixed clipped office chat: dialog now x=10..295 inside 305 client
  width, with dialog client/scroll **268/268**. At 390, right edge **365** inside
  375 client width; client/scroll **338/338**. Composer font is 16px.
- Optional product-photo file target increased from **24px to 48px** height.
- Invoice lines/product matching and recurring expense period fields were
  checked at actual 320x740, with root client/scroll width **305/305** and no
  overflowing form controls. A synthetic invoice and one-off expense were
  confirmed against the current local API; this does not verify phone access.
- Social request controls and disabled generated-image export remain readable;
  provider availability was not established by layout testing.

These are browser viewport tests, not physical Android/WebView tests. Browser
scrollbars account for client widths below requested viewport widths. The
viewport tool targets the selected tab; every measurement was checked in-page.

## Install and verify on the user's phone

1. Have the Android owner build/package the latest verified web output and
   supply the APK with build date/version. Existing build instructions are in
   `docs/mobile/android-apk-local-development.md`; this task does not edit or
   rebuild Android files. The package is documented as `com.streetceo.app`.
2. Install/update that APK through the phone's normal trusted installation flow.
   Do not use a PWA install banner. Confirm the real Street CEO logo and
   Today/Sell/Stock navigation, with no shop Team page or install notification.
3. Connect to the intended backend using an address reachable from the phone,
   not the phone's localhost. Verify the actual shop exists and the catalogue
   is live. Keep backend credentials out of the APK and screen recording.
4. Test portrait, landscape, large text, display cutouts and bottom gesture bar.
   Confirm no sideways scrolling or covered buttons. Open the office separately
   at `/office.html`; verify its project/room controls and chat can scroll/close.
5. Choose a real camera/gallery photo and a PDF invoice; test permission denial,
   cancellation, wrong file type, oversize file and successful local preview.
   Verify any real upload receipt. Confirm previews/temporary API storage are
   not presented as durable download URLs.
6. Test the soft keyboard on caption, invoice, cost, expense and chat fields.
   Check the focused field and primary action remain reachable; test Android
   Back returning from details and dismissing keyboard/chat appropriately.
7. Test microphone permission and capture on-device, including denial and text
   fallback. Permission/camera/gallery/WebView behavior is **not** proven by
   desktop emulation.
8. In a designated demo data set, confirm one sale, changed stock, receipt/history,
   invoice review/cost effects and one expense only after their API routes pass.
   Test slow/offline/reconnect without claiming queue/replay behavior unless
   Fambai/Chengetai have verified it.
9. Try actual draft export/download and open the file in the phone's Downloads
   app. Generated-image download is a separate provider/output-contract test.
   No automatic Facebook publication should occur.
10. Report phone model, Android/WebView version, APK version, screenshots and
    each pass/fail. A physical-device pass remains with the user/phone tester.
