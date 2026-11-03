# Inzwi — Current State

Updated 2026-10-30 after W3-VOICE-INPUT-001B.

## Status

W2-INZWI-001 and the W3 voice adapter boundary are implemented and verified. The
voice UI now fails safe when Android/browser microphone permission is denied and
keeps typed Meta AI commands available.

## Work in progress

- Provider-neutral session state machine and focused tests are complete.
- Android permission-denial recovery is implemented in `apps/web/src/VoiceCapture.tsx`.

## Latest verified results

- `python -m unittest discover services/voice -p 'test_*.py' -v`: 7 passed on 2026-10-30.
- `npm run build` in `apps/web/`: passed on 2026-10-30.

## Known blockers

- Integration still requires a concrete catalog resolver and API gateway in the
  consuming layer; this task intentionally supplies protocols and no HTTP client.
- Tender remains operational recording only; no settlement verification is done.
- A real Android microphone test still requires granting/revoking the APK
  permission on a device; this change does not modify native Android permission
  declarations or runtime handlers.

## Next immediate action

Next: coordinate Runako/Hwaro integration against the protocols and documented
sale request shape; preserve the generated idempotency key across safe retries.


## 2026-10-31 — W6-DEMO-VOICE-001 checkpoint
Voice-side fixes complete: cash amount forwarding; tender responses never claim
posting; authoritative change; cycle receipt reset; acknowledged undo and safe retry.
Fresh voice tests 24 passed; backend voice tests 12 passed (8 SSL deprecation
warnings); whitespace check passed. See handoff for gateway signature change and
remaining adapter/device/real speech limitations. Awaiting next assignment.
Master board remains CTO-owned; saved labels do not imply active execution.

## 2026-10-31 — W6-DEMO-VOICE-001 follow-up
Verified and fixed the remaining spoken-boundary issue: normal ASR terminal
punctuation made Quick Sale `Apo.` fail to close, and `Cash, 500.` was rejected.
The voice boundary now trims terminal punctuation and accepts comma-separated
cash amounts without changing tender validation or sale contracts. Focused
pytest: 25 passed; unittest discovery: 22 passed; diff check clean.
## 2026-11-01 — W6-VOICE-COCA-COLA-001

Reproduced the sanitized flow `Apo 1 sugar 1 Coca-Cola Napo`. Before the fix,
web framing removed the internal hyphen and forwarded `Apo 1 sugar 1 coca cola
Napo`; direct backend input with the hyphen also failed because the catalogue
alias set lacked the size-stripped prefix for `Coca-Cola 300ml`. Fixed the web
token sanitizer and backend aliases. The flow now resolves Sugar 1kg x1 and
Coca-Cola 300ml x1 locally, without a Muse/Llama call or sale commit.

## 2026-11-01 — DEMO-VOICE-TRACE-001
Voice provider tracing complete in own scope. Chat and ASR HTTP calls now persist sanitized correlated request/response events through services.ai.tracing; ASR stores size/media metadata, not audio. Focused normal-root voice pytest 29 passed; compile and scoped diff PASS. No live provider/phone check. Handoff persisted; parent owns API correlation, runtime activation and APK acceptance.

## 2026-11-03 - VOICE-LEARN-001
- Scoped web voice changes: HandsFreeVoice.tsx offers five reviewed samples for Apo and Napo. Partial drafts are in memory and cancellation does not persist them. wakePhrase.ts reads optional Apo aliases alongside previous device preferences and validates collisions. Saved wake aliases begin a phrase and preserve matching ordinary words within the product list.
- Full one-utterance framing and reviewed Napo recognition such as nato verified in apps/web/tests/shortVoiceTrain.test.mjs. 173 frontend tests passed and tsc -b passed. Scoped diff check clean.
- Product correction learning deferred because the existing proposal lines can merge or reorder heard segments and do not expose a reliable heard-to-product association. Unknown endings still require a known/reviewed finish phrase. No backend, live service, APK or Git mutation. Parent owns integration and physical device acceptance.
