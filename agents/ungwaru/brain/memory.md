# Ungwaru — Memory

Initialized 2026-10-29. No prior sessions; no work performed yet.

## Project facts (confirmed)

- Street CEO hackathon MVP; deadline November 4, 2026.
- Meta models / Llama integrations for business insights and reasoning.
- No application code exists yet; no model selected yet.

## Stable context

- Role: `agents/ungwaru/role.md`. Activation protocol: `AGENTS.md` section 2.
- Rule: structured, schema-validated outputs for every AI feature consumed by code.
- Serves Inzwi (NLU options) and Chiono (reasoning over metrics).
- Model choices need Mutungamiri approval with cost/latency envelope.

## Verified implementation facts (2026-10-30, W1-UNGWARU-001)

- `services/ai/boundary.py` exposes a provider-neutral `Provider` protocol and
  `StructuredAI` facade. Providers return mappings only; callers receive typed
  results or explicit fallbacks.
- Sale intents and business insights reject unknown fields and invalid values.
  Insight responses must cite IDs from the supplied evidence snapshot.
- No live Meta/Llama credentials, SDK installation, deployment target, or
  successful model request was observed in this workspace.
- Official evidence recorded in `services/ai/capability_matrix.py` supports
  Llama 3.1/4 structured tool-call formats and the official Llama API Python
  client's timeout/error/retry behavior. This is capability evidence, not live
  availability evidence.
