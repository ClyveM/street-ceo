export type ShopReachability = { status: 'connected' | 'unavailable'; checkedAt: number; address: string; detail: string; currency?: string }
export function localShopGuidance(address: string): string {
  try {
    const host = new URL(address).hostname
    if (/^(?:192\.168\.|10\.|172\.(?:1[6-9]|2\d|3[01])\.)/.test(host)) return 'This is a local-network address. Use a network that can reach the shop PC; mobile data alone may not reach it. Keep the PC and demo server running.'
  } catch { /* Invalid addresses are reported by the connection check. */ }
  return 'Check the shop server address and that this device can reach it.'
}
export async function checkShopReachability(config: { baseUrl: string; shopId: string }, signal?: AbortSignal, fetcher: typeof fetch = fetch): Promise<ShopReachability> {
  let address = config.baseUrl.trim().replace(/\/$/, '')
  try { const url = new URL(address); if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || !config.shopId.trim()) throw new Error() }
  catch { return { status: 'unavailable', checkedAt: Date.now(), address: 'Invalid or missing shop connection', detail: 'Open Profile → Shop Connection and check the backend address and shop ID.' } }
  const controller = new AbortController(), cancel = () => controller.abort()
  signal?.addEventListener('abort', cancel, { once: true }); if (signal?.aborted) cancel()
  const timer = setTimeout(cancel, 5000)
  try {
    // Unique query keys also prevent an older installed worker from replaying a cached probe.
    const probe = `connection_check=${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
    const [ready, shop] = await Promise.all([
      fetcher(`${address}/readyz?${probe}`, { cache: 'no-store', headers: { Accept: 'application/json' }, signal: controller.signal }),
      fetcher(`${address}/shops/${encodeURIComponent(config.shopId)}?${probe}`, { cache: 'no-store', headers: { Accept: 'application/json', 'X-Shop-ID': config.shopId }, signal: controller.signal }),
    ])
    if (!ready.ok) throw new Error(`The shop server is not ready (${ready.status}).`)
    if (!shop.ok) throw new Error(`The configured shop is unavailable (${shop.status}).`)
    const [readiness, record] = await Promise.all([ready.json(), shop.json()])
    if (readiness?.status !== 'ready' || record?.id !== config.shopId) throw new Error('The server did not verify the configured shop.')
    return { currency: typeof record.currency === 'string' && /^[A-Z]{3}$/.test(record.currency) ? record.currency : undefined, status: 'connected', checkedAt: Date.now(), address, detail: 'Readiness and this shop were verified from this device. A completed receipt still confirms each sale.' }
  } catch (failure) {
    const detail = failure instanceof Error && /^(The shop server|The configured shop|The server did not)/.test(failure.message) ? failure.message : 'Could not verify this shop from this device. A network indicator alone does not confirm access to the shop server.'
    return { status: 'unavailable', checkedAt: Date.now(), address, detail }
  } finally { clearTimeout(timer); controller.abort(); signal?.removeEventListener('abort', cancel) }
}
