/** Verified contract: services/api/costs.py ProductCostCorrectionCreate/Correction. */
export type CostCorrectionInput = { unit_cost_micros: number; effective_date: string; reason: string; source_ref: string; actor: string }
export type CostCorrection = CostCorrectionInput & { id: string; shop_id: string; product_id: string; status: 'draft' | 'confirmed'; created_at: string; confirmed_at: string | null }
type Config = { baseUrl: string; shopId: string }
const object = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value)
const text = (value: unknown): value is string => typeof value === 'string' && !!value.trim()
const stamp = (value: unknown) => typeof value === 'string' && Number.isFinite(Date.parse(value))

export function costInput(amount: string, effectiveDate: string, reason: string, source: string, actor: string): CostCorrectionInput {
  if (!/^\d+(?:\.\d{1,6})?$/.test(amount.trim())) throw new Error('Enter a non-negative cost with up to six decimal places.')
  const [whole, fraction = ''] = amount.trim().split('.')
  const micros = BigInt(whole) * 1000000n + BigInt(fraction.padEnd(6, '0'))
  if (micros > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error('Cost exceeds the supported range.')
  if (!/^\d{4}-\d{2}-\d{2}$/.test(effectiveDate) || !Number.isFinite(Date.parse(effectiveDate)) || new Date(effectiveDate).toISOString().slice(0, 10) !== effectiveDate) throw new Error('Choose a valid effective date.')
  for (const [value, limit, name] of [[reason, 500, 'reason'], [source, 240, 'source reference'], [actor, 80, 'recorder']] as const) {
    if (!value.trim() || value.trim().length > limit) throw new Error(`Provide a ${name} within ${limit} characters.`)
  }
  return { unit_cost_micros: Number(micros), effective_date: effectiveDate, reason: reason.trim(), source_ref: source.trim(), actor: actor.trim() }
}

export function parseCostCorrection(value: unknown, config: Config, productId: string): CostCorrection {
  if (!object(value) || !text(value.id) || value.shop_id !== config.shopId || value.product_id !== productId || !Number.isSafeInteger(value.unit_cost_micros) || Number(value.unit_cost_micros) < 0 || !['draft', 'confirmed'].includes(String(value.status)) || !stamp(value.created_at) || !(value.confirmed_at === null || stamp(value.confirmed_at)) || (value.status === 'confirmed' && !stamp(value.confirmed_at))) throw new Error('Unreadable cost receipt. Check product cost history before retrying.')
  if (![value.reason, value.source_ref, value.actor, value.effective_date].every(text)) throw new Error('Cost receipt is missing its source details.')
  return value as unknown as CostCorrection
}

export function createProductCostsClient(getConfig: () => Config, fetcher: typeof fetch = fetch) {
  const call = async (productId: string, suffix: string, init?: RequestInit) => {
    const config = getConfig()
    if (!config.baseUrl || !config.shopId || !productId) throw new Error('Connect a shop and choose a product first.')
    try {
      const response = await fetcher(`${config.baseUrl.replace(/\/$/, '')}/api/v1/shops/${encodeURIComponent(config.shopId)}/products/${encodeURIComponent(productId)}${suffix}`, { ...init, headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'X-Shop-ID': config.shopId }, signal: AbortSignal.timeout(20000) })
      if (!response.ok) throw new Error(response.status === 404 ? 'Product cost service or record was not found (404). Check your shop connection and backend version.' : response.status === 409 ? 'Cost record is no longer a draft (409). Check cost history before retrying.' : `Cost request failed (${response.status}). Check the source and saved history.`)
      return { value: await response.json() as unknown, config }
    } catch (failure) {
      if (failure instanceof TypeError || failure instanceof SyntaxError || (failure instanceof Error && ['TimeoutError', 'AbortError'].includes(failure.name))) throw new Error('Cost request outcome is unknown. Check product cost history before retrying; no automatic retry was made.')
      throw failure
    }
  }
  return {
    async draft(productId: string, payload: CostCorrectionInput) {
      if (!Number.isSafeInteger(payload.unit_cost_micros) || payload.unit_cost_micros < 0) throw new Error('Cost must be a non-negative safe integer in micros.')
      const clean = costInput((BigInt(payload.unit_cost_micros) / 1000000n).toString() + '.' + (BigInt(payload.unit_cost_micros) % 1000000n).toString().padStart(6, '0'), payload.effective_date, payload.reason, payload.source_ref, payload.actor)
      const { value, config } = await call(productId, '/cost-corrections', { method: 'POST', body: JSON.stringify(clean) })
      const receipt = parseCostCorrection(value, config, productId)
      if (receipt.status !== 'draft' || Object.entries(clean).some(([key, expected]) => receipt[key as keyof CostCorrection] !== expected)) throw new Error('Cost receipt differs from the requested draft. Check history before retrying.')
      return receipt
    },
    async confirm(draft: CostCorrection) {
      const { value, config } = await call(draft.product_id, `/cost-corrections/${encodeURIComponent(draft.id)}/confirm`, { method: 'POST' })
      const receipt = parseCostCorrection(value, config, draft.product_id)
      if (receipt.id !== draft.id || receipt.status !== 'confirmed' || (['unit_cost_micros', 'effective_date', 'reason', 'source_ref', 'actor'] as const).some((key) => receipt[key] !== draft[key])) throw new Error('Cost confirmation differs from the reviewed draft. Check history before retrying.')
      return receipt
    },
    async history(productId: string) {
      const { value, config } = await call(productId, '/cost-history')
      if (!Array.isArray(value) || value.some((item) => !object(item) || !text(item.id) || item.shop_id !== config.shopId || item.product_id !== productId || !Number.isSafeInteger(item.new_unit_cost_micros) || Number(item.new_unit_cost_micros) < 0 || !Number.isSafeInteger(item.stock_before) || !Number.isSafeInteger(item.stock_after) || !stamp(item.recorded_at) || !text(item.source_type) || typeof item.source_ref !== 'string' || typeof item.reason !== 'string' || typeof item.actor !== 'string')) throw new Error('Unreadable product cost history.')
      return value as { id: string; new_unit_cost_micros: number; stock_before: number; stock_after: number; recorded_at: string; source_type: string; source_ref: string; reason: string; actor: string }[]
    },
  }
}
