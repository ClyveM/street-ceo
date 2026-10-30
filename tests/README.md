# Street CEO quality checks

Run from the repository root:

```text
python tests/run_checks.py
```

The runner uses Python's standard library only. It checks the agreed API and
architecture safety conventions, scans source-like files for accidental
secrets, compiles Python sources, and activates the backend smoke check once
`services/api/` exists.

Backend agents should add focused tests for each endpoint and keep the smoke
entrypoint importable as `services.api.main:app` or `services.api.app:app`.
Mutating endpoint tests must cover authentication, shop authorization,
validation, audit data, reversal behavior, and idempotency where applicable.
