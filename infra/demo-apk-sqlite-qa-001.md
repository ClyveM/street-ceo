# Connected SQLite APK QA — 2026-11-01

Task: DEMO-APK-SQLITE-QA-001. Chengetai.

Verdict: SQLite software acceptance and focused voice bridge tests pass; physical
APK acceptance remains unverified. Native lifecycle fixes were reviewed in source;
package validation belongs to root. This is not production or accounting sign-off.

## Completed changes

- Fixed repository-root imports for `python tests/run_checks.py`.
- Allowed ignored, untracked local environment configuration without reading it.
  Tracked environment files still fail even when ignored; nonignored local files
  fail; `.env.example` remains the template exception. Source secret scanning is
  unchanged. Two real temporary-Git regressions cover these boundaries.
- Added seven independent isolated HTTP/file acceptance tests in
  `tests/sqlite_demo_acceptance.py`.
- Extended CI's normal command to include all service tests and this acceptance
  suite. No remote CI execution is claimed.
- Under an explicit temporary scope extension, changed only construction of a
  synthetic sensitive assignment in `services/ai/test_tracing.py` so its fixture
  still exercises redaction without matching the literal-secret source gate.

## Evidence

| Check | Result | Provenance |
|---|---|---|
| `python tests/run_checks.py` | 8 passed; compilation passed | Chengetai, fresh execution, 2.116s |
| `python -m unittest services.ai.test_tracing -v` | 6 passed | Chengetai, fresh execution, 0.110s |
| `python -m pytest services tests/sqlite_demo_acceptance.py -q` with isolated basetemp | 181 passed; 16 existing SSL warnings | Root host execution, 12.95s, relayed to Chengetai |
| Scoped `git diff --check` | Passed | Chengetai; line-ending notices only |
| Focused speech bridge, quick-sale and wake tests | 28 passed, zero failures/skips | Chengetai, fresh execution, 258.0273ms |
| Full frontend suite and build | 114 passed; build 77 modules | Runako execution, relayed to Chengetai |
| Real configured Meta interpreter call | `record_sale`, Coke, quantity 1; persisted started/completed events with request/response | Root execution; no sale mutation; correlation `demo-provider-check-2b5577ce-3713-48ab-a094-95529d4b7ab5` |

Restricted ASGI tests stalled before application middleware. Root diagnosed a
restricted event-loop socketpair operation; the host test result above supersedes
that environment limitation. An interrupted escalation request is not test evidence.

The independent acceptance suite proves manual receipt and exact retry after
reopen, changed retry conflict, one successful last-unit concurrent sale, disk-write
rollback without success receipt, invalid later-line atomicity, precommit trace
failure rollback, postcommit trace failure recovery under the original key, and
controlled rejection when trace storage is unavailable. Temporary synthetic data
and database/trace files are isolated from the demo runtime. No provider calls are
made by these tests.

Trace tests establish tested credential/header/binary/data-URL/basic-PII redaction,
bounded payloads, correlation isolation and failure persistence. They are not a
claim that arbitrary sensitive text can always be detected.

## Source review and limits

SQLite middleware stages state and rolls back failed responses; it commits before
reporting a successful receipt. A trace failure after state commit returns an
explicit uncertain response requiring the same idempotency key. The initial
unguarded trace-write failure was reported and repaired by Hwaro. Catalogue
transcript parsing is labelled separately from actual provider work.

Runako addressed TTS initialization after destroy with a generation/null guard,
stale recognition cleanup with owner tokens and a serialized native queue, and
first-use permission/pause/resume start races with queued start deduplication and
native foreground deferral. Destroy rejects pending permission/resume calls. These
changes were reviewed in source, and the focused bridge tests now cover delayed
permission, stale disposal/callbacks, playback completion/failure, tender/change,
uncertain mutation recovery and repeat wake framing. They simulate the bridge;
they do not execute Android framework speech services.

There is no attached phone, and browser UI access is disabled in this environment.
Microphone permission, recognition accuracy, actual spoken playback, repeated
Apo/payment/sale cycles and foreground/background behavior therefore require
physical-device evidence. APK build, embedded assets and checksum are root's
packaging responsibility and are not established by this report's test results.

Scope excludes offline sync, invoice/social acceptance, forecasting and full
accounting remediation. PostgreSQL production deployment, authenticated identity,
production HTTPS and Ruzivo's financial review remain separate unresolved gates.
