# Offline layer contract

Fambai owns this directory. Runako-owned presentation code should consume the
plain objects exported by `index.js` and should not reach into IndexedDB.

## Enqueue

```js
const store = createStore();
const queue = new OfflineQueue(store);
await queue.enqueue("sale", shopId, { lines: [{ product_id, quantity }], tender: "cash" }, idempotencyKey);
await queue.enqueue("expense", shopId, { amount_cents, description, tender: "cash" }, idempotencyKey);
```

The key is retained across retries. Reusing a key with a different payload is
rejected locally. A queue entry remains the source of truth for the captured
input until the server confirms it; it is never deleted after commit.

## Replay

`SyncEngine.sync({ sale, expense })` calls the supplied transport with the full
queue entry. The transport must send `entry.payload`, `entry.shopId`, and the
`entry.idempotencyKey` as `Idempotency-Key`. A successful response can be any
JSON value or `{data}`. A 409 response is retained as `conflict`; other errors
are retained as `failed` for a later retry.

`onStateChange` receives the UI-facing state:

```js
{ online, syncing, pendingCount, conflicts, failed, lastError }
```

`QUEUE_STATUS` and `SOURCE` are stable display/filter contracts. Cached
catalogue and totals records include `source`, `fetchedAt` or `calculatedAt`,
so local values cannot be mistaken for server-committed values.
