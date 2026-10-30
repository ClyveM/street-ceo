/**
 * Shared offline contracts. These are deliberately plain JSON objects so the
 * same shapes can cross IndexedDB, the sync worker, and the UI boundary.
 */

export const QUEUE_STATUS = Object.freeze({
  PENDING: "pending",
  SYNCING: "syncing",
  COMMITTED: "committed",
  CONFLICT: "conflict",
  FAILED: "failed",
});

export const SOURCE = Object.freeze({ LOCAL: "local", SERVER: "server" });

export class OfflineConflictError extends Error {
  constructor(message, entry, cause) {
    super(message);
    this.name = "OfflineConflictError";
    this.entry = entry;
    this.cause = cause;
  }
}

export function assertSalePayload(payload) {
  if (!payload || !Array.isArray(payload.lines) || payload.lines.length === 0) {
    throw new TypeError("sale requires at least one line");
  }
  for (const line of payload.lines) {
    if (!line?.product_id || !Number.isInteger(line.quantity) || line.quantity <= 0) {
      throw new TypeError("sale lines require product_id and positive whole quantity");
    }
  }
  if (payload.lines.length !== new Set(payload.lines.map((line) => line.product_id)).size) {
    throw new TypeError("product_id may appear only once");
  }
  return { lines: payload.lines.map((line) => ({ ...line })), tender: String(payload.tender || "cash").trim().toLowerCase() };
}

export function assertExpensePayload(payload) {
  if (!payload || !Number.isInteger(payload.amount_cents) || payload.amount_cents <= 0) {
    throw new TypeError("expense requires a positive integer amount_cents");
  }
  const description = String(payload.description || "").trim();
  if (!description) throw new TypeError("expense requires a description");
  return { amount_cents: payload.amount_cents, description, tender: String(payload.tender || "cash").trim().toLowerCase() };
}

export function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}

export async function fingerprint(payload) {
  const text = stableJson(payload);
  if (globalThis.crypto?.subtle) {
    const bytes = new TextEncoder().encode(text);
    const hash = await crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(hash)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  }
  // Tests and older WebViews can still use a deterministic non-cryptographic fallback.
  let hash = 2166136261;
  for (const char of text) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619);
  return `fnv1a-${(hash >>> 0).toString(16)}`;
}

export function newId() {
  return globalThis.crypto?.randomUUID?.() || `offline-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}
