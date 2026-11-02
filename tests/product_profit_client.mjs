import assert from 'node:assert/strict'
import {test} from 'node:test'
import {parseSalesReport} from '../apps/web/src/reportsClose.ts'
import {rankedProfitProducts,reportMicroAmount,reportMargin} from '../apps/web/src/reportPresentation.ts'
const date='2026-11-02'
const fixture=()=>({start_date:date,end_date:date,coverage_end_date:date,coverage:'historical_or_selected_range',as_of:'2026-11-02T18:00:00Z',shop_timezone:'Africa/Harare',currency:'USD',
 summary:{sales_total_cents:2,transaction_count:1,cash_sales_cents:2,bank_sales_cents:0,other_tender_sales_cents:0,cogs_micros:19999,missing_cogs_sale_count:0,gross_profit_micros:1,margin_bps:1},
 monthly:[{month:'2026-11',sales_total_cents:2,transaction_count:1}],daily:[{business_date:date,sales_total_cents:2,transaction_count:1}],
 products:[{product_id:'one',product_name:'One',sku:'ONE',label_source:'latest_receipt_snapshot',quantity_sold:1,revenue_cents:2,known_revenue_cents:2,unknown_revenue_line_count:0,cogs_micros:19999,gross_profit_micros:1,margin_bps:1}],warnings:[],stock_reversal_count:0})

test('strict profit arithmetic verifies half-up ties independently for either sign',()=>{
 assert.equal(parseSalesReport(fixture(),date,date).summary.margin_bps,1)
 const loss=fixture()
 for(const value of [loss.summary,loss.products[0]])Object.assign(value,{cogs_micros:20001,gross_profit_micros:-1,margin_bps:-1})
 assert.equal(parseSalesReport(loss,date,date).summary.margin_bps,-1)
 for(const change of [{gross_profit_micros:2},{margin_bps:0},{margin_bps:1.5},{gross_profit_micros:Number.MAX_SAFE_INTEGER+1}]){
  const bad=fixture();Object.assign(bad.summary,change);assert.throws(()=>parseSalesReport(bad,date,date))
 }
})

test('missing cost explicitly prevents known profit even when optional known-cost metadata is absent',()=>{
 const bad=fixture();bad.summary.missing_cogs_sale_count=1
 assert.throws(()=>parseSalesReport(bad,date,date))
 const unknown=fixture();Object.assign(unknown.summary,{cogs_micros:null,gross_profit_micros:null,margin_bps:null,missing_cogs_sale_count:1})
 Object.assign(unknown.products[0],{cogs_micros:null,gross_profit_micros:null,margin_bps:null})
 assert.equal(parseSalesReport(unknown,date,date).summary.gross_profit_micros,null)
})

test('old Sales-only reports remain usable but do not gain invented profit',()=>{
 const old=fixture()
 for(const item of [old.summary,old.products[0]]){delete item.gross_profit_micros;delete item.margin_bps}
 const parsed=parseSalesReport(old,date,date)
 assert.equal(parsed.summary.gross_profit_micros,undefined)
 assert.equal(reportMicroAmount(parsed.summary.gross_profit_micros,'USD'),'Incomplete')
})

test('exact micros round half up for display while tiny losses retain explicit loss context',()=>{
 assert.equal(reportMicroAmount(5000,'USD'),'USD 0.01')
 assert.equal(reportMicroAmount(-5000,'USD'),'USD -0.01')
 assert.match(reportMicroAmount(-1,'USD'),/Loss.*0\.01/)
 assert.equal(reportMicroAmount(0,'USD'),'USD 0.00')
 assert.equal(reportMicroAmount(null,'USD'),'Incomplete')
 assert.equal(reportMargin(-20000,100,-2000000),'-200.00%')
 assert.equal(reportMargin(null,0,-1),'Not defined')
})

test('known zero and losses rank before unknown without changing report order or averaging margins',()=>{
 const products=[{product_name:'Unknown',gross_profit_micros:null},{product_name:'Loss',gross_profit_micros:-1},{product_name:'Zero',gross_profit_micros:0},{product_name:'Profit',gross_profit_micros:10000}]
 assert.deepEqual(rankedProfitProducts(products).map(p=>p.product_name),['Profit','Zero','Loss','Unknown'])
 assert.deepEqual(products.map(p=>p.product_name),['Unknown','Loss','Zero','Profit'])
})
