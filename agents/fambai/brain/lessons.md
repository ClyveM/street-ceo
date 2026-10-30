# Fambai — Lessons

## 2026-10-30 — W2-FAMBAI-001

- Node's module mode must be explicit for browser-style ES modules; `apps/web/package.json` sets `type: module` and makes the offline test command reproducible.
- The repository-wide Python check currently fails before exercising Fambai because its import path cannot resolve `services`; this is recorded as an existing cross-team blocker rather than changed from the offline scope.
