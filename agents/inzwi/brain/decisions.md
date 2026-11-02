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


## 2026-10-31 — W6-DEMO-VOICE-001
Backend voice contract supersedes optional cash amount: ask actual received amount,
forward amount_received_cents; never infer it. Closing Apo confirms basket, but
cash still requires amount. needs_tender is not a receipt. Undo requires explicit
reversed acknowledgement and retains sale for safe retry if acknowledgement fails.

## 2026-10-31 — W6-DEMO-VOICE-001 follow-up

- Normalize only terminal spoken punctuation at the state-machine boundary. ASR
  commonly returns `Apo.` or `Cash, 500.`; accepting these bounded variants keeps
  Quick Sale automatic closing usable without widening the command grammar or
  changing backend tender semantics.
