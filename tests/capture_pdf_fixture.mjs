import {buildReportExport} from '../apps/web/src/reportExport.ts'
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs'
const out='data/qa-capture-export/output/pdf';mkdirSync(out,{recursive:true})
const r={start_date:'2026-11-01',end_date:'2026-11-02',coverage_end_date:'2026-11-02',coverage:'historical_or_selected_range',as_of:'2026-11-02T18:00:00Z',shop_timezone:'Africa/Harare',currency:'USD',summary:{sales_total_cents:10000,transaction_count:100,cash_sales_cents:10000,bank_sales_cents:0,other_tender_sales_cents:0,cogs_micros:null,gross_profit_micros:null,margin_bps:null,missing_cogs_sale_count:1},products:Array.from({length:100},(_,i)=>({product_id:`p${i}`,product_name:`Product ${i+1} historical name with long descriptive label`,sku:`SKU-${i}`,label_source:'latest_receipt_snapshot',quantity_sold:1,revenue_cents:100,cogs_micros:i?1000000:null,gross_profit_micros:i?0:null,margin_bps:i?0:null})),warnings:['Some historical costs are unknown.'],monthly:[],daily:[]}
const logo='data:image/png;base64,'+readFileSync('apps/web/dist/street-ceo-logo.png').toString('base64')
writeFileSync(`${out}/report-layout.html`,buildReportExport(r,'profit',logo).html)
