# Mutungamiri — Lessons

## 2026-10-29 — PowerShell `sl` is not Sapling

- Bare `sl` in PowerShell resolves to the `Set-Location` alias, not the Sapling
  CLI. Probe with `sl.exe` / `Get-Command`. Same caution for `hg`.
- Avoid chaining VCS probes with `;` so one missing tool does not mask others;
  check `Get-Command` output first.

## 2026-10-29 — EdenFS mount without VCS CLI

- `.sl/`, `.hg/`, `.eden/` can exist with no corresponding CLI on PATH.
  Treat metadata as read-only and do not infer repo health from dir names.
