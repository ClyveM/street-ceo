import assert from 'node:assert/strict'
import {test} from 'node:test'
import {parseSalesReport} from '../src/reportsClose.ts'
import {reportMicroAmount,reportMargin,rankedProfitProducts} from '../src/reportPresentation.ts'
const date='2026-11-02'
function report(revenue=3,cost=10000,profit=20000,margin=6667){
 const unknown=cost===null
 return {start_date:date,end_date:date,shop_timezone:'Africa/Harare',currency:'USD',coverage:'current_day',coverage_end_date:date,as_of:'2026-11-02T10:00:00Z',summary:{sales_total_cents:revenue,transaction_count:1,cash_sales_cents:revenue,bank_sales_cents:0,other_tender_sales_cents:0,cogs_micros:cost,known_cogs_micros:unknown?0:cost,missing_cogs_sale_count:unknown?1:0,gross_profit_micros:profit,margin_bps:margin},daily:[{business_date:date,sales_total_cents:revenue,transaction_count:1}],monthly:[{month:'2026-11',sales_total_cents:revenue,transaction_count:1}],products:[{product_id:'p',product_name:'Bread',sku:'B',label_source:'latest_receipt_snapshot',quantity_sold:1,revenue_cents:revenue,known_revenue_cents:revenue,unknown_revenue_line_count:0,cogs_micros:cost,known_cogs_micros:unknown?0:cost,unknown_cogs_line_count:unknown?1:0,gross_profit_micros:profit,margin_bps:margin}],warnings:[],stock_reversal_count:0}
}
const parse=r=>parseSalesReport(r,date,date)
test('reported exact gross profit and signed nearest basis points validate with BigInt',()=>{
 assert.equal(parse(report()).summary.margin_bps,6667)
 assert.equal(parse(report(2,19999,1,1)).products[0].gross_profit_micros,1)
 assert.equal(parse(report(2,20001,-1,-1)).summary.margin_bps,-1)
 assert.equal(parse(report(1,10000,0,0)).summary.gross_profit_micros,0)
 assert.equal(parse(report(0,10000,-10000,null)).summary.margin_bps,null)
})
test('unknown costs or revenue never yield profit, including omitted optional known cost',()=>{
 assert.equal(parse(report(3,null,null,null)).summary.gross_profit_micros,null)
 const partial=report();partial.products[0]={...partial.products[0],revenue_cents:null,unknown_revenue_line_count:1,gross_profit_micros:null,margin_bps:null}
 assert.equal(parse(partial).products[0].gross_profit_micros,null)
 const bad=report();bad.summary.missing_cogs_sale_count=1;delete bad.summary.known_cogs_micros
 assert.throws(()=>parse(bad))
 const falseProfit=report(3,null,30000,10000)
 assert.throws(()=>parse(falseProfit))
})
test('malformed, unsafe and mathematically false provider figures are rejected',()=>{
 assert.throws(()=>parse(report(3,10000,20001,6667)))
 assert.throws(()=>parse(report(2,19999,1,0)))
 assert.throws(()=>parse(report(2,20001,-1,0)))
 assert.throws(()=>parse(report(0,10000,-10000,0)))
 assert.throws(()=>parse(report(Number.MAX_SAFE_INTEGER,0,Number.MAX_SAFE_INTEGER,10000)))
})
test('old Sales payload remains readable but missing profit fields do not become zero',()=>{
 const legacy=report()
 for(const row of [legacy.summary,...legacy.products]){delete row.gross_profit_micros;delete row.margin_bps}
 const parsed=parse(legacy)
 assert.equal(parsed.summary.gross_profit_micros,undefined)
 assert.equal(reportMicroAmount(parsed.products[0].gross_profit_micros,'USD'),'Incomplete')
 assert.equal(reportMargin(undefined,3,undefined),'Incomplete')
})
test('integer HALF_UP money preserves tiny known loss and exact zero; margins never divide by zero',()=>{
 assert.equal(reportMicroAmount(5000,'USD'),'USD 0.01')
 assert.equal(reportMicroAmount(-5000,'USD'),'USD -0.01')
 assert.equal(reportMicroAmount(4999,'USD'),'< USD 0.01')
 assert.equal(reportMicroAmount(-4999,'USD'),'Loss < USD 0.01')
 assert.equal(reportMicroAmount(0,'USD'),'USD 0.00')
 assert.equal(reportMicroAmount(null,'USD'),'Incomplete')
 assert.equal(reportMargin(-3333,3,-10000),'-33.33%')
 assert.equal(reportMargin(null,0,-10000),'Not defined')
 assert.equal(reportMargin(null,null,null),'Incomplete')
})
test('profit ranking uses exact complete amounts, losses stay signed and unknown remains last',()=>{
 const products=[{product_name:'Unknown',gross_profit_micros:null},{product_name:'Loss',gross_profit_micros:-1},{product_name:'Zero',gross_profit_micros:0},{product_name:'Profit',gross_profit_micros:1}]
 assert.deepEqual(rankedProfitProducts(products).map(p=>p.product_name),['Profit','Zero','Loss','Unknown'])
 assert.equal(products[0].product_name,'Unknown')
})
