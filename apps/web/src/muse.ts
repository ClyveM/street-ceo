/** Contract verified against services/api/app.py: MuseAskRequest/MuseAskResponse. */
// Confirmed in InMemoryStore.seed_demo_shop() and Hwaro's W3-MUSE-SHOP-001 handoff.
export const DEMO_SHOP_ID = '00000000-0000-0000-0000-000000000001'
export type ShopConnection = { baseUrl: string; shopId: string }

/** Upgrade only the retired, known APK demo connection. Custom shops and browsers stay unchanged. */
export function migrateKnownDemoConnection(storage: Pick<Storage, 'getItem' | 'setItem'>, bundled: Partial<ShopConnection>, nativeAndroid: boolean): string | null {
  if (!nativeAndroid || bundled.baseUrl?.trim().replace(/\/$/, '') !== 'http://192.168.10.213:8001' || (bundled.shopId ?? DEMO_SHOP_ID).trim() !== DEMO_SHOP_ID) return null
  let saved: unknown
  try { saved = JSON.parse(storage.getItem('street-ceo-api-config') ?? 'null') } catch { return null }
  if (!saved || typeof saved !== 'object' || Array.isArray(saved)) return null
  const config = saved as Record<string, unknown>
  if (typeof config.baseUrl !== 'string' || config.baseUrl.trim().replace(/\/$/, '') !== 'http://192.168.10.213:8000' || typeof config.shopId !== 'string' || config.shopId.trim() !== DEMO_SHOP_ID) return null
  try { storage.setItem('street-ceo-api-config', JSON.stringify({ ...config, baseUrl: 'http://192.168.10.213:8001' })) }
  catch { return 'The saved demo connection could not be updated. Open Profile → Shop Connection and use port 8001.' }
  return 'Demo connection updated to the current local server on port 8001. Your shop and other saved settings were preserved.'
}

export function resolveShopConnection(stored: unknown, environment: Partial<ShopConnection> = {}): ShopConnection {
  const saved = stored && typeof stored === 'object' && !Array.isArray(stored) ? stored as Record<string, unknown> : {}
  return {
    baseUrl: (typeof saved.baseUrl === 'string' ? saved.baseUrl : environment.baseUrl ?? '').trim(),
    shopId: (typeof saved.shopId === 'string' ? saved.shopId : environment.shopId ?? DEMO_SHOP_ID).trim(),
  }
}

export function shopConfigurationError(config: ShopConnection): string | null {
  if (!config.baseUrl.trim()) return 'Backend address is missing. Open Shop Connection to connect your shop.'
  if (!config.shopId.trim()) return 'Shop ID is missing. Enter your shop’s ID in Shop Connection.'
  if (!/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(config.shopId.trim()) || /^0{8}(?:-0{4}){3}-0{12}$/.test(config.shopId.trim())) {
    return 'Shop ID is invalid. Enter a non-zero shop UUID in Shop Connection.'
  }
  try {
    const url = new URL(config.baseUrl.trim())
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) throw new Error()
  } catch { return 'Backend address is invalid. Enter the HTTP or HTTPS backend root in Shop Connection.' }
  return null
}

export type MuseResponse = {
  status: 'answered' | 'needs_data' | 'unavailable'
  title: string
  answer: string
  evidence_ids: string[]
  missing_data: string[]
  source: string
  confidence: number
}

export function parseMuseResponse(value: unknown): MuseResponse {
  if (!value || typeof value !== 'object') throw new Error('Muse returned an unreadable response. Please try again.')
  const data = value as Record<string, unknown>
  const strings = (v: unknown): v is string[] => Array.isArray(v) && v.every((item) => typeof item === 'string')
  if (!['answered', 'needs_data', 'unavailable'].includes(String(data.status)) ||
    typeof data.title !== 'string' || !data.title.trim() ||
    typeof data.answer !== 'string' || !data.answer.trim() ||
    typeof data.source !== 'string' || !data.source.trim() ||
    !strings(data.evidence_ids) || !strings(data.missing_data) ||
    typeof data.confidence !== 'number' || !Number.isFinite(data.confidence) || data.confidence < 0 || data.confidence > 1) {
    throw new Error('Muse returned an unreadable response. Please try again.')
  }
  return data as MuseResponse
}

/** Period comes from returned evidence, never from a guess about the question. */
export function museSourcePeriod(ids: string[]): string {
  const periods = [...new Set(ids.map((id) => /^(?:sales|transactions)-(.+)$/.exec(id)?.[1]).filter(Boolean))]
  if (!periods.length) return 'Not supplied by the service'
  return periods.map((period) => {
    if (period === 'today') return 'Today (UTC)'
    if (period === 'this_month') return 'This month (service label)'
    if (period === 'available') return 'All available records'
    const days = /^last_(\d+)_days$/.exec(period!)
    return days ? `Last ${days[1]} days (UTC)` : period
  }).join('; ')
}

export async function requestMuse(
  config: { baseUrl: string; shopId: string }, question: string,
  signal?: AbortSignal, fetcher: typeof fetch = fetch,
): Promise<MuseResponse> {
  const configurationError = shopConfigurationError(config)
  if (configurationError) throw new Error(configurationError)
  const shopId = config.shopId.trim()
  const trimmed = question.trim()
  if (!trimmed || trimmed.length > 1000) throw new Error('Enter a question of 1–1,000 characters.')
  const timeout = AbortSignal.timeout(20000)
  try {
    const response = await fetcher(`${config.baseUrl.trim().replace(/\/$/, '')}/api/v1/shops/${encodeURIComponent(shopId)}/muse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'X-Shop-ID': shopId },
      body: JSON.stringify({ question: trimmed }),
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    })
    if (!response.ok) {
      const message = response.status === 404 ? 'Ask Muse is unavailable on this backend, or the shop was not found.'
        : response.status === 403 ? 'The shop connection was rejected. Check your Shop ID.'
          : response.status === 422 ? 'Muse could not accept this question. Check it and try again.'
            : 'Muse could not answer right now. Please try again.'
      throw new Error(`${message} (${response.status})`)
    }
    return parseMuseResponse(await response.json())
  } catch (error) {
    if (timeout.aborted) throw new Error('Muse took too long to respond. Please try again.')
    if (signal?.aborted) throw error
    if (error instanceof TypeError) throw new Error('Could not reach Muse. Check your connection and try again.')
    if (error instanceof SyntaxError) throw new Error('Muse returned an unreadable response. Please try again.')
    throw error
  }
}
