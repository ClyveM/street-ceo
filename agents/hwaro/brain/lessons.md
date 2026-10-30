# Hwaro — Lessons

No lessons recorded yet. Initialized 2026-10-29; no work performed.

## 2026-10-30 — W1-HWARO-001

- The local Python 3.13 host's synchronous `TestClient` and direct HTTPX ASGI
  transport hung before returning a response. Direct endpoint-handler tests
  remain runnable and cover transaction behavior; HTTP smoke coverage should be
  repeated in Chengetai's deployment/test environment.
- Validate all sale lines before mutating any product stock so insufficient
  stock leaves the entire attempted sale unchanged.
