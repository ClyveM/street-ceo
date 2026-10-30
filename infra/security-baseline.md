# Security and quality baseline

This baseline is the minimum gate for the Street CEO MVP. It is an
engineering checklist, not a statutory or external security certification.

## Required before merge

- `python tests/run_checks.py` passes from a clean checkout.
- No `.env` or credential-bearing file is committed; runtime secrets come from
  the deployment environment or a secret manager.
- Mutating API routes authenticate the caller, enforce per-shop authorization,
  validate input, and emit auditable actor/time/source data.
- Money and stock writes are tested for idempotency, reversal behavior, and
  prevention of silent negative stock.
- AI output is schema-validated and has a tested fallback; voice cannot post an
  unconfirmed sale.
- Database migrations are reviewed for safe forward application and rollback
  impact before deployment.

## Triage convention

Quality failures must identify the command, failing check, affected path, and
re-entry condition. A release remains blocked until the cited failure is fixed
and the same command passes again.

## Local-only data

Tests may use synthetic fixtures only. Never place credentials, customer PII,
or sensitive financial data in fixtures, logs, snapshots, or brain files.
