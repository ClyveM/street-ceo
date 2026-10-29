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
