// Independent contract check: simulated transport only, no live phone/server writes.
import assert from 'node:assert/strict'
import {test} from 'node:test'
import {createQuickSaleClient} from '../apps/web/src/quickSale.ts'
import {checkShopReachability} from '../apps/web/src/shopReachability.ts'

const config={baseUrl:'http://example.test:8001',shopId:'00000000-0000-0000-0000-000000000001'}
const review={reviewId:'review-1',shopId:config.shopId,transcript:'one Coke',status:'needs_confirmation',lines:[{product_id:'product-1',product_name:'Coke',quantity:1}],canCommit:true}
const question={status:'needs_tender',review_id:review.reviewId,question:'Should I record this sale as cash or bank?',allowed_tenders:['cash','bank'],amount_due_cents:150,missing:['tender']}

test('a real-shape HTTP 200 payment question stays a question, never a receipt',async()=>{
 const sent=[]
 const client=createQuickSaleClient(()=>config,async(url,init)=>{sent.push({key:init.headers['Idempotency-Key'],body:JSON.parse(init.body)});return Response.json(question,{status:200})})
 const result=await client.commit(review,null,'unpaid-original')
 assert.equal(result.kind,'question')
 assert.equal(result.status,'needs_tender')
 assert.equal(result.amount_due_cents,150)
 assert.equal(result.sale,undefined)
 assert.equal(sent[0].body.tender,undefined)
 assert.equal(sent[0].body.amount_received_cents,undefined)
})

test('lost prepayment question is safely retryable with the identical original unpaid request',async()=>{
 const sent=[]
 const client=createQuickSaleClient(()=>config,async(url,init)=>{sent.push({url,key:init.headers['Idempotency-Key'],body:JSON.parse(init.body)});if(sent.length===1)throw new TypeError('simulated inaccessible LAN');return Response.json(question,{status:200})})
 await assert.rejects(client.commit(review,null,'unpaid-original'),error=>error.uncertain===false && error.code==='payment_question_connection')
 const recovered=await client.commit(review,null,'unpaid-original')
 assert.equal(recovered.kind,'question')
 assert.deepEqual(sent[0],sent[1])
 assert.equal(recovered.sale,undefined)
})

test('only complete payment and undo transport failures imply an unknown mutation',async()=>{
 const client=createQuickSaleClient(()=>config,async()=>{throw new TypeError('simulated inaccessible LAN')})
 for(const answer of [null,{tender:'cash'}])await assert.rejects(client.commit(review,answer,'question-original'),error=>error.uncertain===false&&error.code==='payment_question_connection')
 for(const answer of [{tender:'bank'},{tender:'cash',amount_received_cents:500},{tender:'cash',amount_received_cents:0}])await assert.rejects(client.commit(review,answer,'paid-original'),error=>error.uncertain===true)
 await assert.rejects(client.undo({id:'prior-receipt',lines:review.lines},'undo-original'),error=>error.uncertain===true)
})

test('invalid runtime payment cannot reach the server while being classified as an unpaid question',async()=>{
 let calls=0
 const client=createQuickSaleClient(()=>config,async()=>{calls++;throw new TypeError('Invalid supplied payment reached transport')})
 for(const answer of [{tender:'Cash',amount_received_cents:500},{tender:'Bank'},{tender:'cash',amount_received_cents:true},{tender:'cash',amount_received_cents:'500'},{tender:'cash',amount_received_cents:Number.MAX_SAFE_INTEGER+1},{tender:'cash',amount_received_cents:1.5}])await assert.rejects(client.commit(review,answer,'invalid-payment'),error=>error.uncertain===false)
 assert.equal(calls,0)
})

test('server failure during a question does not make an unqualified no-sale claim about earlier paid uncertainty',async()=>{
 const sent=[]
 const client=createQuickSaleClient(()=>config,async(url,init)=>{sent.push({key:init.headers['Idempotency-Key'],body:JSON.parse(init.body)});return Response.json({detail:'unavailable'},{status:503})})
 await assert.rejects(client.commit(review,{tender:'cash',amount_received_cents:500},'paid-original'),error=>error.uncertain===true)
 await assert.rejects(client.commit(review,null,'unpaid-diagnostic'),error=>error.uncertain===false&&error.code==='payment_question_connection'&&/This request/.test(error.message)&&!/(?:no sale was recorded|no sale was submitted)/i.test(error.message))
 assert.equal(sent[0].key,'paid-original')
 assert.equal(sent[0].body.amount_received_cents,500)
})

test('transcript connection failure is retryable and cannot be reported as a sale mutation',async()=>{
 const client=createQuickSaleClient(()=>config,async()=>{throw new TypeError('simulated inaccessible LAN')})
 await assert.rejects(client.interpret('one Coke','review-original'),error=>error.uncertain===false && error.code==='voice_connection')
})

test('network interface online is not used as proof of a reachable shop',async()=>{
 const before=Object.getOwnPropertyDescriptor(globalThis,'navigator')
 Object.defineProperty(globalThis,'navigator',{configurable:true,value:{onLine:true}})
 try {
  const result=await checkShopReachability(config,undefined,async()=>{throw new TypeError('simulated inaccessible LAN')})
  assert.equal(result.status,'unavailable')
  assert.match(result.detail,/network indicator alone/)
 } finally {if(before)Object.defineProperty(globalThis,'navigator',before);else delete globalThis.navigator}
})

test('only read-only readiness and matching shop prove the current connection',async()=>{
 const calls=[]
 const result=await checkShopReachability(config,undefined,async(url,init)=>{calls.push({url,init});return Response.json(new URL(url).pathname.endsWith('/readyz')?{status:'ready'}:{id:config.shopId})})
 assert.equal(result.status,'connected')
 assert.equal(calls.length,2)
 assert.ok(calls.every(call=>!call.init.method||call.init.method==='GET'))
 assert.ok(calls.every(call=>call.init.cache==='no-store'&&new URL(call.url).searchParams.has('connection_check')))
 assert.equal(calls.find(call=>!new URL(call.url).pathname.endsWith('/readyz')).init.headers['X-Shop-ID'],config.shopId)
 for(const failure of ['wrong-shop','not-ready']) {
  const result=await checkShopReachability(config,undefined,async url=>Response.json(new URL(url).pathname.endsWith('/readyz')?{status:failure==='not-ready'?'unavailable':'ready'}:{id:failure==='wrong-shop'?'other':config.shopId}))
  assert.equal(result.status,'unavailable')
 }
})

test('invalid credential-bearing address is neither probed nor displayed',async()=>{
 let calls=0
 const result=await checkShopReachability({...config,baseUrl:'https://user:placeholder@example.test'},undefined,async()=>{calls++;throw new TypeError('Invalid connection reached transport')})
 assert.equal(result.status,'unavailable')
 assert.equal(result.address,'Invalid or missing shop connection')
 assert.ok(!result.address.includes('placeholder'))
 assert.equal(calls,0)
})
