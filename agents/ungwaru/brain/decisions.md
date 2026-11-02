# Ungwaru — Decisions

## 2026-10-30 — W1-UNGWARU-001

- Keep model integration behind a provider protocol returning JSON-compatible
  mappings. Rationale: Llama API, local inference, and other providers can be
  swapped without leaking SDK types into business code.
- Treat model output as untrusted until strict schema validation succeeds.
  Unknown fields, unsupported enum values, invalid quantities, and unsupported
  evidence references fail closed.
- On timeout, provider exception, missing provider, prompt injection marker, or
  schema failure, return a typed non-actionable fallback. No fallback can post a
  sale or invent insight evidence.
- Do not select a production model yet. Official capability evidence exists,
  but this workspace has no live access or measured cost/latency evidence.

## 2026-10-30 — W3-MUSE-001

- Keep Ask Muse behind the existing `StructuredAI` boundary and Meta-compatible
  server adapter. Rationale: the browser must never receive the provider key,
  and model output must remain schema-validated.
- Treat profit as unavailable when the evidence snapshot lacks COGS or expenses.
  Rationale: sales revenue alone cannot support a defensible profit answer.

## 2026-10-31 — W4-SOCIAL-001

- Social generation is draft-only at the AI boundary. It cannot publish or
  schedule content, and the output status must remain `draft`.
- Factual social claims must cite an explicitly selected product and one of its
  supplied fields (`name`, `sku`, or `price_minor`). Rationale: catchy copy may
  be creative, but product facts must remain inspectable and grounded.

## 2026-10-31 — W4-MUSE-IMAGE-001

- Do not route image requests through the existing Llama text chat endpoint.
  Image generation uses a separate explicitly configured Muse Image model and
  endpoint; absent that configuration, return `provider_not_configured`.
- Image results are draft-only and may carry a URL/data/file reference, but the
  AI boundary cannot publish, schedule, or post to Facebook.

## 2026-11-01 — DEMO-MUSE-TRACE-001
Use separate SQLite provider-trace DB to avoid second-writer deadlock while shop transaction is open. Persist start before outbound call and terminal event after; trace storage failure fails call. Store bounded redacted requests/provider JSON, not keys or raw audio. Copy ContextVars into provider executor to retain API correlation.

## 2026-11-01 — CATALOGUE-VOICE-MUSE-001
Model matches known IDs only against actual bounded catalogue. Quantity slots originate locally, never model guesses; all slots covered and proposals confirmed before sale. Deterministic question uses trusted names/qty. Shared bounded executor prevents timed-out request retries from growing unbounded worker threads. API remains authoritative for stock/prices/payment.

## 2026-11-02 — MUSE-OUTAGE-001
Use catalogue outer deadline24s/max25 against provider20s read/frontend30s budgets, preserving bounded2worker concurrency/no retry. Confirmed incident trace justifies longer wait; no alias stripping or validation weakening. Timeout feedback states delay and no sale rather than unsupported provider-down claim.

## 2026-11-02 — FAST-VOICE-001 supersedes outage budget
Owner rejects24s criticalsale wait. Root approved local exactuniquealias+boundedobservedASRtail proposal before realMuse; all items/qty known and explicitYes required, source honest. One-edit deferred. RemainingMuse deadline6smax; keep2capacity/no retry. Cached provider pools reduce TLS setup overhead without model-speed guarantee.
