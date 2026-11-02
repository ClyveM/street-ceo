const validDate = (value: unknown): value is string => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value

export type PurchaseLine = { product_id: string | null; sku: string | null; name: string | null; unit_price_cents: number | null; quantity: number; purchase_unit_cost_micros: number; line_total_micros: number }
export type PurchaseInput = { kind: 'invoice' | 'manual'; reference: string; purchase_date: string; actor: string; supplier: string | null; tender: 'cash' | 'bank' | 'unpaid'; notes: string; lines: PurchaseLine[]; total_cost_micros: number }
export type PurchaseRecord = PurchaseInput & { id: string; shop_id: string; status: 'draft' | 'confirmed'; created_at: string; confirmed_at: string | null }
export type PurchaseResult = { purchase_id: string; shop_id: string; status: 'confirmed'; total_cost_micros: number; lines: { product_id: string; quantity_received: number; stock_before: number; stock_after: number; purchase_unit_cost_micros: number; previous_unit_cost_micros: number | null; new_average_unit_cost_micros: number; cost_change_micros: number | null; insight: string }[]; insights: string[]; confirmed_at: string }
export type StockTakeInput = { mode: 'monthly' | 'on_demand'; count_date: string; actor: string; notes: string; lines: { product_id: string; counted_qty: number }[] }
export type StockTakeRecord = StockTakeInput & { id: string; shop_id: string; status: 'draft' | 'confirmed'; created_at: string; confirmed_at: string | null; expected_snapshot: Record<string, number> }
export type StockTakeResult = { stock_take_id: string; shop_id: string; status: 'confirmed'; adjustments: { id: string; stock_take_id: string; shop_id: string; product_id: string; expected_qty: number; counted_qty: number; adjustment_qty: number; actor: string; reason: string; recorded_at: string }[]; confirmed_at: string }
export type DayCloseInput = { business_date: string; cash_counted_cents: number; bank_card_counted_cents: number; actor: string; notes: string; confirmed: boolean }
export const closeComponentKeys = ['opening_cash_cents', 'opening_bank_card_cents', 'sales_cash_cents', 'sales_bank_card_cents', 'paid_expenses_cash_cents', 'paid_expenses_bank_card_cents', 'paid_purchases_cash_cents', 'paid_purchases_bank_card_cents', 'refunds_cash_cents', 'refunds_bank_card_cents', 'adjustments_cash_cents', 'adjustments_bank_card_cents'] as const
export type DayClosePreview = { business_date: string; expected_cash_cents: number; expected_bank_card_cents: number; shop_timezone: string; calculation_basis: 'sales_only' | 'full_recorded_movements'; warnings: string[] } & Partial<Record<typeof closeComponentKeys[number], number>>
export type DayCloseRecord = DayClosePreview & { id: string; audit_id: string; shop_id: string; cash_counted_cents: number; bank_card_counted_cents: number; cash_variance_cents: number; bank_card_variance_cents: number; actor: string; notes: string; confirmed_at: string }

export const isRecord = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value)
const integer = (value: unknown, minimum = 0): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= minimum
const nonblank = (value: unknown, max: number): value is string => typeof value === 'string' && !!value.trim() && value.length <= max
const stamp = (value: unknown) => typeof value === 'string' && Number.isFinite(Date.parse(value))
function ensure(condition: unknown, message: string): asserts condition { if (!condition) throw new Error(message) }

function samePurchase(saved: PurchaseInput, input: PurchaseInput): boolean {
  return (['kind', 'reference', 'purchase_date', 'actor', 'supplier', 'tender', 'notes', 'total_cost_micros'] as const).every((key) => saved[key] === input[key]) && saved.lines.length === input.lines.length && saved.lines.every((line, index) => (['product_id', 'sku', 'name', 'unit_price_cents', 'quantity', 'purchase_unit_cost_micros', 'line_total_micros'] as const).every((key) => line[key] === input.lines[index][key]))
}

export function costToMicros(value: string): number {
  const match = /^(\d+)(?:\.(\d{1,6}))?$/.exec(value.trim())
  if (!match) throw new Error('Enter a cost with up to six decimal places, without rounding.')
  const amount = BigInt(match[1]) * 1000000n + BigInt((match[2] ?? '').padEnd(6, '0'))
  if (amount > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error('Cost exceeds the supported range.')
  return Number(amount)
}
export function sumPurchaseLines(lines: PurchaseLine[]): number {
  const total = lines.reduce((sum, line) => sum + BigInt(line.line_total_micros), 0n)
  if (total > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error('Purchase total exceeds the supported range.')
  return Number(total)
}
export function validatePurchase(value: PurchaseInput): PurchaseInput {
  ensure(['invoice', 'manual'].includes(value.kind) && ['cash', 'bank', 'unpaid'].includes(value.tender), 'Choose the purchase source and payment status.')
  ensure(validDate(value.purchase_date) && nonblank(value.reference, 120) && nonblank(value.actor, 80), 'Enter a date, purchase reference and recorder name.')
  ensure((value.supplier === null || typeof value.supplier === 'string' && value.supplier.length <= 160) && typeof value.notes === 'string' && value.notes.length <= 500, 'Keep supplier/notes within the displayed limits.')
  ensure(Array.isArray(value.lines) && value.lines.length > 0 && value.lines.length <= 200, 'Add 1–200 purchase lines.')
  const products = new Set<string>(), skus = new Set<string>()
  for (const line of value.lines) {
    ensure(integer(line.quantity, 1) && line.quantity <= 1000000 && integer(line.purchase_unit_cost_micros) && integer(line.line_total_micros), 'Each line needs whole base units and a valid cost.')
    ensure(BigInt(line.quantity) * BigInt(line.purchase_unit_cost_micros) === BigInt(line.line_total_micros), 'Line total must equal quantity multiplied by unit cost.')
    if (line.product_id) { ensure(!products.has(line.product_id), 'Combine duplicate existing-product lines.'); products.add(line.product_id) }
    else {
      ensure(nonblank(line.sku, 64) && nonblank(line.name, 120) && integer(line.unit_price_cents), 'New products need a SKU, name and selling price.')
      const sku = line.sku.toLowerCase().trim(); ensure(!skus.has(sku), 'New product SKUs must be unique.'); skus.add(sku)
    }
  }
  ensure(integer(value.total_cost_micros) && value.total_cost_micros === sumPurchaseLines(value.lines), 'Review the total cost of every purchase line.')
  ensure(value.tender === 'unpaid' || value.total_cost_micros % 10000 === 0, 'A paid purchase total must have at most two decimal places. Review the unit costs and quantities; no payment amount will be silently rounded.')
  return value
}
export function validateStockTake(value: StockTakeInput): StockTakeInput {
  ensure(['monthly', 'on_demand'].includes(value.mode) && validDate(value.count_date) && nonblank(value.actor, 80), 'Choose count mode, date and recorder.')
  ensure(typeof value.notes === 'string' && value.notes.length <= 500, 'Keep count notes to 500 characters.')
  ensure(Array.isArray(value.lines) && value.lines.length > 0 && value.lines.length <= 500, 'Enter 1–500 product counts. Blank counts are not zero.')
  const ids = new Set<string>()
  for (const line of value.lines) { ensure(nonblank(line.product_id, 100) && integer(line.counted_qty) && !ids.has(line.product_id), 'Enter a whole non-negative count once per product.'); ids.add(line.product_id) }
  return value
}
export function parsePurchase(value: unknown, shopId: string): PurchaseRecord {
  ensure(isRecord(value) && nonblank(value.id, 100) && value.shop_id === shopId && ['draft', 'confirmed'].includes(String(value.status)) && stamp(value.created_at) && (value.confirmed_at === null || stamp(value.confirmed_at)), 'Unreadable purchase receipt. Check its saved state before retrying.')
  validatePurchase(value as unknown as PurchaseInput)
  return value as unknown as PurchaseRecord
}
export function parseStockTake(value: unknown, shopId: string): StockTakeRecord {
  ensure(isRecord(value) && nonblank(value.id, 100) && value.shop_id === shopId && ['draft', 'confirmed'].includes(String(value.status)) && stamp(value.created_at) && (value.confirmed_at === null || stamp(value.confirmed_at)), 'Unreadable count receipt. Check saved state before retrying.')
  validateStockTake(value as unknown as StockTakeInput)
  ensure(isRecord(value.expected_snapshot) && (value.lines as StockTakeInput['lines']).every((line) => integer((value.expected_snapshot as Record<string, unknown>)[line.product_id])), 'Stock count is missing its verified comparison baseline.')
  return value as unknown as StockTakeRecord
}

export function parseClosePreview(value: unknown, date: string): DayClosePreview {
  ensure(isRecord(value) && value.business_date === date && ['sales_only', 'full_recorded_movements'].includes(String(value.calculation_basis)) && Number.isSafeInteger(value.expected_cash_cents) && Number.isSafeInteger(value.expected_bank_card_cents) && nonblank(value.shop_timezone, 100) && Array.isArray(value.warnings) && value.warnings.every((warning) => typeof warning === 'string'), 'Unreadable closing comparison. No close has been confirmed.')
  if (value.calculation_basis === 'full_recorded_movements') {
    ensure(closeComponentKeys.every((key) => Number.isSafeInteger(value[key]) && (key.startsWith('adjustments_') || (value[key] as number) >= 0)), 'Closing preview is missing recorded movement components.')
    for (const bucket of ['cash', 'bank_card']) {
      const n = (prefix: string) => BigInt(value[`${prefix}_${bucket}_cents`] as number)
      ensure(n('opening') + n('sales') - n('paid_expenses') - n('paid_purchases') - n('refunds') + n('adjustments') === BigInt(value[`expected_${bucket}_cents`] as number), 'Closing totals do not reconcile to recorded movements.')
    }
  }
  return value as unknown as DayClosePreview
}

/** These paths are source-verified; confirmation UI is gated separately by review readiness. */
export function createRetailClient(getConfig: () => { baseUrl: string; shopId: string }, fetcher: typeof fetch = fetch) {
  const call = async (path: string, input?: unknown, headers: Record<string, string> = {}) => {
    const config = getConfig()
    ensure(config.baseUrl && config.shopId, 'Connect your shop before using retail controls.')
    try {
      const response = await fetcher(`${config.baseUrl.replace(/\/$/, '')}/api/v1/shops/${encodeURIComponent(config.shopId)}${path}`, { method: input === undefined ? 'GET' : 'POST', headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'X-Shop-ID': config.shopId, ...headers }, body: input === undefined ? undefined : JSON.stringify(input), signal: AbortSignal.timeout(20000) })
      if (!response.ok) throw new Error(response.status === 404 || response.status === 405 ? `This shop or retail operation is unavailable (${response.status}). Verify the shop connection and running service.` : response.status === 409 ? 'The record changed or is already confirmed (409). Reload and review before retrying.' : response.status === 422 ? 'The service rejected these details (422). Check every line, date and amount.' : `Retail operation failed (${response.status}).`)
      return { value: await response.json() as unknown, shopId: config.shopId }
    } catch (error) {
      if (error instanceof TypeError || error instanceof SyntaxError || error instanceof Error && ['TimeoutError', 'AbortError'].includes(error.name)) throw new Error('Outcome unconfirmed. Your input is kept. Reload the saved record before retrying; do not post a duplicate.')
      throw error
    }
  }
  return {
    async createPurchase(input: PurchaseInput) { validatePurchase(input); const { value, shopId } = await call('/purchases', input); const saved = parsePurchase(value, shopId); ensure(saved.status === 'draft' && samePurchase(saved, input), 'Saved purchase differs from your review. Reload before confirming.'); return saved },
    async getPurchase(id: string) { const { value, shopId } = await call(`/purchases/${encodeURIComponent(id)}`); const saved = parsePurchase(value, shopId); ensure(saved.id === id, 'Wrong purchase receipt.'); return saved },
    async confirmPurchase(draft: PurchaseRecord): Promise<PurchaseResult> {
      ensure(draft.status === 'draft', 'Only an unconfirmed reviewed purchase can be confirmed.')
      const { value, shopId } = await call(`/purchases/${encodeURIComponent(draft.id)}/confirm`, {})
      ensure(isRecord(value) && value.purchase_id === draft.id && value.shop_id === shopId && value.status === 'confirmed' && value.total_cost_micros === draft.total_cost_micros && stamp(value.confirmed_at) && Array.isArray(value.insights) && value.insights.every((item) => typeof item === 'string') && Array.isArray(value.lines) && value.lines.length === draft.lines.length, 'Unreadable purchase confirmation. Reload before retrying.')
      for (const line of value.lines) ensure(isRecord(line) && nonblank(line.product_id, 100) && integer(line.quantity_received, 1) && integer(line.stock_before) && integer(line.stock_after) && line.stock_after === line.stock_before + line.quantity_received && integer(line.new_average_unit_cost_micros) && integer(line.purchase_unit_cost_micros) && ['baseline_established', 'cost_increased', 'cost_decreased', 'cost_unchanged'].includes(String(line.insight)), 'Unreadable cost/stock result. Reload the purchase.')
      for (let index = 0; index < draft.lines.length; index++) { const line = value.lines[index] as PurchaseResult['lines'][number], expected = draft.lines[index]; ensure(line.quantity_received === expected.quantity && line.purchase_unit_cost_micros === expected.purchase_unit_cost_micros && (!expected.product_id || line.product_id === expected.product_id), 'Confirmation lines differ from the saved purchase. Reload before retrying.') }
      return value as unknown as PurchaseResult
    },
    async createStockTake(input: StockTakeInput) { validateStockTake(input); const { value, shopId } = await call('/stock-takes', input); const saved = parseStockTake(value, shopId); ensure(saved.status === 'draft' && JSON.stringify(saved.lines) === JSON.stringify(input.lines) && saved.count_date === input.count_date && saved.mode === input.mode, 'Saved count differs from your review.'); return saved },
    async getStockTake(id: string) { const { value, shopId } = await call(`/stock-takes/${encodeURIComponent(id)}`); const saved = parseStockTake(value, shopId); ensure(saved.id === id, 'Wrong stock count receipt.'); return saved },
    async confirmStockTake(draft: StockTakeRecord): Promise<StockTakeResult> {
      ensure(draft.status === 'draft', 'Only a reviewed count draft can be confirmed.')
      const { value, shopId } = await call(`/stock-takes/${encodeURIComponent(draft.id)}/confirm`, {})
      ensure(isRecord(value) && value.shop_id === shopId && value.stock_take_id === draft.id && value.status === 'confirmed' && stamp(value.confirmed_at) && Array.isArray(value.adjustments), 'Unreadable count confirmation. Reload before retrying.')
      const expectedChanges = draft.lines.filter((line) => line.counted_qty !== draft.expected_snapshot[line.product_id])
      ensure(value.adjustments.length === expectedChanges.length, 'Stock adjustments differ from the reviewed count.')
      for (const item of value.adjustments) {
        ensure(isRecord(item) && item.shop_id === shopId && item.stock_take_id === draft.id && nonblank(item.id, 100) && nonblank(item.product_id, 100) && stamp(item.recorded_at), 'Unreadable stock adjustment audit.')
        const line = expectedChanges.find((line) => line.product_id === item.product_id)
        ensure(line && item.counted_qty === line.counted_qty && item.expected_qty === draft.expected_snapshot[line.product_id] && item.adjustment_qty === line.counted_qty - draft.expected_snapshot[line.product_id], 'Stock adjustment differs from the reviewed baseline.')
      }
      return value as unknown as StockTakeResult
    },
    async previewDayClose(date: string) { ensure(validDate(date), 'Choose a valid comparison date.'); const { value } = await call(`/day-close/preview?business_date=${encodeURIComponent(date)}`); return parseClosePreview(value, date) },
    async confirmDayClose(input: DayCloseInput, key: string): Promise<DayCloseRecord> {
      ensure(input.confirmed === true && validDate(input.business_date) && integer(input.cash_counted_cents) && integer(input.bank_card_counted_cents) && nonblank(input.actor, 80) && typeof input.notes === 'string' && input.notes.length <= 500 && nonblank(key, 200), 'Review actual counts and explicitly confirm the close.')
      const { value, shopId } = await call('/day-close', input, { 'Idempotency-Key': key })
      const preview = parseClosePreview(value, input.business_date)
      ensure(preview.calculation_basis === 'full_recorded_movements' && isRecord(value) && value.shop_id === shopId && nonblank(value.id, 100) && nonblank(value.audit_id, 100) && stamp(value.confirmed_at) && value.actor === input.actor && value.notes === input.notes && value.cash_counted_cents === input.cash_counted_cents && value.bank_card_counted_cents === input.bank_card_counted_cents && value.cash_variance_cents === input.cash_counted_cents - preview.expected_cash_cents && value.bank_card_variance_cents === input.bank_card_counted_cents - preview.expected_bank_card_cents, 'Closing receipt is unverified. Retry only with the original reference to recover its outcome.')
      return value as unknown as DayCloseRecord
    },
  }
}
