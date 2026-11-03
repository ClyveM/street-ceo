# Inzwi — Handoffs

## 2026-10-30 — W3-VOICE-INPUT-001B permission recovery

### Assignment

Review the urgent Android voice-capture failure and make only voice-side changes
needed so microphone denial is clear, recoverable, and does not block typed Meta AI
commands. Do not modify Android native files.

### Files changed

- `apps/web/src/VoiceCapture.tsx` — distinguishes microphone permission/security
  denial from general voice failure, gives Android Settings recovery guidance,
  preserves the typed command, focuses the text input, and adds a direct
  “Continue with typed command” action.
- `agents/inzwi/brain/current-state.md` — recorded verified status and the device
  test limitation.

### Evidence

- `npm run build` from `apps/web/` — passed.
- `python -m unittest discover services/voice -p 'test_*.py' -v` — 7 passed.
- No Android native files were changed.

### User-visible result

When Android/browser microphone permission is denied, the card now says the
microphone is unavailable while typed commands still work. Android users receive
the Settings → Apps → Street CEO → Permissions → Microphone → Allow path, and can
continue directly to the typed Meta AI field without dismissing the whole feature.

### Outstanding

The APK must still be tested on a physical Android device after installing this
web build. Native permission declaration/runtime changes remain outside this task.

## 2026-10-30 — W2-INZWI-001 completed

### Assignment

Implement the provider-neutral foreground Apo/Napo state machine in
`services/voice/`, with push-to-talk/text fallbacks, API-contract routing,
basket preservation, and safe retries.

### Files changed

- `services/voice/__init__.py` — public voice boundary exports.
- `services/voice/state_machine.py` — session states, input mappings, protocols,
  catalog resolution, quote/payment/validation flow, failure preservation, and
  idempotent retry behavior.
- `services/voice/test_state_machine.py` — seven dependency-light contract tests.

### Tests run

- `python -m unittest discover services/voice -p 'test_*.py' -v` — 7 passed.
- `$env:PYTHONPATH='.'; python tests/run_checks.py` — 6 passed, compilation
  passed, quality checks passed.

### Integration dependencies and outstanding issues

- A consuming adapter must implement `Interpreter`, `CatalogResolver`, and
  `SaleGateway`; the latter must call `POST /shops/{shop_id}/sales` with the
  documented scope and `Idempotency-Key` headers.
- Runako supplies microphone/touch presentation and confirmation UI; Inzwi did
  not modify it. Hwaro/Verengai supply the real API gateway behavior.
- Ungwaru may implement an interpreter adapter later; its output must be mapped
  to `CommandIntent` and must not receive permission to post directly.
- No provider credentials, microphone code, backend, finance, inventory, or
  offline code was added.
- Cash amount is optional: when supplied, an amount below the quote fails safe;
  no amount is accepted as operational tender recording per MVP policy.

## 2026-10-31 — W6-VOICE-QUICK-SALE-001 / W6-VOICE-TENDER-CONVERSATION-001 — completed voice boundary

### Changes

- `services/voice/state_machine.py` — added configurable `SaleMode.REVIEW` and
  `SaleMode.QUICK`. Quick mode accepts multiple strictly resolved catalogue
  lines and treats a closing `Apo` as the explicit confirmation signal. It
  auto-commits only when a configured default tender exists; otherwise it asks
  the spoken question `Your total is {amount}. Cash or Bank?`.
- Tender conversation now accepts exact `cash`, `cash <amount>`, and `bank`.
  Cash overpayment produces bounded receipt `cash_received` and `change_minor`;
  bank produces no cash change. Missing, unclear, or insufficient tender keeps
  the session in `PAYMENT`, speaks a recovery question, preserves the basket,
  and never posts.
- Successful commits expose a bounded receipt and retain the existing stable
  idempotency key across retry. `undo_last_sale()` calls an explicit
  `undo_sale` gateway when available; otherwise it fails closed with a clear
  reversal-service blocker. No reversal endpoint was invented or added.
- `services/voice/test_state_machine.py` — added tests for Apo quick commit,
  missing tender, ambiguity, provider retry/idempotency, receipt/change,
  bank, unclear tender recovery, and undo safety.

### Tests

- `$env:PYTHONPATH="$PWD\\services\\voice;$PWD"; python -m pytest services/voice -q`
  from the repository root — **18 passed**.

### Integration handoff

Hwaro/Verengai must expose the configured Quick Sale mode and connect the
existing `POST /voice/commit` sale boundary to a real reversal/undo endpoint
before undo can be offered in the UI. The current voice implementation does
not bypass the backend, stock checks, ledger, review/audit, or idempotency.


## 2026-10-31 — W6-DEMO-VOICE-001 — completed voice-side safety fixes
Assignment: verify Quick Sale Apo/items/Apo, tender, cash/change and undo; fix highest
priority failure. Read role, six brain files, shared voice/product/API docs and board.
Scope: services/voice/ and own brain only. Existing unrelated changes preserved.

Files changed this assignment:
- services/voice/state_machine.py: needs_tender remains PAYMENT, missing sale ID
  cannot report success; cash amount is required and forwarded as keyword
  amount_received_cents; bank mismatched amount rejected; backend change/amount
  respected; new cycles clear receipts/cash; boolean quantities rejected.
- Undo requires status=reversed; missing acknowledgement/transport failure retains
  original sale and permits retry with the same reversal key.
- services/voice/test_state_machine.py: regression tests for amount forwarding,
  tender questions, missing IDs, authoritative change, cycle reset and undo retry.
- Own current-state.md, decisions.md, tasks.md and this handoff updated.

Fresh evidence (PYTHONPATH includes services/voice and repo root):
- python -m pytest services/voice -q: 24 passed.
- python -m pytest services/api/test_voice_boundary.py -q: 12 passed; 8 existing
  SSL/truststore deprecation warnings during audio provider construction.
- git diff --check -- services/voice/state_machine.py services/voice/test_state_machine.py:
  passed, no whitespace errors.

Handoff and limitations:
- Closing Apo confirms basket; configured bank posts immediately, cash asks amount.
- Cash gateways must now accept keyword amount_received_cents. No production
  VoiceSession consumer found in inspected services; browser/API flow is separate.
- Backend commit/undo routes exist and focused tests pass, superseding saved missing
  endpoint warning. Consumer still must bind review_id, shop scope/idempotency
  headers and undo actor/reason/confirmed fields. No backend/UI code changed here.
- Amount grammar is integer minor units (cash 500 means 500 cents); natural spoken
  decimal/number-word money unverified. Multi-item tests use sequential captures
  and fixture interpreters, not real provider/audio parsing.
- No physical Android/noisy-market/TTS/live provider/end-to-end UI verification.
  Chengetai release review remains required.
Next: Runako/Hwaro reconcile demo adapters; verify microphone and spoken flow on device.

## 2026-10-31 — W6-DEMO-VOICE-001 follow-up — punctuated spoken tokens

### Assignment

Verify the current Apo Quick Sale close and spoken Cash/Bank amount behavior;
fix one proven remaining voice issue, run focused tests, and hand off evidence.

### Files changed

- `services/voice/state_machine.py` — trims bounded terminal punctuation from
  Apo/Napo words and accepts comma-separated/terminal-punctuated tender amounts.
- `services/voice/test_state_machine.py` — regression tests for `Apo.` close and
  `Cash, 500.` parsing.
- Inzwi brain files — current state, decision, lesson, task, and this handoff.

### Evidence

- Before fix reproducer: Quick mode `end("Apo.")` returned `FAILURE` with
  `Finish the item with Apo.` despite a valid basket.
- `PYTHONPATH="$PWD\\services\\voice;$PWD"; python -m pytest services/voice -q`:
  **25 passed**.
- `python -m unittest discover services/voice -p 'test_*.py' -v`:
  **22 passed**.
- `git diff --check -- services/voice/state_machine.py services/voice/test_state_machine.py`:
  clean.

### Outstanding

No real microphone, noisy-market, TTS, or live provider validation was performed.
Natural number-word money remains outside this bounded parser. Backend/UI
integration and Chengetai release review remain required.
## Handoff — W6-VOICE-COCA-COLA-001 — 2026-11-01

Reproduced the flow and fixed both verified layers: `apps/web/src/wakePhrase.ts`
now preserves internal hyphens, and `services/api/voice_boundary.py` recognizes
size-stripped catalogue-name aliases. Before the fix, the sanitized direct
backend replay returned HTTP 200 `rejected` with
`invalid_or_unsafe_provider_response`; no provider call or sale commit occurred.

Tests: `npm run test:frontend` 104 passed; `python -m pytest
services/api/test_voice_boundary.py -q` 13 passed; `npm run build` passed;
Capacitor copy/sync passed; Gradle `assembleDebug` passed. New APK:
`apps/android/android/app/build/outputs/apk/debug/app-debug.apk`, 7,172,104
bytes, SHA-256
`14A30AC5521203426919031C6071488C0AD14729B96DF1D94036C5E5A6591B50`.

No physical Android device or original audio was available. Device microphone,
live LAN HTTP, and production signer checks remain unverified.

## 2026-11-01 — DEMO-VOICE-TRACE-001 completed
- Assignment: integrate durable sanitized tracing around actual voice intent/chat and ASR provider calls. Read AGENTS.md, role, six brain files, shared voice/API docs and master board. Confirmed scope services/voice and own brain; no other owners edited.
- Files changed: services/voice/meta_llama.py wraps HTTP send in services.ai.tracing.traced_call with voice_intent operation, model/messages and secret-value redaction. services/voice/meta_voice.py wraps ASR send with voice_transcription operation; traces size/media metadata and provider JSON, never raw audio. services/voice/test_provider_tracing.py adds isolated SQLite trace tests for correlated request/response, credential redaction, HTTP failure preservation, binary omission and fail-closed unavailable trace storage. services/voice/test_state_machine.py import supports normal root pytest and direct unittest discovery.
- Tests: python -m pytest services/voice -q -p no:cacheprovider --basetemp .pytest-voice-trace — 29 passed in 0.63s. python -m compileall -q services/voice — PASS. git diff --check -- services/voice — PASS (line-ending warnings only).
- Dependencies: services.ai.tracing (Ungwaru) must ship; API supplies trace_context correlation. Trace DB configured by STREET_CEO_TRACE_DATABASE, default data/muse-traces.sqlite3. Failure to persist started event prevents provider invocation; failed HTTP call re-raises original error after recording sanitized status/body.
- Limits: mocked provider HTTP only; no live provider or phone verification. ASR conversion still occurs before traced HTTP call, and conversion errors are API-level failures rather than provider events. No raw audio stored. No live service restart/mutations performed.
- Next: parent integrate full service tests, APK packaging and real-device acceptance. Verify API correlation joins provider and sale outcome events; no UI/transaction claim inferred from focused provider wrapper tests.

## 2026-11-03 - VOICE-LEARN-001
- Scoped web voice changes: HandsFreeVoice.tsx offers five reviewed samples for Apo and Napo. Partial drafts are in memory and cancellation does not persist them. wakePhrase.ts reads optional Apo aliases alongside previous device preferences and validates collisions. Saved wake aliases begin a phrase and preserve matching ordinary words within the product list.
- Full one-utterance framing and reviewed Napo recognition such as nato verified in apps/web/tests/shortVoiceTrain.test.mjs. 173 frontend tests passed and tsc -b passed. Scoped diff check clean.
- Product correction learning deferred because the existing proposal lines can merge or reorder heard segments and do not expose a reliable heard-to-product association. Unknown endings still require a known/reviewed finish phrase. No backend, live service, APK or Git mutation. Parent owns integration and physical device acceptance.
