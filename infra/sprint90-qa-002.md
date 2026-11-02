# Connected demo improvement QA — 2026-11-01

Task: SPRINT90-QA-002. Chengetai. Scope: tests, infrastructure, CI and own brain;
application source reviewed without changes.

## Delivered

- `infra/start-demo.ps1`: repeatable single-worker SQLite API launcher on 8001.
  Reuse requires the expected database identity, listening PID, uvicorn entrypoint
  and readiness. Unknown listeners, including 8000, are preserved. Query failures
  fail closed. No firewall rules or credentials are changed or printed.
- `infra/serve_apk.py`: optional separate 8081 server for exactly one built APK
  and its public hash metadata. No directory listing or repository-file access.
- `infra/phone-demo-checklist.md`: launch/download/connect instructions and an
  explicit pending physical acceptance table.
- Three additional independent SQLite HTTP acceptance cases covering strict
  manual cash/change, restart/retry after catalogue price change, legacy null
  compatibility, bank validation, scoped trace filtering/redaction, bounded
  queries and absent/corrupt trace storage. Independent suite now has ten tests.
- Three APK handler tests and three PowerShell launcher behavior tests without
  opening network listeners or starting services.

## Evidence from this sprint

| Check | Result | Provenance |
|---|---|---|
| Baseline including first two launcher cases | 13 passed; compilation passed, 3.664s | Chengetai execution |
| All three launcher behavior cases | 3 passed, 1.485s | Chengetai execution; mocked OS inventory |
| Launcher inventory cross-check regressions after host reuse defect | 7 passed, 5.286s | Chengetai fresh execution; IPv4/IPv6, unknown preservation, verified reuse and invalid queries |
| Numbered TCP-state/full-table launcher follow-up | 8 passed, 5.826s | Chengetai fresh execution; includes FIN_WAIT_1/FIN_WAIT_2, headers and IPv6 |
| Latest baseline after launcher cross-check repair | 18 passed; compilation passed, 10.343s | Chengetai fresh execution |
| APK-only handler cases | 3 passed | Chengetai execution; in-memory HTTP handler |
| PowerShell AST syntax parse | Passed | Chengetai execution |
| Focused manual/trace/voice frontend tests | 37 passed, 272.1741ms | Chengetai execution |
| Scoped `git diff --check` | Passed; line-ending notices only | Chengetai execution |
| Integrated backend plus ten independent acceptance tests | 190 passed; 16 existing SSL warnings | Root host execution, relayed to QA |
| Latest normal baseline | 14 passed | Root execution, relayed to QA |
| Full frontend suite and build | 122 passed; build 80 modules | Runako execution, relayed to QA |
| Final investigation/manual receipt tests | 10 passed, 256.0471ms | Chengetai fresh execution |
| Final trace tests including oversized envelopes | 8 passed, 0.259s | Chengetai fresh execution |
| Final receipt-history and known-native-connection migration checks | 14 passed, 218.6149ms | Chengetai fresh execution |
| Final frontend/history build | 125 passed; build 82 modules, explicit demo port 8001 | Runako execution, relayed to QA |
| Final host launcher verified reuse and APK-only download | Passed; existing API PID 30460 unchanged | Root host execution after inventory fixes, relayed to QA |
| Live synthetic manual cash/change and exact retry | 150 total, 500 received, 350 change; original receipt returned | Root LAN execution, relayed to QA |
| Live shop investigations and unknown-product rejection | Scoped events returned; unknown product rejected | Root LAN execution, relayed to QA |
| Final Gradle APK, v1/v2 signature, ZIP and embedded bundle | Passed; 12 embedded files match final build | Root host execution, relayed to QA |
| Final downloaded APK byte/hash equality | Passed; 7,178,827 bytes, final hash below | Root host execution, relayed to QA |

The launcher tests found and corrected PowerShell 5.1 single-item array unrolling:
one listener must not appear to be a free port. They prove no-write CheckOnly,
fail-closed inventory denial and preservation of an unknown occupied port.
Restricted real CIM inventory is unavailable here; an earlier suppressed query
was corrected to fail explicitly. Mocked checks do not replace host runtime tests.

Root subsequently executed those host checks successfully, including the verified
SQLite runtime and separate APK download service. The live synthetic manual sale
returned receipt `ee596e4b-9248-4a89-b418-a0da7b99ba3b` for one Coke: 150 cents
total, 500 received, 350 change. Exact retry returned the original sale. Scoped
investigations returned saved events and the unknown-product command was rejected.
Gradle succeeded and the downloaded APK matched the local candidate SHA-256
`694c7053d30c390353860d90826934df22f343dbc6e9a2af7caa1cc655a40818`.
The LAN URL is `http://192.168.10.213:8081/street-ceo.apk`. Root requested a
subsequent sales-history display update, so this is candidate packaging evidence;
the final rebuilt artifact hash must supersede it after that update.

The final history/migration source subsequently passed targeted QA. History uses
saved quantities and stock snapshots, labels current catalogue names explicitly,
falls back to complete product references, and never infers historical prices or
uses fixture catalogue names. Legacy cash without a saved received amount shows
both received and change as Not supplied. The migration changes only the known
native Android demo connection from the retired LAN 8000 endpoint to the explicitly
bundled matching-shop 8001 endpoint. Browser/custom shops and extra saved settings
are preserved; repeat execution is idempotent and write failure displays guidance.
Final packaging after this source update is root's remaining artifact gate.

A subsequent root host reuse check found CIM could return an empty listener table
despite the existing ready API. The launcher attempted a second process, whose
bind failed; the original PID 30460 remained untouched. QA repaired inventory to
union CIM with independently parsed `netstat.exe -ano -p tcp` rows. IPv4/IPv6
endpoints, states, ports and PIDs are validated; failed, empty or malformed
netstat output cannot authorize startup. Seven mocked PowerShell cases now pass,
including this exact empty-CIM/occupied-netstat scenario and verified reuse without
starting another process. The complete fresh baseline passes 18 tests. Root's host
reuse rerun must confirm the repair; no host success is inferred from mocks.
Root's first rerun correctly failed closed because the parser's state expression
did not allow digits in otherwise-valid FIN_WAIT_1/FIN_WAIT_2 rows. QA corrected
the expression and added a complete mixed-table regression. All eight launcher
tests now pass; the host rerun remains the authority for actual process reuse.
Safe follow-up diagnostics then identified a legitimate unrelated CLOSED/PID 4
row. CLOSED was added to the validated TCP states; only LISTENING rows are counted
as listeners. Mixed-table and verified-reuse tests cover CLOSED rows, including a
CLOSED row on the download port that must remain classified as not listening.
All eight launcher tests passed again after this narrow correction (5.934s).

## Final packaged candidate

Root's final host rerun passed after the inventory corrections: the launcher
reused the existing SQLite API PID **30460** without replacing it; the database
remained `demo-mvp.sqlite3`. Gradle, v1/v2 signature verification, ZIP integrity
and all twelve embedded-file comparisons passed. The final shop bundle is
`shop-l6068vGv.js`.

The final APK is **7,178,827 bytes**, SHA-256
`5ff29235d0e5a81edcddb28c4215b513767a7ed6984fbd7c50d4ea585182e91a`.
Root downloaded the LAN-served APK and verified matching bytes/hash at
`http://192.168.10.213:8081/street-ceo.apk`. This supersedes the earlier candidate
hash in this report. All host observations are explicitly attributed to root;
Chengetai's own launcher evidence consists of eight isolated PowerShell cases.
Physical-phone installation, rendering and ASR/TTS/repeated-sale acceptance remain
pending. Final baseline rerun is being executed by root; the previous complete
baseline had eighteen passes before the eighth launcher test was added.

## Reviewed application behavior

Manual requests use server catalogue prices and integer cash amounts, reject
shortfall before stock mutation, preserve legacy omitted/null fingerprints and
return historical receipts before recalculating against changed prices. The trace
reader filters by shop in bound SQL before limiting, opens the trace database
read-only and sanitizes returned payloads again.

Frontend manual recovery retains original configuration, payload and key; mutation
uncertainty locks editing and navigation. Receipt success is separate from refresh
failure. The new shop request UI distinguishes loading, empty and error states and
validates shop/event metadata before rendering saved payloads as escaped text.

QA identified two voice cross-flow defects: parent manual/navigation controls
could unlock after an uncertain voice commit, and a subsequent 4xx during recovery
could clear the prior uncertainty. Runako fixed both: the parent lock derives from
busy/listening/recording/tender/uncertainty; recovery retains uncertainty until a
verified receipt/reversal. Spoken warnings use the unresolved state. Targeted
source re-review found these changes correct. Frontend tests simulate data and
bridge behavior; they do not establish rendered touch interaction or Android ASR.

Root repaired oversized trace envelopes to retain bounded sanitized shop,
correlation, operation, phase, provider/model, status and error metadata. Scoped
investigation no longer loses these events. The viewer validates and explicitly
labels their saved prefixes as partial, rather than presenting complete content.
Final QA read-only review confirmed `provider_called: null` renders as Unknown;
only actual booleans render Yes/No. There are no fixture events or provider-success
fallbacks in the live viewer. Saved request/response/prefix text is escaped React
content. The fresh eight trace tests include oversized Unicode and metadata
redaction/bounds, and ten final viewer/manual tests passed after these fixes.

## Acceptance limits

No physical phone or browser UI observation is available to this agent. No claim
is made about microphone grant, actual speech recognition/playback, visual layout,
phone download/install or repeated real-device sale cycles. Root owns host
regression, runtime activation, APK build/asset/hash evidence and LAN checks.
Offline sync, full accounting remediation and production authentication/HTTPS
remain outside this connected-demo improvement sprint.

## Root final integration evidence (appended after QA handoff)
Fresh python tests/run_checks.py: 19 tests passed in 10.101s, Quality checks passed. Final signed APK/download parity and unchanged API30460 verified as above. Root append requested in QA's final handoff; no product changes accompanied this evidence update.
