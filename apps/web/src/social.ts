export type ShopImageMetadata = { filename: string; content_type: string; size_bytes: number }
export type SocialBriefRequest = { product_ids: string[]; shop_image?: ShopImageMetadata | null }
export type SocialBrief = { shop_id: string; catalogue_source: 'repository'; created_at: string; shop_image?: ShopImageMetadata | null; products: { product_id: string; sku: string; name: string; unit_price_cents: number; stock_qty: number }[] }
export type SocialImageRequest = { product_ids: string[]; brief: string; aspect_ratio: '1:1' | '4:5' | '9:16' | '16:9'; source_image_id?: string; shop_photo_data?: string }
export type SocialImageResult = Omit<SocialImageRequest, 'source_image_id' | 'shop_photo_data'> & { id: string; shop_id: string; source_image_id?: string | null; status: 'draft' | 'provider_not_configured' | 'unavailable'; provider: string; model: string | null; image_refs: string[]; warnings: string[]; draft_only: true; output_url: string | null; created_at: string }
export type SocialDraftResult = { id: string; shop_id: string; title: string; caption: string; voiceover_script: string; shot_list: string[]; selected_product_ids: string[]; claims: { product_id: string; claim: string; source_field: string }[]; status: 'draft' | 'unavailable'; source: 'provider' | 'fallback'; provider: string; model: string | null; warnings: string[]; draft_only: true; created_at: string }
const stringList = (value: unknown): value is string[] => Array.isArray(value) && value.every((item) => typeof item === 'string')
export function previewImageRef(value: string | null): string | null {
  if (!value) return null
  if (/^data:image\/(?:png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(value) && value.length <= 16 * 1024 * 1024) return value
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? value : null } catch { return null }
}
export function parseSocialDraft(value: unknown, shopId: string, selected: string[]): SocialDraftResult {
  if (!value || typeof value !== 'object') throw new Error('Unreadable social-draft response.')
  const data = value as SocialDraftResult
  if (data.shop_id !== shopId || typeof data.id !== 'string' || !data.id || data.draft_only !== true || !['draft', 'unavailable'].includes(data.status) || !['provider', 'fallback'].includes(data.source) || typeof data.provider !== 'string' || !(data.model === null || typeof data.model === 'string') || typeof data.title !== 'string' || typeof data.caption !== 'string' || typeof data.voiceover_script !== 'string' || !stringList(data.shot_list) || !stringList(data.warnings) || !stringList(data.selected_product_ids) || new Set(data.selected_product_ids).size !== data.selected_product_ids.length || data.selected_product_ids.some((id) => !selected.includes(id)) || !Array.isArray(data.claims) || data.claims.length > 20 || data.claims.some((claim) => !claim || !selected.includes(claim.product_id) || typeof claim.claim !== 'string' || !['name', 'sku', 'price_minor'].includes(claim.source_field)) || typeof data.created_at !== 'string' || !Number.isFinite(Date.parse(data.created_at)) || (data.status === 'draft' && (data.source !== 'provider' || !data.selected_product_ids.length || !data.caption.trim()))) throw new Error('Unreadable social-draft response.')
  return data
}
export async function requestSocialDraft(config: { baseUrl: string; shopId: string }, payload: { product_ids: string[]; brief: string; source_image_id?: string; duration_seconds?: number }, signal?: AbortSignal, fetcher: typeof fetch = fetch): Promise<SocialDraftResult> {
  selection(payload.product_ids)
  const clean = { ...payload, brief: payload.brief.trim(), duration_seconds: payload.duration_seconds ?? 40 }
  if (!clean.brief || clean.brief.length > 1000 || !Number.isInteger(clean.duration_seconds) || clean.duration_seconds < 1 || clean.duration_seconds > 120) throw new Error('Enter a brief of 1–1,000 characters and a duration up to 120 seconds.')
  return parseSocialDraft(await post(config, 'draft', clean, signal, fetcher), config.shopId, clean.product_ids)
}

function selection(ids: string[]) {
  if (!ids.length || ids.length > 12 || new Set(ids).size !== ids.length) throw new Error('Choose 1–12 different shop products.')
}
async function post(config: { baseUrl: string; shopId: string }, suffix: string, payload: unknown, signal?: AbortSignal, fetcher: typeof fetch = fetch): Promise<unknown> {
  if (!config.baseUrl || !config.shopId) throw new Error('Connect your shop before preparing a social update.')
  try {
    const timeout = AbortSignal.timeout(suffix === 'image-generation' ? 90000 : suffix === 'draft' ? 80000 : 10000)
    const response = await fetcher(`${config.baseUrl.replace(/\/$/, '')}/api/v1/shops/${encodeURIComponent(config.shopId)}/social/${suffix}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'X-Shop-ID': config.shopId }, body: JSON.stringify(payload), signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    })
    if (!response.ok) throw new Error(response.status === 404 ? 'This social service, shop, product, or image is unavailable (404). Check the shop connection and backend version.' : `Social request failed (${response.status}). Your selections are kept.`)
    return await response.json()
  } catch (error) {
    if (signal?.aborted) throw error
    if (error instanceof Error && error.name === 'TimeoutError') throw new Error('The draft request took too long. Your selections are kept. Try again.')
    if (error instanceof TypeError) throw new Error('Could not reach the social service. Check your connection and try again.')
    if (error instanceof SyntaxError) throw new Error('The social service returned an unreadable response.')
    throw error
  }
}
export function parseSocialBrief(value: unknown, shopId: string, selected: string[]): SocialBrief {
  if (!value || typeof value !== 'object') throw new Error('Unreadable catalogue verification response.')
  const data = value as SocialBrief
  if (data.shop_id !== shopId || data.catalogue_source !== 'repository' || typeof data.created_at !== 'string' || !Number.isFinite(Date.parse(data.created_at)) || !Array.isArray(data.products) || data.products.length !== selected.length ||
    new Set(data.products.map((item) => item?.product_id)).size !== selected.length || data.products.some((item) => !item || !selected.includes(item.product_id) || typeof item.name !== 'string' || typeof item.sku !== 'string' || !Number.isInteger(item.unit_price_cents) || item.unit_price_cents < 0 || !Number.isInteger(item.stock_qty) || item.stock_qty < 0)) throw new Error('Unreadable catalogue verification response.')
  return data
}
export async function requestSocialBrief(config: { baseUrl: string; shopId: string }, payload: SocialBriefRequest, signal?: AbortSignal, fetcher: typeof fetch = fetch): Promise<SocialBrief> {
  selection(payload.product_ids)
  return parseSocialBrief(await post(config, 'brief', payload, signal, fetcher), config.shopId, payload.product_ids)
}
export function parseSocialImageResult(value: unknown, shopId: string, payload: SocialImageRequest): SocialImageResult {
  if (!value || typeof value !== 'object') throw new Error('Unreadable image-generation response.')
  const data = value as SocialImageResult
  if (data.shop_id !== shopId || typeof data.id !== 'string' || !data.id || !Array.isArray(data.product_ids) || data.product_ids.length !== payload.product_ids.length || new Set(data.product_ids).size !== payload.product_ids.length || data.product_ids.some((id) => !payload.product_ids.includes(id)) ||
    (data.source_image_id ?? null) !== (payload.source_image_id ?? null) || data.brief !== payload.brief || data.aspect_ratio !== payload.aspect_ratio || !['draft', 'provider_not_configured', 'unavailable'].includes(data.status) || typeof data.provider !== 'string' || !(data.model === null || typeof data.model === 'string') || !stringList(data.image_refs) || !stringList(data.warnings) || data.draft_only !== true || !(data.output_url === null || typeof data.output_url === 'string') || (data.status === 'draft' ? !data.image_refs.length || data.output_url !== data.image_refs[0] : data.image_refs.length !== 0 || data.output_url !== null) || typeof data.created_at !== 'string' || !Number.isFinite(Date.parse(data.created_at))) throw new Error('Unreadable image-generation response.')
  return data
}
export async function requestSocialImage(config: { baseUrl: string; shopId: string }, payload: SocialImageRequest, signal?: AbortSignal, fetcher: typeof fetch = fetch): Promise<SocialImageResult> {
  selection(payload.product_ids)
  const trimmed = { ...payload, brief: payload.brief.trim() }
  if (!trimmed.brief || trimmed.brief.length > 1000) throw new Error('Enter an image request of 1–1,000 characters.')
  if (!['1:1', '4:5', '9:16', '16:9'].includes(trimmed.aspect_ratio)) throw new Error('Choose a supported image aspect ratio.')
  return parseSocialImageResult(await post(config, 'image-generation', trimmed, signal, fetcher), config.shopId, trimmed)
}
