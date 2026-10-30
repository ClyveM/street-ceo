# Fambai — Decisions

## 2026-10-30 — W2-FAMBAI-001

- Use a transport-agnostic queue boundary because the current API contract documents sales but not expenses. The sync caller supplies `sale` and `expense` request functions and is responsible for mapping the entry to endpoint headers.
- Keep committed records instead of deleting them. This preserves an audit/retry boundary and prevents a client from claiming success before a server response.
- Represent conflict, failed, syncing, pending, and committed as explicit states for UI consumption; HTTP 409 is deterministic conflict, other request errors are retryable failures.
- Use IndexedDB in browsers and a small in-memory store in non-browser tests. Both implement the same async store interface.
