# Chengetai — Lessons

## 2026-10-30 — W1-CHENGETAI-001

- Contract tests must assert the semantics currently documented by the backend,
  not exact wording from the earlier conventions-only document. The check now
  accepts the verified `X-Shop-ID`, validation, idempotency, and audit wording.
- The local environment has Python but no `pytest` or FastAPI; CI must install
  the backend requirements before backend tests can provide full evidence.

## 2026-10-31 — W6-DEMO-QA-001

- Historical missing-dependency blocker is superseded: installed runtime executes 131 service tests with explicit PYTHONPATH. Default commands still expose import-path defects.
- Ignored local environment files are not proof of a tracked secret; baseline currently rejects their existence. Do not delete user runtime configuration to make a gate green.
- Validate APK embedded files against fresh web output; existence alone does not prove current UI packaging. This APK matched every dist file; physical-device readiness remains separate.

## 2026-11-01 — SPRINT90-QA-002
- PowerShell5.1 function output unrolls one-item arrays; PSCustomObject.Count can be null. Get-Listeners must return a protected array (unary comma), otherwise one occupied port can be misreported free. Real PowerShell subprocess mock regression caught and verified the fix.
- Get-NetTCPConnection -LocalPort with SilentlyContinue cannot distinguish absent listener from denied CIM inventory. Query full listening table with ErrorActionStop then filter port; failure must not authorize starting another service.
- Isolated BaseHTTPRequestHandler memory connections can prove fixed-file MIME/hash/HEAD and traversal rejection without binding restricted sockets; they do not prove real LAN reachability.

## 2026-11-01 — SPRINT90-QA-002 silent CIM inventory
Hostproved CIMcanreturnemptywithaliveAPI withoutqueryerror. Failclosedonexceptionsaloneinsufficient; crosscheckindependentnetstatrowsbeforeassumingportfree. Regressionmodels emptyCIM+occupiedIPv4/IPv6netstat and actualidentity-gatedreuse, no arbitraryStopProcess.

## 2026-11-01 — SPRINT90-QA-002 netstat state parser
State-tokenregexmustmatch validstateenumdigits (FIN_WAIT_1/2). Fullmixedtable regressions needed, notonly isolatedLISTENINGrows. Invalid/unrecognizedrows remainfailclosed.

## 2026-11-01 — CATALOGUE-VOICE-QA-001
Test actualresponseintentshape acrossAPI/UI, not handauthoredproposalfixturesalone. NewautomaticAI fallback means existingunknown-itemtests must explicitly injectresolverNone/fakes to avoidliveMeta. Allitemcoverage test realresolverboundarywithsyntheticprovider, not an unchecked fakeproposedlambda.

## 2026-11-02 — MUSE-OUTAGE-QA-001
A caller timeout is not provider cancellation. Keep the capacity token until actual future completion, discard late results, and test with controlled blocked providers rather than timing assumptions. Confirm each frontend endpoint budget separately: transcript30s vs question-only commit8s.


## 2026-11-02 — FAST-COUNTER-QA-001
When adding local short circuits, syntheticprovider schema/failure tests must explicitly disable local proposals; otherwise a passing local path silently skips the intended provider boundary. Keep separate HTTP tests for new fast-path mandatory confirmation, no mutation, durable replay and truthful provenance.


2026-11-02 launcher: post-shutdown CIM may transiently misreport Listen/PID0. Only discard a zero-owner row with independent validated same-port nonlistener corroboration; preserve nonzero/unknown owners and fail closed on ambiguity. Root retry restoration is observed; exact stale CIM capture remains unconfirmed.


## 2026-11-02 — QUANTITY-REPLY-QA-001
A final-answer latch must suppress duplicate dispatch without suppressing foreground/background updates. Async-handler completion must not rearm a hidden app. Readiness needs the same visibility guard as start/text, and must come from actualrecognizerready rather than permission/startpromise. Independent realbridge+turn composition reproduced and verified ownerfixes; phonecause remains separate.


## 2026-11-02 — REPORTS-CLOSE-QA-001
Read complete financialcalculator control flow before flagging preliminary values: later validatedcashoverride replaced legacycash result, and QA correctedpartialread. Test API/UI shapes using authoritative auditreason normalization, nullhistoricalSKU/unknownpayment andother-tender totals. New guardedendpoint is insufficient ifgenericmutation can bypass it; preserve exactoldreplay before rejecting newcashopenings/futureactuals. Source/tests/DOM do not establish physicalphone orbank/fullledger acceptance.


## 2026-11-02 — NAPO-RETRY-QA-001
A reply-mode directfinal path can bypass wake-frame normalization even when idleframing works. Test question→full/splitframedretry using realhelpers and recognizerrestarts. Prefer longestvalidpersonalalias overdefaultprefix, keep ordinaryproductwords, and preserve exactlegacytypedcompat without adding arbitraryglobalendaliases. Sourcefix is not proof of completephonecause.

