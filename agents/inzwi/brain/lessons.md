# Inzwi — Lessons

## 2026-10-30 — W2-INZWI-001

- Text fallback can map a complete submitted command through Apo/capture/Napo
  automatically and arrive at quote; callers should not require a literal Napo.
- A retry from failure must re-enter payment/validation before calling the gateway;
  otherwise the basket is preserved but cannot be safely resubmitted.
- Repository-wide checks require `PYTHONPATH=.` in this shell so `services.*`
  imports resolve; the focused voice suite is independently runnable from its
  directory with unittest discovery.
