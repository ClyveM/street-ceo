// Independent financial API fixtures, no real service or provider.
import assert from 'node:assert/strict'
import {test} from 'node:test'
import {canStartEndDay,endDayCommand,parseCashClose,parseCashPreview,parseSalesReport,createReportsCloseClient} from '../apps/web/src/reportsClose.ts'

const shop='00000000-0000-0000-0000-000000000001',day='2026-11-01',version='a'.repeat(64)
const preview={business_date:day,shop_timezone:'Africa/Harare',opening_cash_cents:2000,opening_source:'explicit_opening',requires_opening:false,requires_payment_review:false,expected_cash_cents:2300,sales_cash_cents:300,paid_expenses_cash_cents:0,paid_purchases_cash_cents:0,refunds_cash_cents:0,adjustments_cash_cents:0,preview_version:version,warnings:[],saved_close:null}
const receipt={...preview,id:'close-1',audit_id:'audit-1',shop_id:shop,cash_counted_cents:2200,cash_variance_cents:-100,bank_card_counted_cents:null,bank_card_variance_cents:null,bank_status:'not_counted',confirmed_at:'2026-11-01T20:00:00Z',source_version:version}

test('End my day is exact and idle-only; pending/manual/unknown states never close',()=>{
 for(const text of ['end my day','Apo end my day Napo'])assert.equal(endDayCommand(text),true)
 for(const text of ['end my day one coke','one end my day','do not end my day'])assert.equal(endDayCommand(text),false)
 const base={phase:'idle',busy:false,blocked:false,uncertain:false,manualBasket:false}
 assert.equal(canStartEndDay(base),true)
 for(const phase of ['tender','match','clarification','error'])assert.equal(canStartEndDay({...base,phase}),false)
 for(const flag of ['busy','blocked','uncertain','manualBasket'])assert.equal(canStartEndDay({...base,[flag]:true}),false)
})

test('cash comparison preserves shortage and rejects invented bank count or auto-balance',()=>{
 assert.equal(parseCashPreview(preview,shop).expected_cash_cents,2300)
 assert.equal(parseCashClose(receipt,shop,day).cash_variance_cents,-100)
 assert.throws(()=>parseCashClose({...receipt,bank_card_counted_cents:0},shop,day))
 assert.throws(()=>parseCashClose({...receipt,cash_variance_cents:0},shop,day))
 assert.throws(()=>parseCashPreview({...preview,expected_cash_cents:2500},shop))
 const unknown=parseCashPreview({...preview,opening_cash_cents:null,expected_cash_cents:null,requires_opening:true},shop)
 assert.equal(unknown.expected_cash_cents,null)
 const paymentReview=parseCashPreview({...preview,paid_purchases_cash_cents:null,expected_cash_cents:null,requires_payment_review:true},shop)
 assert.equal(paymentReview.paid_purchases_cash_cents,null)
 assert.throws(()=>parseCashPreview({...preview,paid_purchases_cash_cents:null},shop))
})

test('opening declaration accepts authoritative server audit reason instead of false uncertain outcome',async()=>{
 const input={business_date:day,opening_cash_cents:0,actor:'QA',reason:'explicit synthetic opening',confirmed:true},requests=[]
 const client=createReportsCloseClient(()=>({baseUrl:'http://example.test',shopId:shop}),async(url,options)=>{
  requests.push(JSON.parse(options.body))
  return Response.json({id:'opening-1',shop_id:shop,kind:'opening_balance',tender:'cash',amount_cents:0,actor:'QA',reason:'Explicit late start-of-day opening declaration: '+input.reason,created_at:'2026-11-01T09:00:00Z',occurred_at:'2026-10-31T22:00:00Z'})
 })
 const result=await client.opening(input,'original-opening-key')
 assert.equal(result.amount_cents,0)
 assert.deepEqual(requests,[input])
})

test('deleted-product report keeps null current SKU and other-tender amounts without inventing labels',()=>{
 const data={start_date:day,end_date:day,shop_timezone:'Africa/Harare',currency:'USD',summary:{sales_total_cents:500,transaction_count:1,cash_sales_cents:0,bank_sales_cents:0,other_tender_sales_cents:500,cogs_micros:null,missing_cogs_sale_count:1},daily:[{business_date:day,sales_total_cents:500,transaction_count:1}],products:[{product_id:'deleted',product_name:'deleted',sku:null,label_source:'product_id',quantity_sold:1,revenue_cents:500,known_revenue_cents:500,unknown_revenue_line_count:0}],warnings:['Current product label unavailable'],stock_reversal_count:0}
 Object.assign(data,{coverage:'historical_or_selected_range',coverage_end_date:day,as_of:'2026-11-01T20:00:00Z',monthly:[{month:'2026-11',sales_total_cents:500,transaction_count:1}]})
 const result=parseSalesReport(data,day,day)
 assert.equal(result.summary.sales_total_cents,500)
 assert.equal(result.products[0].sku,null)
})

test('lost close response stays uncertain and exact caller payload/reference can be retried',async()=>{
 const sent=[],input={business_date:day,cash_counted_cents:2200,actor:'QA',notes:'synthetic',confirmed:true,preview_version:version}
 const client=createReportsCloseClient(()=>({baseUrl:'http://example.test',shopId:shop}),async(url,options)=>{sent.push({key:options.headers['Idempotency-Key'],body:options.body});if(sent.length===1)throw new TypeError('synthetic lost response');return Response.json(receipt)})
 await assert.rejects(client.confirm(input,'same-close-key'),error=>error.uncertain===true)
 assert.equal((await client.confirm(input,'same-close-key')).cash_variance_cents,-100)
 assert.deepEqual(sent[0],sent[1])
})
