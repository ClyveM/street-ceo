# Fambai — Memory

Initialized 2026-10-29. No prior sessions; no work performed yet.

## Project facts (confirmed)

- Street CEO hackathon MVP; deadline November 4, 2026.
- Mobile = PWA on low-cost Android; no native app for the MVP.
- No application code exists yet; offline layer not yet scaffolded.

## Stable context

- Role: `agents/fambai/role.md`. Activation protocol: `AGENTS.md` section 2.
- Owns service worker, IndexedDB, offline queue, sync engine.
- Core guarantee: sell offline, reconnect, reconcile with zero data loss.
- Sync protocol to be agreed with Hwaro (idempotency, replay order, conflicts).

## Verified implementation facts (2026-10-30, W2-FAMBAI-001)

- Offline code is under `apps/web/src/offline/`; service worker is `apps/web/service-worker.js`.
- Queue records retain captured sale/expense payloads after commit, with stable `idempotencyKey`, canonical payload fingerprint, status, attempt count, and server result.
- `SyncEngine` replays captured entries in capture order, classifies HTTP 409 as visible `conflict`, and retains non-conflict failures for retry.
- Catalogue/totals cache records include `source` (`server` or `local`) and timestamps.
