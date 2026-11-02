import type { SalesReport } from './reportsClose'
export type ReportSelection = {preset: 'last1'|'last20'|'last90'|'month'; month?: string} | {start: string; end: string}
export function selectionKey(value: ReportSelection): string { return 'preset' in value ? `${value.preset}:${value.month ?? ''}` : `${value.start}:${value.end}` }
export function selectionLabel(value: ReportSelection): string { return 'preset' in value ? ({last1:'Today', last20:'Last 20 days', last90:'Last 90 days', month:'Month review'}[value.preset]) : 'Custom dates' }
export function validReportDates(start: string,end: string,isDate: (value:string)=>boolean): boolean { return isDate(start) && isDate(end) && start <= end }
export function reportDateLabel(value: string): string { return new Intl.DateTimeFormat('en-GB', {day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}).format(new Date(`${value}T12:00:00Z`)) }
export function rankedProducts(products: SalesReport['products']): SalesReport['products'] { return [...products].sort((a,b)=>b.quantity_sold-a.quantity_sold || a.product_name.localeCompare(b.product_name)) }
export function missingCostMessage(summary: SalesReport['summary']): string | null {
 if(summary.missing_cogs_sale_count > 0) return `Cost missing for ${summary.missing_cogs_sale_count} ${summary.missing_cogs_sale_count === 1 ? 'sale' : 'sales'}. Profit is incomplete.`
 return summary.cogs_micros === null ? 'Some saved costs are unknown. Profit is incomplete.' : null
}
