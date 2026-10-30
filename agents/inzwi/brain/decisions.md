# Inzwi — Decisions

## 2026-10-30 — W2-INZWI-001

- Keep voice provider-neutral by accepting an `Interpreter` protocol that returns
  `CommandIntent`; no Meta/provider import or microphone implementation belongs here.
- Resolve names through a `CatalogResolver`; ambiguous, unavailable, and
  insufficient-stock results fail without creating a basket mutation.
- Submit only the documented sales contract (`product_id`, `quantity`, `tender`,
  idempotency key). Price overrides are not supported because the API contract
  does not accept them.
- Preserve basket and one idempotency key through a retryable gateway failure;
  commit only after quote confirmation and tender selection.
- Treat a supplied cash amount below the quote as an interaction-level failure;
  omitted amount remains allowed because MVP tender recording is not settlement.
