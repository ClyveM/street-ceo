# Chengetai — Memory

Initialized 2026-10-29; updated 2026-10-30 under W1-CHENGETAI-001.

## Project facts (confirmed)

- Street CEO hackathon MVP; deadline November 4, 2026.
- QA scope: automated testing, security, CI/CD, deployment, reliability.
- No application code exists yet; no pipelines exist yet.

## Stable context

- Role: `agents/chengetai/role.md`. Activation protocol: `AGENTS.md` section 2.
- Final word on release readiness; blocks include failure report + re-entry criteria.
- Owns shared suites, e2e, infra, CI config. Validates; does not add features.
- Gates cannot be lowered for a date without Mutungamiri + Owner approval.

## Confirmed quality foundation

- `tests/run_checks.py` is the dependency-light entrypoint and uses stdlib
  `unittest`, source compilation, contract checks, and security checks.
- `.github/workflows/quality.yml` installs `services/api/requirements.txt` when
  present, runs the dependency-light checks, then runs `pytest services/api`.
- `infra/security-baseline.md` defines merge gates and failure re-entry rules.
- Backend smoke import is intentionally skipped when FastAPI is unavailable;
  with backend dependencies installed it requires `services.api.main:app` or
  `services.api.app:app`.
