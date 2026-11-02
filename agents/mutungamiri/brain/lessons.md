# Mutungamiri — Lessons

## 2026-10-29 — PowerShell `sl` is not Sapling

- Bare `sl` in PowerShell resolves to the `Set-Location` alias, not the Sapling
  CLI. Probe with `sl.exe` / `Get-Command`. Same caution for `hg`.
- Avoid chaining VCS probes with `;` so one missing tool does not mask others;
  check `Get-Command` output first.

## 2026-10-29 — EdenFS mount without VCS CLI

- `.sl/`, `.hg/`, `.eden/` can exist with no corresponding CLI on PATH.
  Treat metadata as read-only and do not infer repo health from dir names.

## 2026-11-01 — SPRINT90 Windows listener inventory
Get-NetTCPConnection can silently return an incomplete listener table in this environment. Cross-check netstat, validate expected process/database identity, and preserve unknown listeners. Real netstat includes CLOSED and numbered FIN_WAIT states; mock fixtures must include full realistic tables. Launcher host reuse verified after regressions.

## 2026-11-01 — PHONE-RECOVERY-001
Classify sale uncertainty by whether a request can actually commit payment, not merely POST method. Question-only failures are recoverable without falsely claiming a paid sale; preserve earlier genuine uncertainty. navigator.onLine is not backend reachability. Service workers can ignore fetch no-store and return stale API JSON; use network-only routing and unique probe URLs for older workers. Windows CIM state filters can include CLOSED rows or omit live listeners; validate state and trusted live runtime identity.

## 2026-11-01 — CATALOGUE-VOICE
A strict-parser early rejection can accidentally make an advertised AI fallback unreachable; test actual routing and provider_called provenance. Match API proposal schemas against strict frontend parsers (intent field omission was caught/fixed). Model proposals must resolve all known IDs and preserve independently extracted quantities, with explicit confirmation. PowerShell @(Invoke-RestMethod empty-array) can mislead count checks; validate raw JSON or audit the isolated database independently.

2026-11-02 MUSE-OUTAGE: trace lateprovidercompletion can distinguish too-short resolverdeadline from provideroutage. Align resolver24s<client30s whilekeeping2inflight/noautoretry; timeoutcompletion mustneverlatecommit. LauncherAPIstart can succeed beforedownloadinventoryfailure: verifyruntimeindependently and preserveunknownlisteners.
