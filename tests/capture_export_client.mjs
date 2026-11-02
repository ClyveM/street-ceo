import assert from 'node:assert/strict'
import {test} from 'node:test'
import {csvCell,buildReportExport} from '../apps/web/src/reportExport.ts'
const fixture=()=>({start_date:'2026-11-01',end_date:'2026-11-02',coverage_end_date:'2026-11-02',coverage:'historical_or_selected_range',as_of:'2026-11-02T18:00:00Z',shop_timezone:'Africa/Harare',currency:'ZAR',summary:{sales_total_cents:1,transaction_count:1,cash_sales_cents:1,bank_sales_cents:0,other_tender_sales_cents:0,cogs_micros:10001,gross_profit_micros:-1,margin_bps:-1,missing_cogs_sale_count:0},products:[{product_id:'p',product_name:'=HYPERLINK("bad")\n<x>',sku:'@evil',label_source:'latest_receipt_snapshot',quantity_sold:1,revenue_cents:1,cogs_micros:10001,gross_profit_micros:-1,margin_bps:-1}],warnings:['Missing historical information'],stock_reversal_count:0,monthly:[],daily:[]})
test('untrusted CSV formula text is neutralized even after whitespace/control characters',()=>{
 for(const text of ['=SUM(1,2)',' +1','\t-1','\r\n@evil','\u0000=bad'])assert.match(csvCell(text),/^"'/)
 assert.equal(csvCell('A,"B"\nC'),'"A,""B""\nC"')
 assert.throws(()=>csvCell({number:'=bad'}))
})
test('exports exact signed micro loss and selected source metadata without repricing',()=>{
 const r=fixture(),m=buildReportExport(r,'profit')
 assert.match(m.csv,/"-0\.000001"/);assert.match(m.csv,/"-0\.01"/)
 assert.match(m.csv,/"Currency","ZAR"/);assert.match(m.csv,/2026-11-01/)
 assert.match(m.html,/&lt;x&gt;/);assert.ok(!m.html.includes('<x>'))
 assert.match(m.csv,/gross profit is before shop expenses/i)
 assert.match(m.html,/Missing historical information/)
})
test('unknown cost/profit and zero revenue undefined margin survive both file representations',()=>{
 const r=fixture();Object.assign(r.summary,{cogs_micros:null,gross_profit_micros:null,margin_bps:null,missing_cogs_sale_count:1})
 Object.assign(r.products[0],{revenue_cents:0,cogs_micros:0,gross_profit_micros:0,margin_bps:null})
 const m=buildReportExport(r,'profit')
 assert.match(m.csv,/"Unknown"/);assert.match(m.csv,/"Not defined"/);assert.match(m.html,/profit is incomplete/)
})

test('daily sheets stay separate from customer receipts and missing historical sheet costs remain incomplete',()=>{
 const r=fixture();Object.assign(r.summary,{transaction_count:0,daily_summary_count:1,missing_cogs_sale_count:0,missing_cogs_daily_summary_count:1,cogs_micros:null,gross_profit_micros:null,margin_bps:null})
 const m=buildReportExport(r,'profit')
 assert.match(m.csv,/"Customer receipts","0"/);assert.match(m.csv,/"Daily summaries","1"/)
 assert.match(m.html,/historical|incomplete/i);assert.match(m.csv,/"Unknown"/)
})

test('gross margin export rows use percentage units and unknown margin never gains currency',()=>{
 const r=fixture();const known=buildReportExport(r,'profit').rows.find(x=>x.text.startsWith('Gross margin (%)'))
 assert.equal(known.text,'Gross margin (%): -0.01%')
 r.summary.margin_bps=null;r.summary.gross_profit_micros=null
 const unknown=buildReportExport(r,'profit').rows.find(x=>x.text.startsWith('Gross margin (%)'))
 assert.equal(unknown.text,'Gross margin (%): Unknown')
})
