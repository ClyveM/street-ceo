export type SaleMode = 'quick' | 'review'
export const SALE_MODE_KEY = 'street-ceo-sale-mode-v1'
export function readSaleMode(storage?: Pick<Storage, 'getItem'>): SaleMode { try { return storage?.getItem(SALE_MODE_KEY) === 'review' ? 'review' : 'quick' } catch { return 'quick' } }
export type QuickLine = { product_id: string; product_name: string; quantity: number }
export type PendingVoiceItem = { slot_id:number; heard:string; quantity:number|null; product_id:string|null; product_name:string|null }
export type VoiceReview = { reviewId: string; shopId: string; transcript: string; status: string; lines: QuickLine[]; canCommit: boolean; requiresMatchConfirmation?: boolean; matchConfirmed?: boolean; resolutionSource?: string; clarificationQuestion?: string; providerCalled?: boolean; retainedLines?: QuickLine[]; pendingItems?: PendingVoiceItem[] }
export type TenderAnswer = { tender: 'cash' | 'bank'; amount_received_cents?: number }
export type TenderQuestion = { kind: 'question'; status: 'needs_tender'; review_id: string; question: string; amount_due_cents: number; allowed_tenders: ('cash' | 'bank')[]; missing: string[] }
export type QuickReceipt = { id: string; shop_id: string; lines: { product_id: string; quantity: number }[]; tender: 'cash' | 'bank'; total_cents: number; amount_received_cents: number; change_cents: number; stock_after: Record<string, number>; created_at: string }
export type QuickReversal = { reversal_id: string; audit_id: string; original_sale_id: string; shop_id: string; status: 'reversed'; lines: { product_id: string; quantity: number }[]; actor: string; reason: string; created_at: string }
export class QuickSaleError extends Error {
  uncertain: boolean
  code: string
  constructor(message: string, uncertain = false, code = '') { super(message); this.name = 'QuickSaleError'; this.uncertain = uncertain; this.code = code }
}
const record = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value)
const text = (value: unknown): value is string => typeof value === 'string' && !!value.trim()
const minor = (value: unknown): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0
const instant = (value: unknown) => typeof value === 'string' && /(?:Z|[+-]\d\d:\d\d)$/i.test(value) && Number.isFinite(Date.parse(value))

const spokenQuantities: Record<string, number> = { zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12, thirteen: 13, fourteen: 14, fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18, nineteen: 19, twenty: 20 }
export function cancelPayment(value: string) { return /^(?:cancel|cancel sale|cancel basket)[.!?]*$/i.test(value.trim()) }
export function paymentCommand(value: string) { return (/^apo\b([\s\S]+?)\b(?:napo|nabo|napple|apo)[.!?]*$/i.exec(value.trim())?.[1] ?? value).trim() }
export function matchAnswer(value: string): 'yes' | 'no' | 'cancel' | null {
  const clean = paymentCommand(value).toLowerCase().trim().replace(/[.!?]+$/, '')
  if (cancelPayment(clean)) return 'cancel'
  if (/^(yes|yes please|correct)$/.test(clean)) return 'yes'
  if (clean === 'no') return 'no'
  return null
}
export function confirmVoiceMatch(review: VoiceReview): VoiceReview {
  if (review.status === 'needs_confirmation' && review.canCommit && !review.requiresMatchConfirmation && review.lines.length) return review
  if (review.status !== 'needs_match_confirmation' || !review.requiresMatchConfirmation || !review.lines.length) throw new QuickSaleError('There is no grounded product proposal to confirm.')
  return { ...review, canCommit: true, matchConfirmed: true }
}
export function catalogueMatchQuestion(review: VoiceReview) { return review.clarificationQuestion ?? `Did you mean ${review.lines.map((line) => `${line.quantity} ${line.product_name}`).join(', ')}? Say Yes, No, or Cancel.` }
export function cashAmountCents(value: string): number | null {
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(value.trim())
  if (!match) return null
  const amount = BigInt(match[1]) * 100n + BigInt((match[2] ?? '').padEnd(2, '0'))
  return amount <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(amount) : null
}
function spokenInteger(value: string): number | null {
  const clean = value.trim().replace(/-/g, ' '), tokens = clean.split(/\s+/)
  if (/^\d+$/.test(clean)) { const number = Number(clean); return Number.isSafeInteger(number) ? number : null }
  const tens: Record<string, number> = { twenty:20, thirty:30, forty:40, fifty:50, sixty:60, seventy:70, eighty:80, ninety:90 }
  let hundreds = 0
  if (tokens[1] === 'hundred' && spokenQuantities[tokens[0]] >= 1 && spokenQuantities[tokens[0]] <= 9) {
    hundreds = spokenQuantities[tokens.shift()!] * 100; tokens.shift()
    if (tokens[0] === 'and') { tokens.shift(); if (!tokens.length) return null }
    if (!tokens.length) return hundreds
  }
  if (tokens.length === 1 && spokenQuantities[tokens[0]] !== undefined) return hundreds + spokenQuantities[tokens[0]]
  if (tokens.length === 1 && tens[tokens[0]]) return hundreds + tens[tokens[0]]
  if (tokens.length === 2 && tens[tokens[0]] && spokenQuantities[tokens[1]] >= 1 && spokenQuantities[tokens[1]] <= 9) return hundreds + tens[tokens[0]] + spokenQuantities[tokens[1]]
  return null
}
export function spokenCashCents(value: string): number | null {
  const clean = value.toLowerCase().trim().replace(/\s+/g, ' ')
  const exact = cashAmountCents(clean)
  if (exact !== null) return exact
  const split = /^(.+?) dollars? (?:and )?(.+?) cents?$/.exec(clean)
  if (split) {
    const whole = spokenInteger(split[1]), cents = spokenInteger(split[2])
    if (whole === null || cents === null || cents > 99) return null
    const total = BigInt(whole) * 100n + BigInt(cents)
    return total <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(total) : null
  }
  const decimal = /^(.+?) point (.+)$/.exec(clean)
  if (decimal) {
    const whole = spokenInteger(decimal[1]), digits = decimal[2].split(' ').map((word) => /^\d$/.test(word) ? word : spokenQuantities[word] >= 0 && spokenQuantities[word] <= 9 ? String(spokenQuantities[word]) : '?').join('')
    return whole !== null && /^\d{1,2}$/.test(digits) ? cashAmountCents(`${whole}.${digits}`) : null
  }
  const centsOnly = /^(.+?) cents?$/.exec(clean)
  if (centsOnly) { const cents = spokenInteger(centsOnly[1]); return cents !== null && cents <= 99 ? cents : null }
  const integer = spokenInteger(clean.replace(/ dollars?$/, ''))
  return integer !== null && Number.isSafeInteger(integer * 100) ? integer * 100 : null
}
export function tenderAnswer(value: string, amountOnly = false): TenderAnswer | null {
  let clean = value.trim().replace(/[.!?]+$/, '').toLowerCase()
  if (amountOnly && !/^(cash|bank)\b/.test(clean)) clean = `cash ${clean}`
  if (clean === 'bank') return { tender: 'bank' }
  if (clean === 'cash') return { tender: 'cash' }
  const match = /^cash\s+(.+)$/.exec(clean)
  if (!match) return null
  const amount = spokenCashCents(match[1])
  return amount !== null ? { tender: 'cash', amount_received_cents: amount } : null
}
export function apoCommand(value: string) {
  const clean = value.trim(), framed = /^apo\b([\s\S]+?)\b(?:napo|nabo|napple|apo)[.!?]*$/i.exec(clean)
  let body = (framed?.[1] ?? clean).trim().replace(/[,;]+/g, ' ').replace(/\s+/g, ' ')
  const ending = /\s+(cash(?:\s+[a-z0-9.-]+){0,9}|bank)$/i.exec(body)
  const tender = ending ? tenderAnswer(ending[1]) : null
  if (ending && tender) body = body.slice(0, ending.index).trim()
  const heardBody = body
  body = body.replace(/^(?:sell|record sale|sale)\s+/i, '').replace(/\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\b/gi, (word) => String(spokenQuantities[word.toLowerCase()])).replace(/\s+and\s+/gi, ' ')
  const complete = commandLines(body) !== null
  return { body, heardBody, closed: !!framed, complete, tender }
}
function commandLines(body: string): { quantity: number; name: string }[] | null {
  const matches = [...body.matchAll(/(\d{1,4})\s+([a-z][a-z0-9-]*(?:\s+(?!\d{1,4}\s)[a-z0-9][a-z0-9-]*)*)(?=\s+\d{1,4}\s|$)/gi)]
  if (!matches.length || matches.map((match) => match[0]).join(' ').toLowerCase() !== body.toLowerCase() || matches.some((match) => Number(match[1]) === 0)) return null
  return matches.map((match) => ({ quantity: Number(match[1]), name: match[2].toLowerCase() }))
}
export function eligibleForQuickSale(command: ReturnType<typeof apoCommand>, review: VoiceReview): boolean {
  const requested = commandLines(command.body)
  return command.closed && command.complete && review.canCommit && requested !== null && requested.length === review.lines.length && requested.every((item, i) => {
    const line = review.lines[i], name = line.product_name.toLowerCase(), stripped = name.replace(/\s+\d+(?:[a-z]+)?$/, '')
    const aliases = [name, stripped, ...name.split(/[\s-]+/)]
    if (name.startsWith('coca-cola')) aliases.push('coke')
    const normalize = (value: string) => value.replace(/[^a-z0-9]/g, '')
    return item.quantity === line.quantity && aliases.some((alias) => normalize(alias) === normalize(item.name))
  })
}
export function parseVoiceReview(value: unknown, shopId: string): VoiceReview {
  if (record(value) && ['unavailable', 'rejected'].includes(String(value.status))) throw new QuickSaleError(text(value.error) ? value.error : 'That command could not be safely understood. Please try again.', false, text(value.error_code) ? value.error_code : undefined)
  if (!record(value) || value.shop_id !== shopId || !text(value.request_id) || !text(value.transcript) || !text(value.status) || !Array.isArray(value.lines)) throw new QuickSaleError('The voice response could not be verified. Nothing has been confirmed.')
  const lines = value.lines as QuickLine[]
  if (lines.some((line) => !record(line) || !text(line.product_id) || !text(line.product_name) || !minor(line.quantity) || line.quantity === 0) || lines.length > 100 || new Set(lines.map((line) => line.product_id)).size !== lines.length) throw new QuickSaleError('The selected products or quantities could not be verified.')
  const retained = value.retained_lines, pendingItems = value.pending_items
  if(retained!==undefined||pendingItems!==undefined){
    if(!Array.isArray(retained)||!Array.isArray(pendingItems)||retained.length+pendingItems.length>100||retained.some(line=>!record(line)||!text(line.product_id)||!text(line.product_name)||!minor(line.quantity)||line.quantity===0)||new Set(retained.map(line=>line.product_id)).size!==retained.length||pendingItems.some(item=>!record(item)||!minor(item.slot_id)||item.slot_id>99||typeof item.heard!=='string'||item.heard.length>500||!(item.quantity===null||minor(item.quantity))||!(item.product_id===null&&item.product_name===null||text(item.product_id)&&text(item.product_name)))||new Set(pendingItems.map(item=>item.slot_id)).size!==pendingItems.length)throw new QuickSaleError('The retained basket or pending item could not be verified. Nothing has been confirmed.')
    if(value.status==='needs_clarification'&&pendingItems.length===0&&retained.length>0)throw new QuickSaleError('The pending basket context is incomplete.')
    if(value.status!=='needs_clarification'&&(retained.length>0||pendingItems.length>0))throw new QuickSaleError('Pending products cannot be treated as a complete basket.')
  }
  const saleIntent = record(value.intent) && value.intent.action === 'record_sale' && value.intent.needs_confirmation === true
  const requiresMatch = value.requires_match_confirmation === true
  if (value.requires_match_confirmation !== undefined && typeof value.requires_match_confirmation !== 'boolean' || value.provider_called != null && typeof value.provider_called !== 'boolean' || value.resolution_source != null && typeof value.resolution_source !== 'string') throw new QuickSaleError('The catalogue interpretation metadata could not be verified.')
  if (value.status === 'needs_match_confirmation' && (!requiresMatch || !saleIntent || !lines.length || !text(value.clarification_question))) throw new QuickSaleError('The proposed catalogue match could not be verified.')
  if (value.status === 'needs_clarification' && (!text(value.clarification_question) || lines.length > 0)) throw new QuickSaleError('The clarification question could not be verified.')
  const canCommit = value.status === 'needs_confirmation' && !requiresMatch && lines.length > 0 && saleIntent
  return { reviewId: value.request_id, shopId, transcript: value.transcript, status: value.status, lines, canCommit, requiresMatchConfirmation: requiresMatch, resolutionSource: typeof value.resolution_source === 'string' ? value.resolution_source : undefined, clarificationQuestion: text(value.clarification_question) ? value.clarification_question : undefined, ...(Array.isArray(retained)?{retainedLines:retained as QuickLine[],pendingItems:pendingItems as PendingVoiceItem[]}:{}), providerCalled: typeof value.provider_called === 'boolean' ? value.provider_called : undefined }
}
export function parseQuickReceipt(value: unknown, review: VoiceReview): QuickReceipt {
  if (!record(value) || !text(value.id) || value.shop_id !== review.shopId || !['cash', 'bank'].includes(String(value.tender)) || !minor(value.total_cents) || !minor(value.amount_received_cents) || !minor(value.change_cents) || !instant(value.created_at) || !Array.isArray(value.lines) || !record(value.stock_after) || value.lines.length !== review.lines.length) throw new QuickSaleError('The sale receipt is unverified. Recover it using the original request reference.', true)
  const lines = value.lines as QuickReceipt['lines'], stock = value.stock_after
  if (review.lines.some((line) => !lines.some((item) => item && item.product_id === line.product_id && item.quantity === line.quantity) || !minor(stock[line.product_id])) || value.amount_received_cents < value.total_cents || BigInt(value.amount_received_cents) - BigInt(value.total_cents) !== BigInt(value.change_cents) || value.tender === 'bank' && (value.change_cents !== 0 || value.amount_received_cents !== value.total_cents)) throw new QuickSaleError('Receipt amounts, change or stock do not match the reviewed sale. Recover the original request.', true)
  return value as unknown as QuickReceipt
}

export function createQuickSaleClient(getConfig: () => { baseUrl: string; shopId: string }, fetcher: typeof fetch = fetch) {
  const call = async (path: string, body: unknown, key: string, signal?: AbortSignal, mayCommit = true) => {
    const config = getConfig()
    const mutating = path === '/commit' || path.endsWith('/undo')
    if (!config.baseUrl || !config.shopId || !key.trim()) throw new QuickSaleError('Connect your shop before using Quick Sale.')
    const controller = new AbortController(), cancel = () => controller.abort()
    signal?.addEventListener('abort', cancel, { once: true }); if (signal?.aborted) cancel()
    const timer = setTimeout(cancel, mutating && !mayCommit ? 8000 : 30000)
    try {
      const response = await fetcher(`${config.baseUrl.replace(/\/$/, '')}/api/v1/shops/${encodeURIComponent(config.shopId)}/voice${path}`, { method: 'POST', headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'X-Shop-ID': config.shopId, 'Idempotency-Key': key }, body: JSON.stringify(body), signal: controller.signal })
      if (!response.ok) {
        const failure: unknown = await response.json().catch(() => null)
        const detail = record(failure) ? failure.detail : null
        if (mutating && response.status >= 500) {
          if (!mayCommit) throw new QuickSaleError('The payment question is unavailable. This request did not include a complete payment. Reconnect to your shop, then retry this basket with its original reference.', false, 'payment_question_connection')
          throw new QuickSaleError('The sale service could not confirm the outcome. Keep this basket and recover using the original request reference before starting another sale.', true, String(response.status))
        }
        throw new QuickSaleError(record(detail) && text(detail.message) ? detail.message : typeof detail === 'string' ? detail : `Voice sale request failed (${response.status}). Check the basket, stock and shop connection.`, false, record(detail) && text(detail.code) ? detail.code : String(response.status))
      }
      return { value: await response.json() as unknown, shopId: config.shopId }
    } catch (error) {
      if (error instanceof QuickSaleError) throw error
      if (mutating) {
        if (!mayCommit) throw new QuickSaleError('The payment question is unavailable. This request did not include a complete payment. Reconnect to your shop, then retry this basket with its original reference.', false, 'payment_question_connection')
        throw new QuickSaleError('The request outcome is unknown. Keep the basket and recover with the same request reference before trying another sale.', true)
      }
      throw new QuickSaleError(`Could not reach or read the voice service at ${config.baseUrl}. Check Shop Connection, the API server and your network, then retry. No sale was submitted by this voice request.`, false, 'voice_connection')
    } finally { clearTimeout(timer); signal?.removeEventListener('abort', cancel) }
  }
  return {
    async interpret(transcript: string, key: string, signal?: AbortSignal, clarificationOf?: string) {
      if (!transcript.trim() || transcript.length > 16000) throw new QuickSaleError('Use a command of 1–16,000 characters.')
      const { value, shopId } = await call('/transcript', { transcript: transcript.trim(), ...(clarificationOf ? { clarification_of: clarificationOf } : {}) }, key, signal)
      return parseVoiceReview(value, shopId)
    },
    async audio(audio_base64: string, media_type: string, key: string, signal?: AbortSignal) {
      const { value, shopId } = await call('/audio', { audio_base64, media_type }, key, signal)
      return parseVoiceReview(value, shopId)
    },
    async commit(review: VoiceReview, answer: TenderAnswer | null, key: string, signal?: AbortSignal): Promise<TenderQuestion | { kind: 'sale'; sale: QuickReceipt }> {
      if (!review.canCommit || review.shopId !== getConfig().shopId) throw new QuickSaleError('This basket is not a verified sale review for the connected shop.')
      if (review.requiresMatchConfirmation && !review.matchConfirmed) throw new QuickSaleError('Say Yes to confirm the proposed catalogue products before payment.')
      if (answer != null && (!record(answer) || !['cash', 'bank'].includes(String(answer.tender)) || answer.amount_received_cents != null && !minor(answer.amount_received_cents))) throw new QuickSaleError('Payment must be Cash or Bank with a non-negative whole number of cents. No payment request was sent.')
      const mayCommit = answer?.tender === 'bank' || answer?.tender === 'cash' && minor(answer.amount_received_cents)
      const { value } = await call('/commit', { review_id: review.reviewId, lines: review.lines.map(({ product_id, quantity }) => ({ product_id, quantity })), ...(review.requiresMatchConfirmation ? { match_confirmed: true } : {}), ...answer }, key, signal, mayCommit)
      if (record(value) && value.status === 'needs_tender') {
        if (value.review_id !== review.reviewId || !text(value.question) || !minor(value.amount_due_cents) || !Array.isArray(value.allowed_tenders) || value.allowed_tenders.some((item) => !['cash', 'bank'].includes(String(item))) || !Array.isArray(value.missing) || value.missing.some((item) => typeof item !== 'string')) throw new QuickSaleError('The payment question could not be verified. No sale receipt was received.', mayCommit, 'payment_question_response')
        return { ...value, kind: 'question' } as unknown as TenderQuestion
      }
      if (!mayCommit) throw new QuickSaleError('The payment question response could not be read. This request did not include a complete payment. Retry the same basket reference.', false, 'payment_question_response')
      const sale = parseQuickReceipt(value, review)
      if (answer && sale.tender !== answer.tender || answer?.amount_received_cents !== undefined && sale.amount_received_cents !== answer.amount_received_cents) throw new QuickSaleError('Receipt tender or amount differs from your answer. Recover the original request.', true)
      return { kind: 'sale', sale }
    },
    async undo(sale: QuickReceipt, key: string, signal?: AbortSignal): Promise<QuickReversal> {
      const { value, shopId } = await call(`/commit/${encodeURIComponent(sale.id)}/undo`, { actor: 'Shop operator', reason: 'User selected Undo last sale', confirmed: true }, key, signal)
      if (!record(value) || value.shop_id !== shopId || value.original_sale_id !== sale.id || value.status !== 'reversed' || !text(value.reversal_id) || !text(value.audit_id) || !instant(value.created_at) || !Array.isArray(value.lines) || value.lines.length !== sale.lines.length || sale.lines.some((line) => !(value.lines as QuickReversal['lines']).some((item) => item && item.product_id === line.product_id && item.quantity === line.quantity))) throw new QuickSaleError('Undo receipt is unverified. Recover it with the original reference before retrying.', true)
      return value as unknown as QuickReversal
    },
  }
}

