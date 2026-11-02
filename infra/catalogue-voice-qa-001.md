# Catalogue voice QA — 2026-11-01

Task: CATALOGUE-VOICE-QA-001. Chengetai. Targeted software/source gate passes;
physical speech recognition and final APK/server activation remain separate.

## Scope and evidence

- Restored current AGENTS, role, six brain files, task board and connected-demo
  acceptance. Product code was reviewed without editing it.
- Existing independent SQLite test builders explicitly disable the resolver with
  `voice_catalogue_resolver=None`. New cases inject the real grounding validator
  around a synthetic traced provider. These tests cannot invoke Meta.
- Root reported the broad service plus independent SQLite suite **215 passed**,
  with 16 existing SSL warnings in 20.18s. Seven new independent HTTP cases were
  present before that run; the independent SQLite module now has eighteen cases.
- Fresh independent JavaScript catalogue contract checks: **6 passed**,
  190.6297ms. Fresh quick-sale/wake/native-bridge checks: **36 passed**,
  270.7955ms. Compilation and scoped diff checks passed.
- Runako reported **136 frontend tests passed**. Packaging and actual phone
  observations are not established by those tests.

Root separately exercised the real configured provider against the actual demo
catalogue without posting a sale: noisy bread and Coke produced proposals,
unquantified Coca-Cola asked for quantity, and a mixed Coke/unknown product
returned clarification with no lines. Root observed provider-called metadata and
persisted started/completed traces. This real-provider evidence is attributed to
root, not to QA's synthetic tests.

## Contract issue found and repaired

Initial API proposal responses omitted `intent`, while the frontend required a
grounded `record_sale` intent with `needs_confirmation: true`. Real proposals
would therefore fail parsing. QA reported this to Hwaro and Runako. Hwaro added
the grounded intent to both provider proposals and contextual exact proposals;
the frontend retained its fail-closed parser. The independent HTTP and client
cases now assert the actual matching response shape.

## Acceptance covered

- Every enumerated item slot must be returned exactly once by the resolver;
  omitted slots, invented quantities/IDs and extra price fields yield no lines.
- Unknown second items never become partial first-item sales. IDs, quantities,
  duplicate IDs and stock are checked against server catalogue truth.
- Provider proposals are noncommittable until explicit Yes. The client requires
  local approval, and the API requires strict boolean `match_confirmed: true`.
  Unconfirmed paid attempts fail without stock/history changes.
- Reviewed proposals survive SQLite reopen. Exact paid retries return the same
  receipt; changed approval/payload or a second key conflicts. Server prices,
  not provider prices, determine the receipt total and change.
- A missing single-item quantity remains unknown until supplied. The answer
  carries `clarification_of`, survives reopen/replay and produces another explicit
  match confirmation. Invalid contexts and changed same-key replies conflict.
- No, Cancel and ordinary words cannot count as Yes. Native reply mode accepts
  unframed confirmation/quantity answers. A corrected exact basket after No is
  also spoken back for confirmation before payment.
- Original noisy words are retained for interpretation. Only a terminal `nabo`
  closes framing; an interior occurrence does not discard remaining words.
- Match/clarification/tender phases hold the parent interaction lock. Existing
  paid uncertainty and original recovery keys remain guarded.
- Traces distinguish exact/local clarification from actual provider work. The
  synthetic provider is labelled `qa-synthetic-catalogue`, not a real Meta call.

## Remaining acceptance

The actual provider probes and software suites do not prove phone ASR accuracy,
timing, TTS playback, microphone permissions or repeated real voice-sale cycles.
Terminal framing still depends on the recognized utterance. Root owns final
APK build/signature/assets/hash verification and activating the patched backend;
a physical tester must then exercise the spoken proposal → Yes/No → quantity →
payment → saved receipt flow. No live sale, reset or uncontrolled provider call
was performed by this QA task.
