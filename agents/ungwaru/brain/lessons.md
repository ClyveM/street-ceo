# Ungwaru — Lessons

## 2026-10-30 — W1-UNGWARU-001

- Provider-neutral contracts can be tested without network access by injecting
  a small fake provider; this keeps the MVP boundary verifiable before Meta
  credentials exist.
- An insight schema needs evidence IDs, not only prose and confidence. Checking
  IDs against the request snapshot prevents a model from fabricating support.
- Prompt-injection handling is safest at the boundary: classify the transcript
  as untrusted data, reject obvious instruction markers, and never forward a
  blocked transcript to the provider.
