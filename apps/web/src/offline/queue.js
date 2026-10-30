import { assertExpensePayload, assertSalePayload, fingerprint, newId, QUEUE_STATUS } from "./types.js";

export class OfflineQueue {
  constructor(store) { this.store = store; }

  async enqueue(kind, shopId, payload, idempotencyKey = newId()) {
    if (!shopId) throw new TypeError("shopId is required");
    const normalized = kind === "sale" ? assertSalePayload(payload) : kind === "expense" ? assertExpensePayload(payload) : (() => { throw new TypeError("unsupported queue kind"); })();
    const key = String(idempotencyKey).trim();
    if (!key) throw new TypeError("idempotencyKey is required");
    const payloadFingerprint = await fingerprint(normalized);
    const existing = (await this.store.getAll("queue")).find((item) => item.shopId === shopId && item.idempotencyKey === key);
    if (existing) {
      if (existing.payloadFingerprint !== payloadFingerprint) throw new Error("idempotency key payload mismatch");
      return existing;
    }
    const entry = {
      id: newId(), kind, shopId, payload: normalized, idempotencyKey: key,
      payloadFingerprint, status: QUEUE_STATUS.PENDING, attempts: 0,
      capturedAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
    };
    await this.store.put("queue", entry);
    return entry;
  }

  async list(statuses = [QUEUE_STATUS.PENDING, QUEUE_STATUS.FAILED, QUEUE_STATUS.CONFLICT]) {
    return (await this.store.getAll("queue"))
      .filter((item) => statuses.includes(item.status))
      .sort((a, b) => a.capturedAt.localeCompare(b.capturedAt));
  }
  async get(id) { return this.store.get("queue", id); }
  async update(entry) { entry.updatedAt = new Date().toISOString(); await this.store.put("queue", entry); return entry; }
  async pendingCount() { return (await this.list([QUEUE_STATUS.PENDING, QUEUE_STATUS.SYNCING, QUEUE_STATUS.FAILED])).length; }
}
