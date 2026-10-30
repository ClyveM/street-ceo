# Fambai — Tasks

No tasks assigned yet. Initialized 2026-10-29.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W2-FAMBAI-001 — Offline queue and sync contract — active 2026-10-30

- Scope: offline layer inside `apps/web/` only: service worker, IndexedDB, queue and sync modules.
- Read AGENTS.md, this role, all six brain files, `docs/architecture.md`, `docs/api-contracts.md`, `docs/product-requirements.md`, and `tasks/master-board.md`.
- Add an idempotent queue model for manual sales and expenses, cached catalogue/totals, visible pending/sync/conflict states, and deterministic replay/conflict contracts. Preserve captured inputs and never claim committed success before server confirmation.
- Coordinate with Runako through documented interfaces; do not modify Runako-owned presentation components or backend/finance/inventory/voice code.
- Acceptance: offline enqueue/replay/duplicate/conflict tests pass and local data is clearly separated from committed server data.
