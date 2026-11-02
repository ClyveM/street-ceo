# Connected APK demo acceptance — 2026-11-01

## Owner-approved additions — 2026-11-02

Basic mobile reports: monthly sales summary and sales by product for inclusive
selected dates or last1/20/90 shop-local calendar days. Preserve historical
evidence: quantities remain available, but old mixed-sale product amounts without
saved line prices are unknown, not recalculated from current catalogue prices.

Spoken “end my day” from idle Sell asks counted cash, asks opening cash if missing,
compares against server-calculated recorded cash and shows shortage/overage or
balanced. Confirm before saving; preserve uncertainty/retry and frozen snapshots.
Bank is not counted/verified in this cash-only process. Unknown opening is not zero.
Month-end review includes an optional stock-count step with Skip, not a forced count.
See `docs/reports-and-close-acceptance.md` and the latest verification for delivery.

Owner-approved scope: catalogue, manual and hands-free Apo sales, stock, sales
history, SQLite durability, and persisted Muse request/response investigation.
Offline sync, invoices, social, forecasting, and full accounting remediation are
outside this demo acceptance scope.

## Required experience

- Open the APK and grant Android microphone permission on first use. With Sell
  in the foreground, listening arms without a per-sale enable button.
- Say Apo, list catalogue products and quantities, and finish with Napo.
- Unknown or ambiguous products receive a spoken explanation; no partial sale.
- Ask for missing tender/cash received and accept a spoken reply without a tap.
- Compute totals and change from server catalogue prices and cash received.
  Insufficient cash cannot post a sale. Bank is recorded tender, not settlement.
- Speak success only after a durable receipt; update stock and history.
- Resume wake listening after spoken output; do not interpret the app's own TTS
  as a customer command. Pause in background and recover on foreground return.
- Manual sale remains available using the same stock/history truth.

## Persistence and investigation

- Reopen the SQLite-backed API and preserve catalogue, sale receipts, stock,
  historical sale costs, voice reviews, commit bindings and idempotency records.
- Exact retry returns the same receipt; a changed payload conflicts. Failed writes
  leave no partial stock/sale changes and never produce a success receipt.
- Initial seeding never overwrites existing demo state. No silent memory fallback.
- Persist request/response traces with correlation IDs, timestamps, operation,
  provider/model, latency and outcomes; link voice review to resulting sale.
- Trace bounded sanitized payloads, including failures; exclude credentials,
  authorization headers and raw audio. Keep operational traces out of agent brains
  and source control. Distinguish deterministic parsing from actual Muse calls.

## Release evidence

Backend real-file restart/retry/rollback tests, frontend tests/build, APK build
and embedded bundle verification, and physical-device Apo/tender/change/repeat
cycle evidence are required. Package success alone is not phone acceptance.
Record exact artifact hash and unresolved limitations in the handoff.
