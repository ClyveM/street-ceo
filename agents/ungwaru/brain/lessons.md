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

## 2026-10-30 — W3-MUSE-001

- A polished Ask Muse screen can still be a placeholder if its submit handler
  never reaches an API route; verify the network boundary before judging the
  model behavior.
- Financial questions need an explicit completeness check before any model call:
  sales totals are evidence of revenue, not evidence of profit.

## 2026-10-31 — W4-SOCIAL-001

- Social copy needs a separate contract from business insights: a draft may be
  creative, but every factual claim still needs a product and source-field link.
- Passing an image reference is safer than pretending a text-only model has
  inspected the image; multimodal analysis should be added only with an explicit
  provider capability and test fixture.

## 2026-10-31 — W4-MUSE-IMAGE-001

- A valid text-model credential is not evidence of image entitlement. The model
  ID and endpoint must be checked separately, and the feature should remain
  visibly unavailable until an image smoke test succeeds.
- Product image references need transport validation: accept provider-safe URLs,
  data URLs, or file IDs, and reject local filesystem paths before any network
  call.

## 2026-10-31 — W6-MUSE-PROVIDER-WIRING-001

- Provider ID validation and provider payload construction must share the same
  accepted prefixes. A boundary can pass validation while the adapter silently
  changes the transport semantics, as happened for `file_` PDF IDs.
- A LAN smoke test is not evidenced by configured credentials alone: record the
  listener and endpoint result separately, and keep the feature fail-closed when
  the API is unreachable.

## 2026-11-01 — SPRINT90-TRACE-003
Trace truncation must preserve sanitized routing metadata such as shop_id independently of body size, or investigation filters silently hide large events. Bound Unicode by encoded bytes and sanitize SQL index values as well as JSON payload.

## 2026-11-02 — MUSE-OUTAGE-001
Correlate caller deadline with eventual provider terminal event before calling an incident provider outage. An8s local deadline discarded a valid provider completion19.5s later. Keep outer/provider/client budgets aligned, bound lingering work and distinguish timeout/busy/config errors from product ambiguity.

2026-11-02 MUSE-INSIGHT-SCHEMA-001: JSON-object responseformat guarantees syntax only, not applicationfields. An internal ProviderRequest.output_schema is ineffective unless the transport sends it to the model. Transmit explicit exactschema; keep strict downstream validation and test actual HTTPpayload, not merely requestobjects.
