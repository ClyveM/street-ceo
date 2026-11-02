import {reportDate} from '../src/reportsClose.ts'
import assert from 'node:assert/strict'
import {test} from 'node:test'
import {selectionKey,selectionLabel,validReportDates,reportDateLabel,rankedProducts,missingCostMessage} from '../src/reportPresentation.ts'
test('explicit active periods and custom selections have distinct response identity',()=>{
 assert.equal(selectionLabel({preset:'last1'}),'Today')
 assert.equal(selectionLabel({preset:'month',month:'2026-11'}),'Month review')
 assert.notEqual(selectionKey({preset:'month',month:'2026-10'}),selectionKey({preset:'month',month:'2026-11'}))
 assert.notEqual(selectionKey({start:'2026-11-01',end:'2026-11-02'}),selectionKey({preset:'last1'}))
})
test('custom dates are inclusive valid dates in order; labels do not shift timezones',()=>{
 assert.equal(validReportDates('2024-02-29','2024-02-29',reportDate),true)
 assert.equal(validReportDates('2026-02-29','2026-03-01',reportDate),false)
 assert.equal(validReportDates('2026-11-02','2026-11-01',reportDate),false)
 assert.equal(validReportDates('','2026-11-01',reportDate),false)
 assert.match(reportDateLabel('2026-11-02'),/2 Nov 2026/)
})
test('product rank copies by quantity without changing stored amounts or source order',()=>{
 const original=[{product_name:'Soap',quantity_sold:1,revenue_cents:null,known_revenue_cents:20},{product_name:'Bread',quantity_sold:4,revenue_cents:720},{product_name:'Milk',quantity_sold:4,revenue_cents:520}]
 const result=rankedProducts(original)
 assert.deepEqual(result.map(p=>p.product_name),['Bread','Milk','Soap'])
 assert.equal(result[2].revenue_cents,null)
 assert.equal(original[0].product_name,'Soap')
})
test('incomplete costs stay visible and unknown never becomes zero profit',()=>{
 assert.equal(missingCostMessage({cogs_micros:0,missing_cogs_sale_count:0}),null)
 assert.match(missingCostMessage({cogs_micros:null,missing_cogs_sale_count:0}),/unknown/)
 assert.match(missingCostMessage({cogs_micros:null,missing_cogs_sale_count:2}),/2 sales.*incomplete/)
})
