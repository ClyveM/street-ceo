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
