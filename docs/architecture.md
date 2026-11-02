# Street CEO — Architecture (v0, 2026-10-29)

Status: implemented prototype; connected APK demo scope revised 2026-11-01.
See `docs/demo-mvp-acceptance.md` for the current acceptance gates.

## MVP stack

- Frontend: React + TypeScript Progressive Web App, mobile-first, responsive.
- Backend demo: Python FastAPI + file-backed SQLite, one API worker. PostgreSQL
  remains a separate adapter and is not required for this demo.
- Demo connectivity: APK connects to the backend over the local network;
  provider-backed Meta requests require internet. Offline sync is deferred.
- Voice: "Apo" wake word starts listening; "Napo" ends the command; short,
  fast commands for hands-free sales.
- AI: Meta models / Llama integrations for business insights and reasoning.
- Android demo: Capacitor APK with foreground native speech recognition and
  spoken responses; first-use microphone permission is required.

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
3. Connected request retries use stable idempotency keys; conflicts reject
   changed payloads. Offline replay is outside the current demo scope.
4. Cash/bank reconciliation (Verengai) and insights (Chiono + Ungwaru) read
   from the same ledger and stock truth.

## Binding constraints

- Contract-first APIs; no client depends on an undocumented endpoint.
- Balanced, sourced, reversible ledger entries; no silent edits.
- Stock movements always carry source documents; no silent negative stock.
- AI outputs consumed by code are schema-validated with tested fallbacks.
- Voice never posts an unconfirmed sale.
- Chengetai gates releases; Ruzivo reviews financially significant features.
