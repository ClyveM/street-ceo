import test from "node:test";
import assert from "node:assert/strict";
import { MemoryStore, cacheCatalogue, cacheTotals, readCatalogue, readTotals } from "./store.js";
import { OfflineQueue } from "./queue.js";
import { QUEUE_STATUS, SOURCE } from "./types.js";
import { SyncEngine } from "./sync.js";

const sale = { lines: [{ product_id: "p-1", quantity: 2 }], tender: "cash" };

test("enqueue is idempotent and preserves the captured sale", async () => {
  const queue = new OfflineQueue(new MemoryStore());
  const first = await queue.enqueue("sale", "shop-1", sale, "sale-key-1");
  const second = await queue.enqueue("sale", "shop-1", { ...sale, lines: [...sale.lines] }, "sale-key-1");
  assert.equal(first.id, second.id);
  assert.deepEqual((await queue.list()).map((entry) => entry.payload), [sale]);
  await assert.rejects(() => queue.enqueue("sale", "shop-1", { lines: [{ product_id: "p-1", quantity: 3 }] }, "sale-key-1"), /payload mismatch/);
});

test("sale and expense replay once, then remain committed on a repeated sync", async () => {
  const queue = new OfflineQueue(new MemoryStore());
  await queue.enqueue("sale", "shop-1", sale, "sale-key-1");
  await queue.enqueue("expense", "shop-1", { amount_cents: 250, description: "Transport" }, "expense-key-1");
  const calls = [];
  const engine = new SyncEngine(queue);
  const transport = {
    sale: async (entry) => { calls.push([entry.kind, entry.idempotencyKey]); return { ok: true, data: { id: "server-sale" } }; },
    expense: async (entry) => { calls.push([entry.kind, entry.idempotencyKey]); return { ok: true, data: { id: "server-expense" } }; },
  };
  assert.deepEqual(await engine.sync(transport), { synced: 2, skipped: false });
  assert.deepEqual(calls, [["sale", "sale-key-1"], ["expense", "expense-key-1"]]);
  assert.deepEqual(await engine.sync(transport), { synced: 0, skipped: false });
  assert.equal((await queue.list([QUEUE_STATUS.COMMITTED])).length, 2);
});

test("409 becomes a visible conflict while keeping the payload", async () => {
  const queue = new OfflineQueue(new MemoryStore());
  const entry = await queue.enqueue("sale", "shop-1", sale, "sale-key-1");
  const states = [];
  const engine = new SyncEngine(queue, { onStateChange: (state) => states.push(state) });
  await engine.sync({ sale: async () => ({ status: 409, detail: "insufficient stock" }) });
  const stored = await queue.get(entry.id);
  assert.equal(stored.status, QUEUE_STATUS.CONFLICT);
  assert.deepEqual(stored.payload, sale);
  assert.equal(engine.state.conflicts[0].reason, "insufficient stock");
  assert.ok(states.some((state) => state.conflicts.length === 1));
});

test("catalogue and totals identify their source", async () => {
  const store = new MemoryStore();
  await cacheCatalogue(store, "shop-1", [{ id: "p-1", name: "Bread" }]);
  await cacheTotals(store, "shop-1", { cash_cents: 1000 }, SOURCE.LOCAL);
  assert.equal((await readCatalogue(store, "shop-1")).source, SOURCE.SERVER);
  assert.equal((await readTotals(store, "shop-1")).source, SOURCE.LOCAL);
});
