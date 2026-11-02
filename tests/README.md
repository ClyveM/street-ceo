# Street CEO quality checks

Run from the repository root:

```text
python tests/run_checks.py
```

The runner uses Python's standard library only. It checks the agreed API and
architecture safety conventions, scans source-like files for accidental
secrets, compiles Python sources, and activates the backend smoke check once
`services/api/` exists.

Ignored, untracked local `.env` files are allowed without reading their contents.
Tracked environment files and nonignored local environment files fail the gate;
`.env.example` remains the documented template exception. The source secret scan
continues to run independently.

Run the service suite and isolated on-disk connected-demo acceptance after
installing `services/api/requirements.txt`:

```text
python -m pytest services tests/sqlite_demo_acceptance.py
```

The SQLite acceptance tests use temporary database and trace files, synthetic
records and in-process HTTP. They check restart/retry, last-unit concurrency,
atomic rollback and trace-write failures without live provider calls. They do
not establish physical-phone recognition, audio playback or production security.

The baseline also tests the APK-only download handler in memory and, when
PowerShell is installed, the launcher's no-write CheckOnly behavior and refusal
to treat a denied listener query as a free port. It also proves that an occupied
unknown port is preserved. Cross-check cases also cover empty CIM inventory with
occupied IPv4/IPv6 netstat rows, verified reuse, and failed/malformed netstat.
Linux CI skips only those ten
PowerShell-specific cases. Launcher usage and pending physical checks are in
`infra/phone-demo-checklist.md`.

The independent phone recovery client/probe contract tests use simulated fetch
responses, with no live requests or sales:

```text
node --experimental-strip-types --test tests/phone_recovery_client.mjs
```

They distinguish unpaid payment questions from requests that can record a sale,
preserve original retry payloads/keys, and require readiness plus a matching shop
before reporting a connection. The Python acceptance suite also verifies actual
HTTP 200 tender questions against an isolated SQLite file without recording a sale.

Counter receipt/wake safety can be checked independently without a phone:

```text
node --experimental-strip-types --test tests/counter_polish_client.mjs
```

These cases compose the wake framer with the completed-receipt guard and verify
same-utterance/next-utterance preservation, pending-state protection and explicit
pause persistence. They do not prove rendered layout or actual microphone behavior.

Backend agents should add focused tests for each endpoint and keep the smoke
entrypoint importable as `services.api.main:app` or `services.api.app:app`.
Mutating endpoint tests must cover authentication, shop authorization,
validation, audit data, reversal behavior, and idempotency where applicable.

## Clean-checkout gate

Run `python infra/dev.py check`, then `python infra/dev.py setup` for a project
virtual environment and locked shop dependencies. Separate foreground terminals:
`python infra/dev.py api` and `python infra/dev.py web`. Existing environment
settings take precedence; no secret file is copied or changed.

The staged source audit is `python infra/check_source_manifest.py`. It checks
path names only: required wrapper files, locks, catalogue and assets must be
staged; local configuration, databases, attachments and generated output must
not be staged. Run after staging, before commit. Keep the Gradle wrapper JAR.

CI runs backend checks with STREET_CEO_STORE=memory and STREET_CEO_SEED_DEMO=0,
shop `npm ci`, frontend contracts/build and independent client checks. The source
secret scanner uses Git's tracked plus nonignored additions: ignored local files
are not opened, while tracked files remain scanned even when ignored. Archive
verification must use a separate initialized Git snapshot/index for these policy
checks; it must not silently use a parent working-tree index.
