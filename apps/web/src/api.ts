import { requestMuse, resolveShopConnection, shopConfigurationError } from './muse'
import { normalizeApiBaseUrl, validateApiBaseUrl } from './apiUrl'
import { createCostsClient } from './costs'
import { createProductCostsClient } from './productCosts'
import { createRetailClient } from './retailContracts'
import { requestSale } from './saleRequest'

export type Tender = 'cash' | 'bank'

export type Product = {
  id: string
  shop_id: string
  sku: string
  name: string
  unit_price_cents: number
  stock_qty: number
  unit_cost_micros?: number | null
  cost_source_invoice_id?: string | null
}

export type SaleLine = { product_id: string; quantity: number }

export type SaleRequest = { lines: SaleLine[]; tender: Tender; amount_received_cents?: number }

export type Sale = Omit<SaleRequest, 'amount_received_cents'> & {
  id: string
  shop_id: string
  total_cents: number
  stock_after: Record<string, number>
  created_at: string
  amount_received_cents?: number | null
  change_cents?: number
  receipt_lines?: { product_id: string; product_name: string; quantity: number; sku?: string; unit_price_cents?: number; line_total_cents?: number }[]
}

export type ShopSummary = {
  daily_summary_count?: number
  sales_total_cents: number
  transaction_count: number
  low_stock_count: number
  sales_change_percent: number | null
  insight: string
}


// Illustrative starter costs approved in STARTER-COGS-001; this remains a labelled fallback, not live supplier evidence.
export const demoProducts: Product[] = [
  { id: '00000000-0000-0000-0000-000000000001', shop_id: '00000000-0000-0000-0000-000000000001', sku: 'COKE-300', name: 'Coca-Cola 300ml', unit_price_cents: 150, stock_qty: 18, unit_cost_micros: 1000000 },
  { id: '00000000-0000-0000-0000-000000000002', shop_id: '00000000-0000-0000-0000-000000000001', sku: 'BREAD-700', name: 'Bread loaf', unit_price_cents: 180, stock_qty: 11, unit_cost_micros: 1200000 },
  { id: '00000000-0000-0000-0000-000000000003', shop_id: '00000000-0000-0000-0000-000000000001', sku: 'SUGAR-1KG', name: 'Sugar 1kg', unit_price_cents: 240, stock_qty: 7, unit_cost_micros: 1800000 },
  { id: '00000000-0000-0000-0000-000000000004', shop_id: '00000000-0000-0000-0000-000000000001', sku: 'MILK-500', name: 'Milk 500ml', unit_price_cents: 130, stock_qty: 15, unit_cost_micros: 900000 },
  { id: '00000000-0000-0000-0000-000000000005', shop_id: '00000000-0000-0000-0000-000000000001', sku: 'CHIPS-100', name: 'Potato chips', unit_price_cents: 100, stock_qty: 23, unit_cost_micros: 600000 },
  { id: '00000000-0000-0000-0000-000000000006', shop_id: '00000000-0000-0000-0000-000000000001', sku: 'SOAP-175', name: 'Bath soap', unit_price_cents: 220, stock_qty: 5, unit_cost_micros: 1500000 },
]

const CONFIG_KEY = 'street-ceo-api-config'

export type ApiConfig = { baseUrl: string; shopId: string }

export function getApiConfig(): ApiConfig {
  const environment = { baseUrl: import.meta.env.VITE_API_BASE_URL, shopId: import.meta.env.VITE_SHOP_ID }
  try {
    const config = resolveShopConnection(JSON.parse(localStorage.getItem(CONFIG_KEY) ?? 'null'), environment)
    return { ...config, baseUrl: normalizeApiBaseUrl(config.baseUrl) }
  } catch {
    const fallback = resolveShopConnection(null, environment)
    return { ...fallback, baseUrl: normalizeApiBaseUrl(fallback.baseUrl) }
  }
}

export function saveApiConfig(config: ApiConfig): void {
  const normalized = { baseUrl: validateApiBaseUrl(config.baseUrl), shopId: config.shopId.trim() }
  const error = shopConfigurationError(normalized)
  if (error) throw new Error(error)
  localStorage.setItem(CONFIG_KEY, JSON.stringify(normalized))
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const config = getApiConfig()
  const response = await fetch(`${config.baseUrl}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', 'X-Shop-ID': config.shopId, ...(init?.headers ?? {}) },
  })
  if (!response.ok) throw new Error(`API request failed (${response.status})`)
  return response.json() as Promise<T>
}

export const costsApi = createCostsClient(() => {
  const config = getApiConfig()
  const error = shopConfigurationError(config)
  if (error) throw new Error(error)
  return config
})

export const retailApi = createRetailClient(() => {
  const config = getApiConfig(), error = shopConfigurationError(config)
  if (error) throw new Error(error)
  return config
})

export const productCostsApi = createProductCostsClient(() => {
  const config = getApiConfig(), error = shopConfigurationError(config)
  if (error) throw new Error(error)
  return config
})

/** The only network boundary used by screens. Fambai can later decorate this with sync. */
export const apiClient = {
  askMuse(question: string, signal?: AbortSignal) {
    return requestMuse(getApiConfig(), question, signal)
  },
  async listProducts(): Promise<{ products: Product[]; isDemo: boolean }> {
    const config = getApiConfig()
    if (!config.baseUrl) return { products: demoProducts, isDemo: true }
    try {
      return { products: await request<Product[]>(`/shops/${config.shopId}/products`), isDemo: false }
    } catch {
      return { products: demoProducts, isDemo: true }
    }
  },
  async createSale(payload: SaleRequest, idempotencyKey: string): Promise<Sale> {
    return requestSale(getApiConfig(), payload, idempotencyKey)
  },
  async getSummary(): Promise<ShopSummary | null> {
    const config = getApiConfig()
    if (!config.baseUrl) return null
    try { return await request<ShopSummary>(`/shops/${config.shopId}/summary`) } catch { return null }
  },
  async listSales(): Promise<Sale[]> {
    const config = getApiConfig()
    if (!config.baseUrl) throw new Error('Connect the shop to load transactions.')
    return request<Sale[]>(`/shops/${config.shopId}/sales`)
  },

}

export function formatMoney(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`
}
