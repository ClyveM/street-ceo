import { SOURCE } from "./types.js";

const DB_NAME = "street-ceo-offline";
const DB_VERSION = 1;
const STORES = ["queue", "catalogue", "totals", "events"];

function clone(value) {
  return value === undefined ? undefined : typeof structuredClone === "function" ? structuredClone(value) : JSON.parse(JSON.stringify(value));
}

export class MemoryStore {
  constructor() { this.data = new Map(STORES.map((name) => [name, new Map()])); }
  async put(store, value, key = value.id) { this.data.get(store).set(key, clone(value)); return clone(value); }
  async get(store, key) { return clone(this.data.get(store).get(key)); }
  async delete(store, key) { this.data.get(store).delete(key); }
  async getAll(store) { return [...this.data.get(store).values()].map(clone); }
}

export class IndexedDbStore {
  constructor(name = DB_NAME) { this.name = name; this.dbPromise = null; }
  open() {
    if (this.dbPromise) return this.dbPromise;
    this.dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(this.name, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        for (const store of STORES) if (!db.objectStoreNames.contains(store)) db.createObjectStore(store);
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    return this.dbPromise;
  }
  async run(store, mode, operation) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(store, mode);
      const request = operation(tx.objectStore(store));
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
  put(store, value, key = value.id) { return this.run(store, "readwrite", (s) => s.put(value, key)); }
  get(store, key) { return this.run(store, "readonly", (s) => s.get(key)); }
  delete(store, key) { return this.run(store, "readwrite", (s) => s.delete(key)); }
  getAll(store) { return this.run(store, "readonly", (s) => s.getAll()); }
}

export function createStore() {
  return typeof indexedDB === "undefined" ? new MemoryStore() : new IndexedDbStore();
}

export async function cacheCatalogue(store, shopId, products, fetchedAt = new Date().toISOString()) {
  return store.put("catalogue", { id: shopId, shopId, products: clone(products), fetchedAt, source: SOURCE.SERVER });
}

export async function readCatalogue(store, shopId) { return store.get("catalogue", shopId); }

export async function cacheTotals(store, shopId, totals, source = SOURCE.SERVER, calculatedAt = new Date().toISOString()) {
  return store.put("totals", { id: shopId, shopId, totals: clone(totals), calculatedAt, source });
}

export async function readTotals(store, shopId) { return store.get("totals", shopId); }
