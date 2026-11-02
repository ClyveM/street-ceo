# Counter polish QA — 2026-11-01

Task: COUNTER-POLISH-QA-001. Final targeted software/source gate: **PASS**.

The Owner confirmed a physical sale works. QA viewed the supplied completed
receipt photo and existing logo read-only. That supports the working core flow;
the new layout and consecutive-sale behavior still require a phone retest.

## Reviewed behavior

- Apo or leading Apple advances only a verified completed receipt with voice
  enabled and no busy, blocked, TTS or uncertain state. Pending product matching,
  clarification and payment are preserved.
- Wake events and command content travel separately. Closing the receipt does
  not reset the wake machine: a full same-utterance basket, bare wake followed by
  another utterance, and partial basket continuation remain intact.
- One controlled voice preference is shared between the main counter and modal.
  Explicit pause is stored and respected across close/remount. Typing focus and
  speech/background suspension pause recognition without changing that preference.
- The ASR effect does not depend on modal `open` or callback identity. Completed
  success → idle leaves reply mode unchanged. Wake-dismiss skips restoration of
  an old editing input, focuses the nonediting counter, and resets its suppression
  flag at the next modal opening. Done applies the same safe focus behavior.
- Completed receipt amounts come from the validated saved receipt. Latest receipt
  history remains available. Manual receipt IDs moved into reachable details;
  proposal copy requires product confirmation before payment.
- Diagnostics remain accessible through Profile and Details; failure help remains
  visible. Stock-only undo and unverified bank settlement remain explicit. No
  server monetary, stock or payment logic changed in this task.

## Test evidence

| Check | Result | Provenance |
|---|---|---|
| Independent state/wake composition | 6 passed, 218.9202ms | Chengetai fresh execution |
| Counter-session, wake and native speech bridge tests | 17 passed, 250.1736ms | Chengetai fresh execution |
| Baseline | 21 passed, 13.864s | Root execution, relayed to QA |
| Frozen final frontend suite | 140 passed, 706.7265ms | Root execution after final copy changes |
| Scoped diff check | Passed | Chengetai execution; line-ending notice only |

The independent cases protect pending keys, explicit pause, false wake matches,
unchanged receipt amounts and same/next-utterance content. They are not rendered
layout or microphone tests. Product files were reviewed without changes by QA.
QA changed only `tests/counter_polish_client.mjs`, its README instructions, this
report and own brain files. No backend request, live sale, reset, provider call or
privileged command was performed by QA.

## Final artifact

Root verified the final APK build, ZIP, twelve embedded files, explicit port 8001,
build label `COUNTER-POLISH-001`, v1/v2 signatures and downloaded byte/hash equality.
The final bundle is `shop-D1AJuhDJ.js`; API PID 37764 remained unchanged.

- APK size: **7,208,351 bytes**.
- SHA-256: `9da49d7cfc6f10c36657b6f68d9d9273fd4a5f9a6715b10a48f88e1c2103a7d1`.

These host observations are attributed to root. The remaining check is on the
phone: compare the compact receipt, say Apo/Apple for consecutive sales, verify
same-utterance continuation, and confirm Pause/Resume and typed entry behave as
intended. No new physical layout/ASR acceptance is inferred from packaging.
