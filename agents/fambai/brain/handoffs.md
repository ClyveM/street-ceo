# Fambai — Handoffs

## Handoff — W2-FAMBAI-001 — 2026-10-30

### Assignment

Implement the mobile offline layer: idempotent manual sale/expense queue,
catalogue/totals cache, visible sync/conflict contracts, service-worker shell,
and tests. Scope stayed within `apps/web/` and Fambai's own brain files.

### Files changed

- `apps/web/src/offline/types.js`: queue statuses, source markers, payload validation, stable fingerprinting.
- `apps/web/src/offline/store.js`: IndexedDB store plus test-safe memory store and cache helpers.
- `apps/web/src/offline/queue.js`: idempotent sale/expense enqueue and ordered listing.
- `apps/web/src/offline/sync.js`: replay engine with pending/syncing/committed/conflict/failed state reporting.
- `apps/web/src/offline/index.js`: public exports.
- `apps/web/src/offline/README.md`: Runako-facing interface contract.
- `apps/web/src/offline/offline.test.js`: four automated tests.
- `apps/web/service-worker.js`: app-shell cache and offline GET fallback.
- `apps/web/package.json`: ES module mode and offline test script.

### Evidence

- `npm run test:offline` in `apps/web`: 4 tests passed, 0 failed.
- `python tests/run_checks.py` at repository root: 5 passed, 1 error in the pre-existing backend smoke test (`ModuleNotFoundError: No module named 'services'`); no Fambai test failed.

### Outstanding issues / next agent instructions

- Hwaro must confirm the expense endpoint and response shape; the transport boundary is ready but intentionally does not invent that endpoint.
- Runako should consume `SyncEngine.state`, `QUEUE_STATUS`, `SOURCE`, and cache helpers through `src/offline/index.js`.
- Chengetai should add the web test command to CI and validate service-worker behavior on the target device matrix.
