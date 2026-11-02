export function reportDate(value: string) { if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false; const date = new Date(`${value}T00:00:00Z`); return Number.isFinite(date.getTime()) && date.toISOString().slice(0,10) === value }
export function reportRange(today: string, days: 1 | 20 | 90) { if (!reportDate(today)) throw new Error('Choose a valid end date.'); const date = new Date(`${today}T00:00:00Z`); date.setUTCDate(date.getUTCDate() - days + 1); return { start: date.toISOString().slice(0,10), end: today } }
export function monthRange(month: string) { if (!/^\d{4}-(?:0[1-9]|1[0-2])$/.test(month)) throw new Error('Choose a valid month.'); const end = new Date(`${month}-01T00:00:00Z`); end.setUTCMonth(end.getUTCMonth()+1); end.setUTCDate(0); return { start: `${month}-01`, end: end.toISOString().slice(0,10) } }
export function endDayCommand(value: string) { const text=value.trim().toLowerCase().replace(/[.!?]+$/,''); return text === 'end my day' || /^apo\s+end my day\s+(?:napo|nabo|apo)$/.test(text) }
export function canStartEndDay(state: { phase: string; busy: boolean; blocked: boolean; uncertain: boolean; manualBasket: boolean }) { return ['idle','success'].includes(state.phase) && !state.busy && !state.blocked && !state.uncertain && !state.manualBasket }
export const closeMoney = (cents: number) => { const n=BigInt(cents),abs=n<0n?-n:n;return `${n<0n?'-':''}${abs/100n}.${String(abs%100n).padStart(2,'0')}` }
export const closeMicros=(micros:number)=>{const n=BigInt(micros),a=n<0n?-n:n;return `${n<0n?'-':''}${a/1000000n}.${String(a%1000000n).padStart(6,'0')}`}
export type ReportProfit = { gross_profit_micros?: number | null; margin_bps?: number | null }
export type SalesReport = { start_date: string; end_date: string; shop_timezone: string; currency: string; coverage: string; coverage_end_date: string; as_of: string; monthly: { month: string; sales_total_cents: number; transaction_count: number }[]; summary: ReportProfit & { known_cogs_micros?: number; unallocated_product_revenue_cents?: number; sales_total_cents: number; transaction_count: number; cash_sales_cents: number; bank_sales_cents: number; other_tender_sales_cents: number; cogs_micros: number | null; missing_cogs_sale_count: number }; daily: { business_date: string; sales_total_cents: number; transaction_count: number }[]; products: (ReportProfit & { cogs_micros?: number | null; known_cogs_micros?: number; unknown_cogs_line_count?: number; product_id: string; product_name: string; sku: string|null; label_source: string; quantity_sold: number; revenue_cents: number | null; known_revenue_cents: number; unknown_revenue_line_count: number })[]; warnings: string[]; stock_reversal_count: number }
export type CashCloseRecord = { id: string; audit_id: string; shop_id: string; business_date: string; opening_cash_cents: number; expected_cash_cents: number; cash_counted_cents: number; cash_variance_cents: number; bank_card_counted_cents: null; bank_card_variance_cents: null; bank_status: 'not_counted'; confirmed_at: string; source_version: string; warnings: string[] }
export type CashClosePreview = { business_date: string; shop_timezone: string; opening_cash_cents: number|null; opening_source: string; requires_opening: boolean; requires_payment_review: boolean; expected_cash_cents: number|null; sales_cash_cents: number; paid_expenses_cash_cents: number; paid_purchases_cash_cents: number|null; refunds_cash_cents: number; adjustments_cash_cents: number; preview_version: string; warnings: string[]; saved_close: CashCloseRecord|null }
export type CloseInput = { business_date: string; cash_counted_cents: number; actor: string; notes: string; confirmed: true; preview_version: string }
export type OpeningInput = { business_date: string; opening_cash_cents: number; actor: string; reason: string; confirmed: true }
const obj=(v:unknown):v is Record<string,unknown>=>!!v&&typeof v==='object'&&!Array.isArray(v)
const int=(v:unknown):v is number=>typeof v==='number'&&Number.isSafeInteger(v)
const amount=(v:unknown):v is number=>int(v)&&v>=0
const str=(v:unknown):v is string=>typeof v==='string'&&!!v.trim()
const strings=(v:unknown)=>Array.isArray(v)&&v.every(x=>typeof x==='string')
function require(condition:unknown,message='The service returned unverified report or closing details.'):asserts condition { if(!condition)throw new Error(message) }
function verifyReportedProfit(value: Record<string,unknown>, revenue: number|null, cogs: unknown): void {
 // Older servers remain usable for Sales; missing additive fields never imply profit.
 if (!('gross_profit_micros' in value) && !('margin_bps' in value)) return
 require((value.gross_profit_micros===null||int(value.gross_profit_micros)) && (value.margin_bps===null||int(value.margin_bps)) && (cogs===null||amount(cogs)))
 if(revenue===null||cogs===null){require(value.gross_profit_micros===null&&value.margin_bps===null);return}
 const revenueMicros=BigInt(revenue)*10000n, profit=revenueMicros-BigInt(cogs as number)
 require(int(value.gross_profit_micros)&&BigInt(value.gross_profit_micros)===profit)
 if(revenueMicros===0n){require(value.margin_bps===null);return}
 const numerator=(profit<0n?-profit:profit)*10000n, quotient=numerator/revenueMicros, remainder=numerator%revenueMicros
 const rounded=(quotient+(2n*remainder>=revenueMicros?1n:0n))*(profit<0n?-1n:1n)
 require(int(value.margin_bps)&&BigInt(value.margin_bps)===rounded)
}
export function parseSalesReport(v:unknown,start:string,end:string):SalesReport {
 require(obj(v)&&v.start_date===start&&v.end_date===end&&str(v.shop_timezone)&&str(v.currency)&&obj(v.summary)&&Array.isArray(v.daily)&&Array.isArray(v.products)&&Array.isArray(v.monthly)&&str(v.coverage)&&typeof v.coverage_end_date==='string'&&reportDate(v.coverage_end_date)&&str(v.as_of)&&Number.isFinite(Date.parse(v.as_of))&&strings(v.warnings)&&amount(v.stock_reversal_count))
 const s=v.summary;require(['sales_total_cents','transaction_count','cash_sales_cents','bank_sales_cents','other_tender_sales_cents','missing_cogs_sale_count'].every(k=>amount(s[k]))&&(s.cogs_micros===null||amount(s.cogs_micros)))
 require(BigInt(s.cash_sales_cents as number)+BigInt(s.bank_sales_cents as number)+BigInt(s.other_tender_sales_cents as number)===BigInt(s.sales_total_cents as number))
 require(s.missing_cogs_sale_count===0||s.cogs_micros===null)
 if ('known_cogs_micros' in s) require(amount(s.known_cogs_micros)&&(s.missing_cogs_sale_count===0?s.cogs_micros===s.known_cogs_micros:s.cogs_micros===null))
 if ('unallocated_product_revenue_cents' in s) require(amount(s.unallocated_product_revenue_cents))
 verifyReportedProfit(s,s.sales_total_cents as number,s.cogs_micros)
 const dates=new Set<string>();for(const d of v.daily){require(obj(d)&&typeof d.business_date==='string'&&reportDate(d.business_date)&&d.business_date>=start&&d.business_date<=end&&!dates.has(d.business_date)&&amount(d.sales_total_cents)&&amount(d.transaction_count));dates.add(d.business_date)}
 require(v.daily.reduce((sum,d)=>sum+BigInt(d.sales_total_cents),0n)===BigInt(s.sales_total_cents as number))
 for(const m of v.monthly)require(obj(m)&&typeof m.month==='string'&&/^\d{4}-(?:0[1-9]|1[0-2])$/.test(m.month)&&amount(m.sales_total_cents)&&amount(m.transaction_count));require(v.monthly.reduce((sum,m)=>sum+BigInt(m.sales_total_cents),0n)===BigInt(s.sales_total_cents as number))
 const ids=new Set<string>();for(const p of v.products){require(obj(p)&&str(p.product_id)&&!ids.has(p.product_id)&&str(p.product_name)&&(p.sku===null||typeof p.sku==='string')&&str(p.label_source)&&amount(p.quantity_sold)&&(p.revenue_cents===null||amount(p.revenue_cents))&&amount(p.known_revenue_cents)&&amount(p.unknown_revenue_line_count));ids.add(p.product_id);require(p.unknown_revenue_line_count===0?p.revenue_cents===p.known_revenue_cents:p.revenue_cents===null); if ('cogs_micros' in p) require(p.cogs_micros===null||amount(p.cogs_micros)); if ('known_cogs_micros' in p || 'unknown_cogs_line_count' in p) require(amount(p.known_cogs_micros)&&amount(p.unknown_cogs_line_count)&&(p.unknown_cogs_line_count===0?p.cogs_micros===p.known_cogs_micros:p.cogs_micros===null)); verifyReportedProfit(p,p.revenue_cents as number|null,p.cogs_micros)}
 return v as unknown as SalesReport
}
export function parseCashClose(v:unknown,shopId:string,date?:string):CashCloseRecord {
 require(obj(v)&&str(v.id)&&str(v.audit_id)&&v.shop_id===shopId&&typeof v.business_date==='string'&&reportDate(v.business_date)&&(!date||v.business_date===date)&&amount(v.opening_cash_cents)&&int(v.expected_cash_cents)&&amount(v.cash_counted_cents)&&int(v.cash_variance_cents)&&BigInt(v.cash_counted_cents)-BigInt(v.expected_cash_cents)===BigInt(v.cash_variance_cents)&&v.bank_card_counted_cents===null&&v.bank_card_variance_cents===null&&v.bank_status==='not_counted'&&str(v.confirmed_at)&&Number.isFinite(Date.parse(v.confirmed_at))&&str(v.source_version)&&strings(v.warnings),'The closing receipt could not be verified. Keep the original request for recovery.')
 return v as unknown as CashCloseRecord
}
export function parseCashPreview(v:unknown,shopId:string):CashClosePreview {
 require(obj(v)&&typeof v.business_date==='string'&&reportDate(v.business_date)&&str(v.shop_timezone)&&typeof v.requires_opening==='boolean'&&(v.opening_cash_cents===null||amount(v.opening_cash_cents))&&(v.expected_cash_cents===null||int(v.expected_cash_cents))&&str(v.opening_source)&&str(v.preview_version)&&strings(v.warnings))
 require(['sales_cash_cents','paid_expenses_cash_cents','refunds_cash_cents'].every(k=>amount(v[k]))&&(amount(v.paid_purchases_cash_cents)||v.requires_payment_review===true&&v.paid_purchases_cash_cents===null)&&int(v.adjustments_cash_cents))
 require(typeof v.requires_payment_review==='boolean');require(v.requires_opening?v.opening_cash_cents===null&&v.expected_cash_cents===null:(v.requires_payment_review?(v.opening_cash_cents===null||amount(v.opening_cash_cents))&&v.expected_cash_cents===null:amount(v.opening_cash_cents)&&int(v.expected_cash_cents)))
 if(!v.requires_opening&&!v.requires_payment_review)require(BigInt(v.opening_cash_cents as number)+BigInt(v.sales_cash_cents as number)-BigInt(v.paid_expenses_cash_cents as number)-BigInt(v.paid_purchases_cash_cents as number)-BigInt(v.refunds_cash_cents as number)+BigInt(v.adjustments_cash_cents as number)===BigInt(v.expected_cash_cents as number))
 require(v.saved_close===null||obj(v.saved_close));if(v.saved_close)parseCashClose(v.saved_close,shopId,v.business_date)
 return v as unknown as CashClosePreview
}
export class CloseRequestError extends Error { uncertain:boolean;code:string;constructor(message:string,uncertain=false,code=''){super(message);this.uncertain=uncertain;this.code=code} }
export function createReportsCloseClient(getConfig:()=>{baseUrl:string;shopId:string},fetcher:typeof fetch=fetch){
 const call=async(path:string,input?:unknown,key?:string)=>{
  const config=getConfig();require(str(config.baseUrl)&&str(config.shopId),'Connect your shop before loading reports or closing cash.')
  try{
   const response=await fetcher(`${config.baseUrl.replace(/\/$/,'')}/api/v1/shops/${encodeURIComponent(config.shopId)}${path}`,{method:input===undefined?'GET':'POST',headers:{Accept:'application/json','Content-Type':'application/json','X-Shop-ID':config.shopId,...key?{'Idempotency-Key':key}:{}},body:input===undefined?undefined:JSON.stringify(input),signal:AbortSignal.timeout(15000),cache:'no-store'})
   if(!response.ok){let detail:unknown;try{detail=(await response.json()).detail}catch{};throw new CloseRequestError(obj(detail)&&str(detail.message)?detail.message:`Shop request failed (${response.status}).`,input!==undefined&&response.status>=500,obj(detail)&&str(detail.code)?detail.code:String(response.status))}
   return {value:await response.json() as unknown,shopId:config.shopId}
  }catch(e){if(e instanceof CloseRequestError)throw e;throw new CloseRequestError(e instanceof Error?e.message:'Connection unavailable.',input!==undefined)}
 }
 return {
  async report(start:string,end:string){require(reportDate(start)&&reportDate(end)&&start<=end,'Choose valid inclusive start and end dates.');const r=await call(`/reports/sales?start_date=${start}&end_date=${end}`);return parseSalesReport(r.value,start,end)},
  async preset(preset:'last1'|'last20'|'last90'|'month',month?:string){const r=await call(`/reports/sales?preset=${preset}${month?`&month=${month}`:''}`);require(obj(r.value)&&typeof r.value.start_date==='string'&&reportDate(r.value.start_date)&&typeof r.value.end_date==='string'&&reportDate(r.value.end_date));return parseSalesReport(r.value,r.value.start_date,r.value.end_date)},
  async preview(date?:string){require(!date||reportDate(date),'Choose a valid business date.');const r=await call(`/cash-close/preview${date?`?business_date=${date}`:''}`);return parseCashPreview(r.value,r.shopId)},
  async get(date:string){require(reportDate(date));const r=await call(`/cash-close/${date}`);return parseCashClose(r.value,r.shopId,date)},
  async confirm(input:CloseInput,key:string){require(reportDate(input.business_date)&&amount(input.cash_counted_cents)&&str(input.actor)&&input.confirmed===true&&str(input.preview_version)&&str(key));const r=await call('/cash-close',input,key);try{const saved=parseCashClose(r.value,r.shopId,input.business_date);require(saved.cash_counted_cents===input.cash_counted_cents&&saved.source_version===input.preview_version);return saved}catch(e){throw new CloseRequestError(e instanceof Error?e.message:'Unverified receipt.',true)}},
  async opening(input:OpeningInput,key:string){require(reportDate(input.business_date)&&amount(input.opening_cash_cents)&&str(input.actor)&&str(input.reason)&&input.confirmed===true&&str(key));const r=await call('/cash-close/opening',input,key);try{require(obj(r.value)&&str(r.value.id)&&r.value.shop_id===r.shopId&&r.value.kind==='opening_balance'&&r.value.tender==='cash'&&r.value.amount_cents===input.opening_cash_cents&&r.value.actor===input.actor&&r.value.reason===('Explicit late start-of-day opening declaration: '+input.reason).slice(0,240)&&str(r.value.created_at)&&str(r.value.occurred_at));return r.value}catch(e){throw new CloseRequestError(e instanceof Error?e.message:'Opening receipt unverified.',true)}},
 }
}
