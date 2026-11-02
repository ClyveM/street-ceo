import assert from 'node:assert/strict'
import { test } from 'node:test'
import { endDayCommand,canStartEndDay,reportDate,reportRange,monthRange,closeMoney,closeMicros,parseCashPreview,parseCashClose,parseSalesReport,createReportsCloseClient,CloseRequestError } from '../src/reportsClose.ts'
const config={baseUrl:'https://shop.example',shopId:'shop-1'},date='2026-11-02',version='a'.repeat(64)
const preview={business_date:date,shop_timezone:'Africa/Harare',opening_cash_cents:1000,opening_source:'explicit_opening',requires_opening:false,requires_payment_review:false,expected_cash_cents:1150,sales_cash_cents:150,paid_expenses_cash_cents:0,paid_purchases_cash_cents:0,refunds_cash_cents:0,adjustments_cash_cents:0,preview_version:version,warnings:[],saved_close:null}
const receipt={...preview,id:'close-1',audit_id:'audit-1',shop_id:config.shopId,cash_counted_cents:1100,cash_variance_cents:-50,bank_card_counted_cents:null,bank_card_variance_cents:null,bank_status:'not_counted',confirmed_at:'2026-11-02T16:00:00Z',source_version:version}
const report={start_date:date,end_date:date,shop_timezone:'Africa/Harare',currency:'USD',coverage:'historical_or_selected_range',coverage_end_date:date,as_of:'2026-11-02T16:00:00Z',summary:{sales_total_cents:500,transaction_count:1,cash_sales_cents:150,bank_sales_cents:300,other_tender_sales_cents:50,cogs_micros:null,missing_cogs_sale_count:1},daily:[{business_date:date,sales_total_cents:500,transaction_count:1}],monthly:[{month:'2026-11',sales_total_cents:500,transaction_count:1}],products:[{product_id:'deleted',product_name:'deleted',sku:null,label_source:'product_id',quantity_sold:2,revenue_cents:null,known_revenue_cents:0,unknown_revenue_line_count:1}],warnings:['Legacy multi-line revenue unknown'],stock_reversal_count:1}
test('End my day is exact and guarded against every pending sale and manual basket',()=>{
 for(const phrase of ['End my day','Apo end my day Napo','apo end my day nabo.'])assert.equal(endDayCommand(phrase),true)
 for(const phrase of ['one end my day soap','end my day and sell coke','apo end my day','please end my day'])assert.equal(endDayCommand(phrase),false)
 const idle={phase:'idle',busy:false,blocked:false,uncertain:false,manualBasket:false};assert.equal(canStartEndDay(idle),true)
 for(const phase of ['match','clarification','tender','review','error'])assert.equal(canStartEndDay({...idle,phase}),false)
 for(const key of ['busy','blocked','uncertain','manualBasket'])assert.equal(canStartEndDay({...idle,[key]:true}),false)
})
test('inclusive presets, month leap years and signed small shortages are exact',()=>{
 assert.deepEqual(reportRange('2026-11-02',1),{start:'2026-11-02',end:'2026-11-02'})
 assert.deepEqual(reportRange('2026-11-02',20),{start:'2026-10-14',end:'2026-11-02'})
 assert.deepEqual(reportRange('2026-11-02',90),{start:'2026-08-05',end:'2026-11-02'})
 assert.deepEqual(monthRange('2024-02'),{start:'2024-02-01',end:'2024-02-29'});assert.equal(reportDate('2026-02-29'),false)
 assert.equal(closeMicros(9007199254740991),'9007199254.740991');assert.equal(closeMoney(-50),'-0.50');assert.equal(closeMoney(0),'0.00');assert.equal(closeMoney(-1150),'-11.50')
})
test('server expected cash reconciles; missing opening and unavailable payment stay unknown, bank never becomes zero',()=>{
 assert.equal(parseCashPreview(preview,config.shopId).expected_cash_cents,1150)
 assert.equal(parseCashPreview({...preview,requires_opening:true,opening_source:'missing',opening_cash_cents:null,expected_cash_cents:null},config.shopId).requires_opening,true)
 assert.equal(parseCashPreview({...preview,requires_payment_review:true,opening_cash_cents:null,paid_purchases_cash_cents:null,expected_cash_cents:null},config.shopId).expected_cash_cents,null)
 assert.throws(()=>parseCashPreview({...preview,paid_purchases_cash_cents:null},config.shopId))
 assert.throws(()=>parseCashPreview({...preview,expected_cash_cents:1200},config.shopId))
 assert.equal(parseCashClose(receipt,config.shopId,date).cash_variance_cents,-50)
 for(const change of [{bank_card_counted_cents:0},{cash_variance_cents:50},{shop_id:'other'}])assert.throws(()=>parseCashClose({...receipt,...change},config.shopId,date))
})
test('deleted-product and legacy unknown amounts remain valid, separate from complete gross shop totals',()=>{
 const saved=parseSalesReport(report,date,date);assert.equal(saved.products[0].revenue_cents,null);assert.equal(saved.products[0].sku,null);assert.equal(saved.summary.other_tender_sales_cents,50);assert.equal(saved.summary.cogs_micros,null)
 assert.throws(()=>parseSalesReport({...report,products:[{...report.products[0],revenue_cents:500}]},date,date))
 assert.throws(()=>parseSalesReport({...report,daily:[]},date,date))
})
test('presets and business today resolve on the server, never using phone-local date',async()=>{
 const calls=[];const client=createReportsCloseClient(()=>config,async(url,init)=>{calls.push([url,init]);return Response.json(url.includes('/reports/')?report:preview)})
 await client.preview();await client.preset('last20')
 assert.match(calls[0][0],/\/cash-close\/preview$/);assert.match(calls[1][0],/preset=last20$/);assert.equal(calls[0][1].cache,'no-store')
})
test('late opening server reason prefix is verified and explicit zero is preserved',async()=>{
 const input={business_date:date,opening_cash_cents:0,actor:'Shop operator',reason:'Opening approved',confirmed:true};let body
 const client=createReportsCloseClient(()=>config,async(_url,init)=>{body=JSON.parse(init.body);return Response.json({id:'movement',shop_id:config.shopId,kind:'opening_balance',tender:'cash',amount_cents:0,actor:input.actor,reason:'Explicit late start-of-day opening declaration: '+input.reason,created_at:'2026-11-02T16:00:00Z',occurred_at:'2026-11-01T22:00:00Z'})})
 await client.opening(input,'original-opening-key');assert.equal(body.opening_cash_cents,0);assert.equal(body.confirmed,true)
})
test('uncertain close retries preserve original frozen body and key; malformed bank/variance cannot produce success',async()=>{
 const calls=[];const input={business_date:date,cash_counted_cents:1100,actor:'Shop operator',notes:'cash only',confirmed:true,preview_version:version}
 const client=createReportsCloseClient(()=>config,async(_url,init)=>{calls.push([init.headers['Idempotency-Key'],init.body]);if(calls.length===1)return Response.json({detail:'trace failed'},{status:503});return Response.json(receipt)})
 await assert.rejects(client.confirm(input,'same-key'),e=>e instanceof CloseRequestError&&e.uncertain)
 await client.confirm(input,'same-key');assert.deepEqual(calls[0],calls[1])
 const malformed=createReportsCloseClient(()=>config,async()=>Response.json({...receipt,bank_card_counted_cents:0}))
 await assert.rejects(malformed.confirm(input,'key'),e=>e.uncertain===true)
 const stale=createReportsCloseClient(()=>config,async()=>Response.json({detail:{code:'stale_preview',message:'Review again'}},{status:409}))
 await assert.rejects(stale.confirm(input,'key'),e=>e.code==='stale_preview'&&!e.uncertain)
})
