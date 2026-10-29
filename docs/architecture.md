# Street CEO — Architecture (v0, 2026-10-29)

Status: agreed plan. No code implements this yet.

## MVP stack

- Frontend: React + TypeScript Progressive Web App, mobile-first, responsive.
- Backend: Python FastAPI + PostgreSQL (server database).
- Offline: IndexedDB in the PWA; queued transactions sync to the server.
- Voice: "Apo" wake word starts listening; "Napo" ends the command; short,
  fast commands for hands-free sales.
- AI: Meta models / Llama integrations for business insights and reasoning.
- No native Android/iOS app for the hackathon MVP.

## Components and owners

| Component | Owner | Notes |
|-----------|-------|-------|
| Web UI (`apps/web/`) | Runako | Fambai owns the offline layer inside it |
| Offline + sync | Fambai | Service worker, IndexedDB, sync engine |
| API + DB + auth | Hwaro | Contract-first; owns `api-contracts.md` in practice |
| Voice pipeline | Inzwi | Grammar in `voice-design.md` |
| Meta AI inference | Ungwaru | Structured outputs only |
| Finance services | Verengai | Under Ruzivo's accounting review |
| Inventory services | Dura | Source-documented stock movements |
| Analytics | Chiono | Read-only on operational tables |
| Tests, CI/CD, infra | Chengetai | Gates every release |
| Accounting policy | Ruzivo | Advisory; `docs/finance/` memos |

## Data flow (planned)

1. Vendor records a sale via UI (Runako), offline queue (Fambai), or voice
   (Inzwi: Apo … command … Napo).
2. Sale posts through Hwaro's API: stock decremented (Dura), ledger updated
   (Verengai) in one auditable transaction.
3. Offline sales replay via idempotent sync; conflicts resolve deterministically.
4. Cash/bank reconciliation (Verengai) and insights (Chiono + Ungwaru) read
   from the same ledger and stock truth.

## Binding constraints

- Contract-first APIs; no client depends on an undocumented endpoint.
- Balanced, sourced, reversible ledger entries; no silent edits.
- Stock movements always carry source documents; no silent negative stock.
- AI outputs consumed by code are schema-validated with tested fallbacks.
- Voice never posts an unconfirmed sale.
- Chengetai gates releases; Ruzivo reviews financially significant features.
