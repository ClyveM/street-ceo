# Dura — Lessons

## 2026-10-30 — W2-DURA-001

- Movement direction must be explicit at the primitive boundary: a sale request
  is a positive requested quantity but is recorded as a negative stock delta.
- Focused tests caught this sign mismatch before handoff; the final tests verify
  that a rejected sale leaves the prior balance unchanged.
- Full repository pytest currently cannot collect unrelated AI and voice tests
  because those tests import same-directory modules as top-level names. This is
  recorded as an integration blocker, not repaired outside Dura's ownership.

## 2026-10-31 — W6 inventory replay follow-up

- Source references are document identifiers, not safe idempotency keys by
  themselves: a multi-line document must allow one movement per product while
  an identical source/product retry must not apply stock twice.
- Inventory-level replay protection prevents duplicate receipt application and
  rejects altered retries before mutation; API transaction serialization and
  invoice staging remain Hwaro responsibilities.
