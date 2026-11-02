# Connected APK demo runbook

## Backend

Preferred launcher after its host validation:

```powershell
.\infra\start-demo.ps1 -LanAddress 192.168.10.213 -ServeApk
```

It preserves unknown listeners, verifies the expected SQLite identity before
reuse, and optionally serves only the APK at
`http://192.168.10.213:8081/street-ceo.apk`. See the latest verification report for
launcher integration status. It does not change firewall rules.

From the repository root, use one worker and explicit local storage:

```powershell
$env:STREET_CEO_STORE = 'sqlite'
$env:STREET_CEO_SQLITE_PATH = 'data/demo-mvp.sqlite3'
$env:STREET_CEO_TRACE_DATABASE = 'data/muse-traces.sqlite3'
$env:STREET_CEO_VOICE_ENABLED = '1'
$env:STREET_CEO_SEED_DEMO = '1'
python -m uvicorn services.api.app:app --host 0.0.0.0 --port 8001
```

Keep the PC running and the phone on the same reachable network. The current
verified demo APK uses `http://192.168.10.213:8001`; this address must
match the PC. Port 8000 was occupied by an older runtime, which was preserved.
The new APK migrates only the known old demo address on port 8000 with the standard
demo shop ID to port 8001. A custom saved connection remains unchanged and may need
a one-time Shop Connection update; saved settings take precedence over the default.
This is a local debug demo, not a public deployment. Do not expose
the API to the public internet. Meta credentials stay on the backend.

## Phone rehearsal

1. Install the newly verified debug APK and grant its microphone permission.
2. Open Sell. The Android demo should arm foreground listening automatically.
3. Say: **Apo, one Coke and two sugar, Napo.**
4. Answer the payment question: **Cash ten dollars.** If the app first asks only
   cash or bank, saying **Cash** should lead to an amount question; then say **ten**.
5. With the default seeded prices, expect total **6.30**, change **3.70**,
   Coke stock reduced by one and sugar by two. Confirm the receipt and history.
6. Say: **Apo, one unicorn, Napo.** Expect a spoken not-found/clarification response
   and no new sale or stock change.
7. Make a second valid sale without pressing an enable/confirm/payment button.
8. Background and reopen the app; check that foreground listening recovers.
9. Restart the backend normally and verify the same receipts and stock remain.
10. Expand a sale in Sales history to inspect its saved quantities, stock snapshot,
    cash received and change. Product names are current catalogue labels.
11. In Profile, open Recent requests and expand a saved input/response. Unknown
    provider status and truncated data are labelled explicitly.

Manual sales also accept cash received and show a change preview; the server
receipt confirms the actual total/change. An uncertain sale freezes its original
request for recovery. Legacy receipts without recorded cash received remain unknown.

These are acceptance instructions, not a claim that a physical phone has passed.
Android speech recognition availability and pronunciation must be tested on the
actual phone. Listening applies while Sell is in the foreground.

## Investigation

The running demo shop state is saved in `data/demo-mvp.sqlite3`. Correlated sanitized API/provider
request and response events are saved separately in `data/muse-traces.sqlite3`.
Keep both files local and outside source control. Trace entries distinguish
started, prepared, completed and failed operations; an incomplete operation is
not proof of a sale. Sales history and the durable receipt establish the outcome.

To inspect recent sanitized events locally, from the repository root:

```powershell
python -c "import json; from services.ai.tracing import SQLiteTraceStore; print(json.dumps(SQLiteTraceStore().read(limit=20), indent=2))"
```

Use the response `X-Correlation-ID` to filter a particular investigation with
`SQLiteTraceStore().read(correlation_id='the-response-id')`. Provider-level
`trace_id` groups the request and response for each model call. Deterministic
catalogue parsing is not a Muse model invocation.

Do not reset or delete databases as part of routine startup. Preserve the original
idempotency key when recovering an uncertain sale; do not submit a new sale until
the original receipt has been checked.
