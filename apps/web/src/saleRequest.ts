import type { Sale, SaleRequest } from './api'

export class SaleRequestError extends Error {
  uncertain: boolean
  constructor(message: string, uncertain = false) { super(message); this.name = 'SaleRequestError'; this.uncertain = uncertain }
}

/** One logical sale keeps its caller-owned key across an uncertain retry. */
export async function requestSale(config: { baseUrl: string; shopId: string }, input: SaleRequest, key: string, fetcher: typeof fetch = fetch): Promise<Sale> {
  if (!config.baseUrl || !config.shopId || !key.trim() || !['cash', 'bank'].includes(input.tender) || input.amount_received_cents !== undefined && (!Number.isSafeInteger(input.amount_received_cents) || input.amount_received_cents < 0) || !input.lines.length || new Set(input.lines.map((line) => line.product_id)).size !== input.lines.length || input.lines.some((line) => !line.product_id || !Number.isSafeInteger(line.quantity) || line.quantity <= 0)) throw new SaleRequestError('Review the shop, products, quantities and Cash/Bank tender before confirming.')
  let value: unknown
  try {
    const response = await fetcher(`${config.baseUrl.replace(/\/$/, '')}/shops/${encodeURIComponent(config.shopId)}/sales`, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'X-Shop-ID': config.shopId, 'Idempotency-Key': key }, body: JSON.stringify(input), signal: AbortSignal.timeout(20000) })
    if (!response.ok) {
      if (response.status >= 500) throw new SaleRequestError('Sale outcome is unknown. Recover the original request before starting another sale.', true)
      const payload: unknown = await response.json().catch(() => null)
      const detail = payload && typeof payload === 'object' && 'detail' in payload ? payload.detail : null
      const message = detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string' ? detail.message : null
      throw new SaleRequestError(message ?? (response.status === 409 ? 'Sale conflict (409). Check stock and saved transactions before retrying.' : `Sale was not confirmed (${response.status}). Check the shop connection and details.`))
    }
    value = await response.json()
  } catch (failure) {
    if (failure instanceof TypeError || failure instanceof SyntaxError || failure instanceof Error && ['TimeoutError', 'AbortError'].includes(failure.name)) throw new SaleRequestError('Sale outcome is unknown. Recover the original request before starting another sale.', true)
    throw failure
  }
  const sale = value as Sale | null
  if (!sale || typeof sale.id !== 'string' || !sale.id.trim() || sale.shop_id !== config.shopId || sale.tender !== input.tender || !Number.isSafeInteger(sale.total_cents) || sale.total_cents < 0 || !Number.isFinite(Date.parse(sale.created_at)) || !Array.isArray(sale.lines) || sale.lines.length !== input.lines.length || sale.lines.some((line) => !line || typeof line.product_id !== 'string' || !Number.isSafeInteger(line.quantity)) || !sale.stock_after || typeof sale.stock_after !== 'object' || Array.isArray(sale.stock_after) || input.lines.some((line) => !sale.lines.some((item) => item.product_id === line.product_id && item.quantity === line.quantity) || !Number.isSafeInteger(sale.stock_after[line.product_id]) || sale.stock_after[line.product_id] < 0)) throw new SaleRequestError('Unreadable sale receipt. Recover the original request; your basket is kept.', true)
  if (input.amount_received_cents !== undefined && (sale.amount_received_cents !== input.amount_received_cents || !Number.isSafeInteger(sale.change_cents) || sale.amount_received_cents < sale.total_cents || sale.change_cents !== (input.tender === 'cash' ? sale.amount_received_cents - sale.total_cents : 0))) throw new SaleRequestError('Receipt payment amounts could not be verified. Recover the original request.', true)
  if (sale.change_cents !== undefined && (!Number.isSafeInteger(sale.change_cents) || sale.change_cents < 0 || input.tender === 'bank' && sale.change_cents !== 0) || sale.amount_received_cents != null && (!Number.isSafeInteger(sale.amount_received_cents) || sale.amount_received_cents < sale.total_cents || sale.change_cents !== sale.amount_received_cents - sale.total_cents)) throw new SaleRequestError('Receipt payment amounts could not be verified. Recover the original request.', true)
  return sale
}
