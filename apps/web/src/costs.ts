/** Verified against services/api/costs.py and invoice/expense routes in app.py. */
export const expenseCategories = ['electricity', 'transport', 'rent', 'wages', 'airtime', 'supplies', 'other'] as const
export type ExpenseCategory = typeof expenseCategories[number]
export type InvoiceLine = { id: string; description: string; sku: string | null; quantity: number; line_total_cents: number; calculated_unit_cost_micros: number | null; suggested_product_id: string | null; matched_product_id: string | null; match_status: 'unmatched' | 'suggested' | 'accepted'; source: 'manual_review' | 'ocr_provider'; evidence_ref: string | null }
export type InvoiceRecord = { id: string; shop_id: string; filename: string; content_type: string; size_bytes: number; sha256: string; storage_backend: 'memory'; storage_ref: string; extraction_status: 'pending' | 'needs_review' | 'confirmed' | 'rejected' | 'provider_unavailable'; extraction_source: 'none' | 'ocr_provider' | 'manual_review'; lines: InvoiceLine[]; warnings: string[]; uploaded_at: string; confirmed_at: string | null }
export type InvoiceReview = { source: 'manual_review'; evidence_ref: string; lines: { description: string; sku: string | null; product_id: string | null; quantity: number; line_total_cents: number }[] }
export type InvoiceConfirmation = { invoice_id: string; shop_id: string; status: 'confirmed'; applied_line_ids: string[]; stock_units_added: number; cost_updates: number; warnings: string[]; confirmed_at: string }
export type ExpenseRequest = { category: ExpenseCategory; frequency: 'one_off' | 'recurring'; occurred_on: string; period_start: string | null; period_end: string | null; amount_cents: number; notes: string; tender: 'cash' | 'bank' | 'unpaid' }
export type ExpenseRecord = ExpenseRequest & { id: string; shop_id: string; status: 'draft' | 'confirmed' | 'rejected'; created_at: string; confirmed_at: string | null }

const record = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value)
const strings = (value: unknown): value is string[] => Array.isArray(value) && value.every((item) => typeof item === 'string')
const integer = (value: unknown, minimum = 0): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= minimum
const timestamp = (value: unknown): value is string => typeof value === 'string' && Number.isFinite(Date.parse(value))
const id = (value: unknown): value is string => typeof value === 'string' && !!value.trim()
const nullableId = (value: unknown) => value === null || id(value)

export function moneyToCents(value: string, allowZero = false): number {
  const text = value.trim()
  if (!/^\d+(?:\.\d{1,2})?$/.test(text)) throw new Error('Enter an amount with up to two decimal places.')
  const [whole, decimal = ''] = text.split('.')
  const amount = BigInt(whole) * 100n + BigInt(decimal.padEnd(2, '0'))
  if (amount > BigInt(Number.MAX_SAFE_INTEGER) || amount < (allowZero ? 0n : 1n)) throw new Error(allowZero ? 'Amount must be zero or greater and within the supported range.' : 'Amount must be greater than zero and within the supported range.')
  return Number(amount)
}
export function validDate(value: unknown): value is string {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value
}
export function validateExpense(value: ExpenseRequest): ExpenseRequest {
  if (!(expenseCategories as readonly string[]).includes(value.category) || !['one_off', 'recurring'].includes(value.frequency) || !['cash', 'bank', 'unpaid'].includes(value.tender)) throw new Error('Choose a category, frequency, and payment status.')
  if (!integer(value.amount_cents, 1)) throw new Error('Expense amount must be a positive amount in cents.')
  if (!validDate(value.occurred_on)) throw new Error('Choose a valid expense date.')
  if (value.frequency === 'one_off' && (value.period_start !== null || value.period_end !== null)) throw new Error('One-off expenses do not have a recurring period.')
  if (value.frequency === 'recurring' && (!validDate(value.period_start) || !validDate(value.period_end) || value.period_end < value.period_start)) throw new Error('Choose a recurring period with an end on or after the start.')
  if (typeof value.notes !== 'string' || value.notes.length > 500) throw new Error('Keep expense notes to 500 characters.')
  return { ...value, notes: value.notes.trim() }
}
export function parseInvoice(value: unknown, shopId: string): InvoiceRecord {
  if (!record(value) || !id(value.id) || value.shop_id !== shopId || typeof value.filename !== 'string' || !['application/pdf', 'image/jpeg', 'image/png', 'image/webp'].includes(String(value.content_type)) ||
    !integer(value.size_bytes, 1) || value.size_bytes > 10 * 1024 * 1024 || typeof value.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(value.sha256) || value.storage_backend !== 'memory' || typeof value.storage_ref !== 'string' ||
    !['pending', 'needs_review', 'confirmed', 'rejected', 'provider_unavailable'].includes(String(value.extraction_status)) || !['none', 'manual_review', 'ocr_provider'].includes(String(value.extraction_source)) ||
    !timestamp(value.uploaded_at) || !(value.confirmed_at === null || timestamp(value.confirmed_at)) || !strings(value.warnings) || !Array.isArray(value.lines)) throw new Error('Invoice response is incomplete or unreadable. Check the backend version before uploading again.')
  for (const line of value.lines) {
    if (!record(line) || !id(line.id) || typeof line.description !== 'string' || !(line.sku === null || typeof line.sku === 'string') || !integer(line.quantity, 1) || !integer(line.line_total_cents) ||
      !(line.calculated_unit_cost_micros === null || integer(line.calculated_unit_cost_micros)) || !nullableId(line.suggested_product_id) || !nullableId(line.matched_product_id) ||
      !['unmatched', 'suggested', 'accepted'].includes(String(line.match_status)) || !['manual_review', 'ocr_provider'].includes(String(line.source))) throw new Error('Invoice lines are unreadable. No costs have been confirmed by this screen.')
  }
  return value as unknown as InvoiceRecord
}
export function parseExpense(value: unknown, shopId: string): ExpenseRecord {
  if (!record(value) || value.shop_id !== shopId || !id(value.id) || !['draft', 'confirmed', 'rejected'].includes(String(value.status)) || !timestamp(value.created_at) || !(value.confirmed_at === null || timestamp(value.confirmed_at))) throw new Error('Unreadable expense receipt. Check saved records before retrying.')
  validateExpense(value as unknown as ExpenseRequest)
  return value as unknown as ExpenseRecord
}
export function validateInvoiceReview(value: InvoiceReview): InvoiceReview {
  if (value.source !== 'manual_review' || !value.evidence_ref.trim() || value.evidence_ref.length > 240 || !value.lines.length || value.lines.length > 200) throw new Error('Enter 1–200 manual invoice lines with an evidence reference.')
  for (const line of value.lines) {
    if (!line.description.trim() || line.description.length > 240 || (line.sku !== null && line.sku.length > 64) || !integer(line.quantity, 1) || line.quantity > 1000000 || !integer(line.line_total_cents)) throw new Error('Each line needs a description, whole base-unit quantity, and non-negative line total.')
  }
  return value
}
export function canConfirmInvoice(invoice: InvoiceRecord, dirty: boolean): boolean {
  return !dirty && invoice.extraction_status === 'needs_review' && invoice.lines.length > 0 && invoice.lines.every((line) => line.match_status === 'accepted' && !!line.matched_product_id && line.calculated_unit_cost_micros !== null)
}
export function invoiceReviewNotice(invoice: InvoiceRecord): string {
  if (invoice.extraction_status === 'pending') return 'Extraction is pending. Refresh the source for actual results, or enter the original document manually. No extracted lines are assumed.'
  if (invoice.extraction_source === 'ocr_provider' && invoice.lines.length) return 'Provider-supplied lines are shown below as source evidence. Check the original document and explicitly select each product in the purchase; suggestions are not accepted matches.'
  if (invoice.extraction_source === 'manual_review' && invoice.lines.length) return 'Previously entered manual lines are shown below as source evidence. Check the original document and explicitly select each product in this purchase.'
  return 'No extracted lines are available. Enter quantities and costs from the original document manually; no OCR is claimed.'
}
export async function validateInvoiceFile(file: File): Promise<void> {
  if (!['application/pdf', 'image/jpeg', 'image/png', 'image/webp'].includes(file.type)) throw new Error('Choose a PDF, JPEG, PNG, or WebP invoice.')
  if (!file.size || file.size > 10 * 1024 * 1024) throw new Error('Choose a non-empty invoice no larger than 10 MiB.')
  const bytes = new Uint8Array(await file.slice(0, 12).arrayBuffer())
  const text = String.fromCharCode(...bytes)
  const valid = file.type === 'application/pdf' ? text.startsWith('%PDF-') : file.type === 'image/jpeg' ? bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255 : file.type === 'image/png' ? [137,80,78,71,13,10,26,10].every((byte, index) => bytes[index] === byte) : text.startsWith('RIFF') && text.slice(8,12) === 'WEBP'
  if (!valid) throw new Error('Invoice contents do not match the file type.')
}
export function invoiceUploadFilename(file: File): string {
  const stem = file.name.replace(/^.*[\\/]/, '').replace(/\.[^.]*$/, '').replace(/[^A-Za-z0-9_-]/g, '_').replace(/^[_-]+/, '').slice(0,100) || 'invoice'
  return stem + (file.type === 'application/pdf' ? '.pdf' : file.type === 'image/jpeg' ? '.jpg' : file.type === 'image/png' ? '.png' : '.webp')
}

export function createCostsClient(getConfig: () => { baseUrl: string; shopId: string }, fetcher: typeof fetch = fetch) {
  const call = async (path: string, init: RequestInit = {}): Promise<{ value: unknown; shopId: string }> => {
    const config = getConfig()
    if (!config.baseUrl || !config.shopId) throw new Error('Connect your shop before using invoices or expenses.')
    try {
      const response = await fetcher(`${config.baseUrl.replace(/\/$/, '')}/api/v1/shops/${encodeURIComponent(config.shopId)}${path}`, { ...init, headers: { Accept: 'application/json', 'X-Shop-ID': config.shopId, ...(init.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }) }, signal: AbortSignal.timeout(20000) })
      if (!response.ok) throw new Error(response.status === 404 ? 'Invoice/expense service, shop, or record was not found (404). Check the backend version and shop connection.' : response.status === 405 ? 'This backend does not support the invoice/expense operation yet (405). Ask the backend owner to verify the running version.' : response.status === 409 ? 'This record changed or is not ready to confirm (409). Reload and review before retrying.' : response.status === 422 ? 'The backend rejected these inputs (422). Check amounts, dates, quantities, and product matches.' : `The backend could not complete this request (${response.status}).`)
      return { value: await response.json(), shopId: config.shopId }
    } catch (error) {
      if (error instanceof TypeError || (error instanceof Error && error.name === 'TimeoutError')) throw new Error('Could not confirm the operation. Your input is kept; check saved records before retrying.')
      if (error instanceof SyntaxError) throw new Error('Unreadable backend response. Check saved records before retrying.')
      throw error
    }
  }
  return {
    async uploadInvoice(file: File) { await validateInvoiceFile(file); const form = new FormData(); form.append('invoice', file, invoiceUploadFilename(file)); const { value, shopId } = await call('/invoices', { method: 'POST', body: form }); return parseInvoice(value, shopId) },
    async listInvoices() { const { value, shopId } = await call('/invoices'); if (!Array.isArray(value)) throw new Error('Unreadable invoice history.'); return value.map((item) => parseInvoice(item, shopId)) },
    async getInvoice(invoiceId: string) { const { value, shopId } = await call(`/invoices/${encodeURIComponent(invoiceId)}`); const invoice = parseInvoice(value, shopId); if (invoice.id !== invoiceId) throw new Error('Invoice receipt does not match the request.'); return invoice },
    async reviewInvoice(invoiceId: string, payload: InvoiceReview) { validateInvoiceReview(payload); const { value, shopId } = await call(`/invoices/${encodeURIComponent(invoiceId)}/review`, { method: 'POST', body: JSON.stringify(payload) }); const invoice = parseInvoice(value, shopId); if (invoice.id !== invoiceId) throw new Error('Invoice receipt does not match the request.'); return invoice },
    async confirmInvoice(invoiceId: string): Promise<InvoiceConfirmation> {
      const { value, shopId } = await call(`/invoices/${encodeURIComponent(invoiceId)}/confirm`, { method: 'POST' })
      if (!record(value) || value.invoice_id !== invoiceId || value.shop_id !== shopId || value.status !== 'confirmed' || !strings(value.applied_line_ids) || !integer(value.stock_units_added) || !integer(value.cost_updates) || !strings(value.warnings) || !timestamp(value.confirmed_at)) throw new Error('Unreadable confirmation receipt. Check the invoice before confirming again.')
      return value as unknown as InvoiceConfirmation
    },
    async listExpenses() { const { value, shopId } = await call('/expenses'); if (!Array.isArray(value)) throw new Error('Unreadable expense history.'); return value.map((item) => parseExpense(item, shopId)) },
    async createExpense(payload: ExpenseRequest) { const clean = validateExpense(payload); const { value, shopId } = await call('/expenses', { method: 'POST', body: JSON.stringify(clean) }); const expense = parseExpense(value, shopId); if (expense.status !== 'draft' || Object.entries(clean).some(([key, expected]) => (expense as unknown as Record<string, unknown>)[key] !== expected)) throw new Error('Expense receipt does not match the draft. Check history before retrying.'); return expense },
    async confirmExpense(expenseId: string) { const { value, shopId } = await call(`/expenses/${encodeURIComponent(expenseId)}/confirm`, { method: 'POST' }); const expense = parseExpense(value, shopId); if (expense.id !== expenseId || expense.status !== 'confirmed') throw new Error('Expense confirmation does not match the request.'); return expense },
  }
}
