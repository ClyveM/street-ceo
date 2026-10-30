export type Tender = 'cash' | 'bank'

export type Product = {
  id: number
  shop_id: number
  sku: string
  name: string
  unit_price_cents: number
  stock_qty: number
}

export type SaleLine = { product_id: number; quantity: number }

export type SaleRequest = { lines: SaleLine[]; tender: Tender }

export type Sale = SaleRequest & {
  id: number
  shop_id: number
  total_cents: number
  created_at: string
}

export const demoProducts: Product[] = [
  { id: 1, shop_id: 1, sku: 'COKE-300', name: 'Coca-Cola 300ml', unit_price_cents: 150, stock_qty: 18 },
  { id: 2, shop_id: 1, sku: 'BREAD-700', name: 'Bread loaf', unit_price_cents: 180, stock_qty: 11 },
  { id: 3, shop_id: 1, sku: 'SUGAR-1KG', name: 'Sugar 1kg', unit_price_cents: 240, stock_qty: 7 },
  { id: 4, shop_id: 1, sku: 'MILK-500', name: 'Milk 500ml', unit_price_cents: 130, stock_qty: 15 },
  { id: 5, shop_id: 1, sku: 'CHIPS-100', name: 'Potato chips', unit_price_cents: 100, stock_qty: 23 },
  { id: 6, shop_id: 1, sku: 'SOAP-175', name: 'Bath soap', unit_price_cents: 220, stock_qty: 5 },
]

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
const SHOP_ID = 1

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', 'X-Shop-ID': String(SHOP_ID), ...(init?.headers ?? {}) },
  })
  if (!response.ok) throw new Error(`API request failed (${response.status})`)
  return response.json() as Promise<T>
}

/** The only network boundary used by screens. Fambai can later decorate this with sync. */
export const apiClient = {
  async listProducts(): Promise<{ products: Product[]; isDemo: boolean }> {
    if (!API_BASE_URL) return { products: demoProducts, isDemo: true }
    try {
      return { products: await request<Product[]>(`/shops/${SHOP_ID}/products`), isDemo: false }
    } catch {
      return { products: demoProducts, isDemo: true }
    }
  },
  async createSale(payload: SaleRequest): Promise<Sale> {
    return request<Sale>(`/shops/${SHOP_ID}/sales`, {
      method: 'POST',
      headers: { 'Idempotency-Key': `web-${Date.now()}-${Math.random().toString(16).slice(2)}` },
      body: JSON.stringify(payload),
    })
  },
}

export function formatMoney(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`
}
