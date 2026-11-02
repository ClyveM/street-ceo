# Phone recovery QA — 2026-11-01

Task: PHONE-RECOVERY-QA-001. Chengetai. Product code reviewed read-only; QA
changes are confined to tests, infrastructure and own brain.

## Findings and fixes reviewed

- A valid HTTP 200 `needs_tender` response contains the review ID, question,
  amount due, allowed tenders and missing fields. It is not a sale receipt.
  Backend returns before `create_sale` when tender/cash received is missing.
- The previous client classified all `/commit` transport failures as possible
  sales, even requests that lacked payment. The reviewed fix distinguishes these
  unpaid questions from bank, complete cash and undo requests. Unpaid question
  failures retain the reviewed basket/key and allow safe retry/cancellation.
- Invalid supplied payment types/amounts are rejected before transport. Bank and
  complete cash, including zero received for a zero-price sale, retain uncertain
  mutation handling on transport/5xx errors.
- Prior paid uncertainty remains sticky. Recovery retains the original paid
  payload/key; insufficient-cash fallback cannot downgrade that request to an
  unpaid one. A recovered question cannot clear an earlier unknown sale outcome.
  Only a verified receipt/reversal clears that uncertainty.
- The connection indicator now checks readiness and the exact configured shop
  through read-only requests from the device. Network-interface online status
  alone cannot produce a verified connection. Build label, server address, check
  time and manual recheck appear in the source UI.
- The modal Close control now has fixed flex shrink behavior and no wrapping.
  This is a source constraint review, not a physical rendered-layout pass.

## Evidence

| Check | Result | Provenance |
|---|---|---|
| Independent client/probe contract tests | 9 passed, 247.4364ms | Chengetai fresh execution; simulated transport only |
| Baseline and compilation | 20 passed, 11.561s | Chengetai fresh execution |
| API tender-chain and independent SQLite suites | 22 passed, 4.31s | Root host execution, relayed to QA |
| Frontend suite and explicit 8001 build | 130 passed; 84 modules, `shop-Bf6DEXwf.js` | Runako execution, relayed to QA |
| Launcher inventory regression | 9 passed, 6.531s | Chengetai fresh mocked PowerShell execution |
| Health-first trusted-state reuse regression | 10 launcher cases passed, 7.476s; focused trust/mismatch/unknown-process case passed, 1.537s | Chengetai execution; no real listeners |
| Final no-store/worker/probe/payment tests | 24 passed, 291.3191ms | Chengetai fresh execution |
| Independent client/probe after unique-query changes | 9 passed, 210.3808ms | Chengetai fresh execution |
| Final frontend suite and build | 132 passed; 84 modules, `shop-Ct0WV7-I.js` | Runako execution, relayed to QA |

The new independent SQLite HTTP case proves unanswered tender and cash-amount
questions return 200, never a receipt ID/stock snapshot, leave stock/history and
commit bindings unchanged, and remain retryable with the original key after
reopen. Persisted completed-200 events remain questions rather than sale proof.
All data/files in this test are isolated synthetic fixtures, not live phone sales.

The independent JavaScript tests prove the valid question shape, identical retry
payload/key after a lost question, paid versus unpaid transport classification,
no transport for malformed payment, conservative wording after prior paid failure,
and actual readiness/shop checks rather than navigator status. React recovery
guards and Close styling were reviewed in source; the tests do not render Android.

Root also found a CLOSED download-port row returned by a CIM query requesting
Listen. The launcher now explicitly checks each CIM row's state as well as port.
Its regression combines CLOSED/PID 25844 with actual LISTENING/PID 16136 and
proves only the latter is reused after command/path/hash validation, without
starting or stopping processes. Root owns the final real-host verification.

Root later observed both TCP inventories could omit a healthy API. The launcher
now probes identity/readiness before concluding the port is free. Empty inventory
can permit reuse only when the live SQLite database identity and PID, recorded
trusted launcher state, and exact uvicorn process command all agree. Nonempty
inventory must still match the live PID. Mismatched state or an unknown process
is refused, without starting or stopping a service. Mocked regressions prove this
specific 30460 reuse path and its negative cases; root's host rerun is required.

The final freshness review also found the old service worker could replay cached
API GET results. Runako's root-authorized fix bypasses all API/shop/readiness/
health, cross-origin and no-store requests in worker v4, with no cached/HTML
fallback. Probes additionally use unique query keys and `cache: no-store`, so an
older worker cannot match a previous exact cached probe; an HTML shell fallback
fails JSON verification. Normal shell navigation remains separate. Twenty-four
focused worker/probe/payment tests passed, and the final targeted source review
found no remaining concrete blocker in these fixes.

## What remains unproven

Root inspected an unbound review and no corresponding sale; four earlier commit
events were HTTP 200 questions. No matching screenshot-time request was observed
in the inspected trace window. Phone local time was reconciled against UTC under
the assumption the phone clock was correct. This does not establish that mobile
data, an older APK or another specific connectivity issue caused the screenshot.
The user's network/latest-build answer and a phone retest remain necessary.

No live sales, resets, provider calls or privileged commands were run by this QA
task. Final rebuilt APK hash/download verification belongs to root. Physical phone
connection, Close rendering, audible question, Retry/Cancel, actual payment and
repeat-sale behavior must be observed before claiming phone acceptance.
