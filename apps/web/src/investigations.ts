export type InvestigationEvent = { event_id: string; created_at: string; correlation_id: string; shop_id?: string; operation?: string; phase?: string; status_code?: number; model?: string; source?: string; provider_called?: boolean | null; request?: unknown; response?: unknown; error_type?: string; payload?: { truncated: true; sanitized_prefix: string } }
const record = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value)
export async function requestInvestigations(config: { baseUrl: string; shopId: string }, correlation = '', signal?: AbortSignal, fetcher: typeof fetch = fetch): Promise<InvestigationEvent[]> {
  if (!config.baseUrl || !config.shopId) throw new Error('Connect your shop to inspect requests.')
  if (correlation.length > 120 || /[\r\n]/.test(correlation)) throw new Error('Use a correlation reference of at most 120 characters.')
  const query = new URLSearchParams({ limit: '20' })
  if (correlation.trim()) query.set('correlation_id', correlation.trim())
  const response = await fetcher(`${config.baseUrl.replace(/\/$/, '')}/api/v1/shops/${encodeURIComponent(config.shopId)}/investigations/requests?${query}`, { headers: { Accept: 'application/json', 'X-Shop-ID': config.shopId }, signal })
  if (!response.ok) throw new Error(`Request history unavailable (${response.status}). Check the backend connection and try again.`)
  const result: unknown = await response.json()
  if (!record(result) || result.shop_id !== config.shopId || !Array.isArray(result.events) || result.events.length > 20 || result.events.some((event) => !record(event) || typeof event.event_id !== 'string' || !event.event_id || typeof event.created_at !== 'string' || !Number.isFinite(Date.parse(event.created_at)) || typeof event.correlation_id !== 'string' || !event.correlation_id || event.shop_id !== undefined && event.shop_id !== config.shopId || event.status_code !== undefined && (!Number.isInteger(event.status_code) || Number(event.status_code) < 100 || Number(event.status_code) > 599))) throw new Error('The request-history response could not be verified for this shop.')
  if (result.events.some((event) => ['operation', 'phase', 'model', 'source', 'error_type'].some((key) => event[key] !== undefined && typeof event[key] !== 'string') || event.provider_called != null && typeof event.provider_called !== 'boolean')) throw new Error('The request-history response contains invalid event details.')
  if (result.events.some((event) => event.payload !== undefined && (!record(event.payload) || event.payload.truncated !== true || typeof event.payload.sanitized_prefix !== 'string' || event.payload.sanitized_prefix.length > 16000))) throw new Error('The partial request payload could not be verified.')
  return result.events as InvestigationEvent[]
}
