import assert from 'node:assert/strict'
import {test} from 'node:test'
import {buildReportExport,csvCell} from '../src/reportExport.ts'
import {parseVoiceReview,createQuickSaleClient,confirmVoiceMatch} from '../src/quickSale.ts'
import {readRetainedBasket,saveRetainedBasket,clearRetainedBasket} from '../src/retainedBasket.ts'
import {WakeCommand} from '../src/wakePhrase.ts'
const config={baseUrl:'https://shop.invalid',shopId:'shop-1'}
const report={start_date:'2026-11-01',end_date:'2026-11-02',currency:'USD',shop_timezone:'Africa/Harare',coverage:'selected_range',coverage_end_date:'2026-11-02',as_of:'2026-11-02T12:00:00Z',summary:{sales_total_cents:3,transaction_count:1,cash_sales_cents:3,bank_sales_cents:0,other_tender_sales_cents:0,cogs_micros:40000,gross_profit_micros:-10000,margin_bps:-3333,missing_cogs_sale_count:0},products:[{product_name:'=SUM(1,2)',sku:'@BAD',product_id:'p',quantity_sold:1,revenue_cents:3,cogs_micros:40000,gross_profit_micros:-10000,margin_bps:-3333,label_source:'latest_receipt_snapshot'}],warnings:[],daily:[],monthly:[],stock_reversal_count:0}
const pending={shop_id:'shop-1',request_id:'review-1',transcript:'long original basket',status:'needs_clarification',lines:[],retained_lines:Array.from({length:99},(_,i)=>({product_id:`p${i}`,product_name:`Product ${i}`,quantity:1})),pending_items:[{slot_id:99,heard:'unclear',quantity:2,product_id:null,product_name:null}],clarification_question:'Which product is unclear?'}
function store(){const data=new Map();return {getItem:key=>data.get(key)??null,setItem:(key,value)=>data.set(key,value),removeItem:key=>data.delete(key)}}
test('CSV export preserves exact selected period, signed numeric values, zero and formula-safe text',()=>{
 const model=buildReportExport(report,'profit')
 assert.match(model.csv,/2026-11-01/);assert.match(model.csv,/2026-11-02/)
 assert.match(model.csv,/'=SUM\(1,2\)/);assert.match(model.csv,/'@BAD/)
 assert.match(model.csv,/"-0\.010000"/);assert.doesNotMatch(model.csv,/"'-0\.010000"/)
 assert.match(model.csv,/before shop expenses/);assert.match(model.csv,/latest_receipt_snapshot/)
 assert.match(csvCell('  =CMD()'),/^"'  =/)
 assert.equal(csvCell('a,"b"\nnext'),'"a,""b""\nnext"')
 assert.throws(()=>csvCell({number:'=CMD()'}))
})
test('unknown cost/profit never exports as zero and branded HTML escapes catalogue text',()=>{
 const unknown={...report,summary:{...report.summary,cogs_micros:null,gross_profit_micros:null,margin_bps:null,missing_cogs_sale_count:1},products:[{...report.products[0],product_name:'<script>alert(1)</script>',cogs_micros:null,gross_profit_micros:null,margin_bps:null}]}
 const model=buildReportExport(unknown,'profit')
 assert.match(model.csv,/Unknown/);assert.match(model.html,/street-ceo-logo\.png/)
 assert.match(model.html,/&lt;script&gt;/);assert.doesNotMatch(model.html,/<script>/)
 assert.match(model.rows.map(row=>row.text).join(' '),/1 sale\(s\) have missing cost/)
})
test('100-item partial basket is nonactionable and keeps all independently understood lines',async()=>{
 const review=parseVoiceReview(pending,'shop-1')
 assert.equal(review.retainedLines.length,99);assert.equal(review.pendingItems.length,1);assert.equal(review.lines.length,0);assert.equal(review.canCommit,false)
 const client=createQuickSaleClient(()=>config,()=>assert.fail('No partial commit request'))
 await assert.rejects(client.commit(review,null,'key'))
 assert.throws(()=>parseVoiceReview({...pending,retained_lines:[...pending.retained_lines,{product_id:'extra',product_name:'Extra',quantity:1}]},'shop-1'))
 assert.throws(()=>parseVoiceReview({...pending,lines:[{product_id:'p',product_name:'Partial',quantity:1}]},'shop-1'))
})
test('retained basket and exact in-flight reply key restore only under the same scoped shop',()=>{
 const storage=store(),review=parseVoiceReview(pending,'shop-1'),attempt={context:review.reviewId,transcript:'Bread loaf',key:'same-reply-key'}
 saveRetainedBasket(storage,config,{review,attempt},parseVoiceReview)
 assert.equal(readRetainedBasket(storage,config,parseVoiceReview).review.retainedLines.length,99)
 assert.deepEqual(readRetainedBasket(storage,config,parseVoiceReview).attempt,attempt)
 assert.equal(readRetainedBasket(storage,{...config,shopId:'other'},parseVoiceReview),null)
 clearRetainedBasket(storage,config);assert.equal(readRetainedBasket(storage,config,parseVoiceReview),null)
 assert.throws(()=>clearRetainedBasket({getItem:()=>'{still here}',setItem(){},removeItem(){}},config))
})
test('restored unpaid full match requires explicit Yes, never approval from saved client state',()=>{
 const wire={...pending,status:'needs_match_confirmation',lines:pending.retained_lines,retained_lines:[],pending_items:[],requires_match_confirmation:true,intent:{action:'record_sale',needs_confirmation:true}}
 const review=parseVoiceReview(wire,'shop-1'),storage=store()
 saveRetainedBasket(storage,config,{review,attempt:null},parseVoiceReview)
 const restored=readRetainedBasket(storage,config,parseVoiceReview).review
 assert.equal(restored.canCommit,false);assert.equal(restored.matchConfirmed,undefined)
 assert.equal(confirmVoiceMatch(restored).matchConfirmed,true)
})
test('long foreground basket supports 100 chunks while silence and total duration stay bounded',()=>{
 const machine=new WakeCommand(),names={apo:'apo',napo:'napo'}
 machine.accept('Apo',names,0)
 for(let i=0;i<100;i++)assert.equal(machine.accept(`one product${i}`,names,(i+1)*2000),null)
 const result=machine.accept('Napo',names,202000)
 assert.equal((result.match(/product/g)||[]).length,100)
 machine.accept('Apo one bread',names,0);assert.equal(machine.accept('Napo',names,21000),null)
 machine.accept('Apo one bread',names,0);machine.touch(299000);assert.equal(machine.accept('Napo',names,301000),null)
})
