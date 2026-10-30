import { OfflineConflictError, QUEUE_STATUS } from "./types.js";

export class SyncEngine {
  constructor(queue, { onStateChange } = {}) {
    this.queue = queue; this.onStateChange = onStateChange; this.state = { online: true, syncing: false, pendingCount: 0, conflicts: [], failed: [], lastError: null };
  }
  async setOnline(online) { this.state.online = Boolean(online); await this.publish(); }
  async publish() { this.state.pendingCount = await this.queue.pendingCount(); this.onStateChange?.({ ...this.state, conflicts: [...this.state.conflicts], failed: [...this.state.failed] }); }
  async sync(transport) {
    if (!this.state.online) return { synced: 0, skipped: true };
    this.state.syncing = true; this.state.lastError = null; await this.publish();
    let synced = 0;
    try {
      for (const entry of await this.queue.list([QUEUE_STATUS.PENDING, QUEUE_STATUS.FAILED])) {
        const current = await this.queue.update({ ...entry, status: QUEUE_STATUS.SYNCING, attempts: entry.attempts + 1 });
        try {
          const response = await transport[current.kind](current);
          if (!response || response.ok === false || (response.status && response.status >= 400)) {
            if (response?.status === 409) throw new OfflineConflictError(response.detail || "server conflict", current, response);
            throw new Error(response?.detail || "sync request failed");
          }
          await this.queue.update({ ...current, status: QUEUE_STATUS.COMMITTED, serverResult: response.data ?? response, committedAt: new Date().toISOString() });
          synced += 1;
        } catch (error) {
          const conflict = error instanceof OfflineConflictError || error?.status === 409;
          const updated = { ...current, status: conflict ? QUEUE_STATUS.CONFLICT : QUEUE_STATUS.FAILED, error: String(error.message || error) };
          await this.queue.update(updated);
          if (conflict) this.state.conflicts.push({ entryId: current.id, reason: updated.error });
          else this.state.failed.push({ entryId: current.id, reason: updated.error });
          if (!conflict) this.state.lastError = updated.error;
        }
        await this.publish();
      }
      return { synced, skipped: false };
    } finally { this.state.syncing = false; await this.publish(); }
  }
}
