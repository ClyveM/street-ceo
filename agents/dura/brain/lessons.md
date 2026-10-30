# Dura — Lessons

## 2026-10-30 — W2-DURA-001

- Movement direction must be explicit at the primitive boundary: a sale request
  is a positive requested quantity but is recorded as a negative stock delta.
- Focused tests caught this sign mismatch before handoff; the final tests verify
  that a rejected sale leaves the prior balance unchanged.
- Full repository pytest currently cannot collect unrelated AI and voice tests
  because those tests import same-directory modules as top-level names. This is
  recorded as an integration blocker, not repaired outside Dura's ownership.
