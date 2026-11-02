// Independent real-contract fixtures and simulated transport only; never Meta/API calls.
import assert from 'node:assert/strict'
import {test} from 'node:test'
import {apoCommand,confirmVoiceMatch,createQuickSaleClient,matchAnswer,parseVoiceReview} from '../apps/web/src/quickSale.ts'
import {WakeCommand} from '../apps/web/src/wakePhrase.ts'

const shop='00000000-0000-0000-0000-000000000001'
const config={baseUrl:'http://example.test:8001',shopId:shop}
const proposed={request_id:'proposal-1',shop_id:shop,input_kind:'transcript',status:'needs_match_confirmation',transcript:'one bread glove number',intent:{action:'record_sale',item:'Bread loaf',quantity:1,needs_confirmation:true},lines:[{product_id:'bread-id',product_name:'Bread loaf',quantity:1}],requires_match_confirmation:true,clarification_question:'Did you mean 1 Bread loaf? Please say yes or no.',resolution_source:'muse_catalogue',provider_called:true}

test('actual proposal shape is not committable until explicit Yes and cannot bypass the guard',async()=>{
 const review=parseVoiceReview(proposed,shop)
 assert.equal(review.canCommit,false)
 assert.equal(review.requiresMatchConfirmation,true)
 let sent=0
 const client=createQuickSaleClient(()=>config,async()=>{sent++;throw new TypeError('must not reach transport')})
 for(const basket of [review,{...review,canCommit:true}])await assert.rejects(client.commit(basket,{tender:'bank'},'no-confirmation'))
 assert.equal(sent,0)
 assert.equal(confirmVoiceMatch(review).matchConfirmed,true)
})

test('Yes-confirmed proposal sends explicit match approval before asking for payment',async()=>{
 const review=confirmVoiceMatch(parseVoiceReview(proposed,shop)),sent=[]
 const client=createQuickSaleClient(()=>config,async(url,init)=>{sent.push(JSON.parse(init.body));return Response.json({status:'needs_tender',review_id:'proposal-1',question:'Cash or bank?',allowed_tenders:['cash','bank'],amount_due_cents:180,missing:['tender']})})
 const result=await client.commit(review,null,'original-proposal-key')
 assert.equal(result.kind,'question')
 assert.deepEqual(sent,[{review_id:'proposal-1',lines:[{product_id:'bread-id',quantity:1}],match_confirmed:true}])
 assert.equal(result.sale,undefined)
})

test('missing-quantity replies preserve clarification context without inventing lines or calling commit',async()=>{
 const body={...proposed,request_id:'clarify-1',status:'needs_clarification',transcript:'Coca-Cola',intent:null,lines:[],requires_match_confirmation:false,clarification_question:'How many Coca-Cola 300ml?',clarification_code:'missing_quantity',resolution_source:'local_clarification',provider_called:false}
 const review=parseVoiceReview(body,shop)
 assert.equal(review.canCommit,false)
 assert.deepEqual(review.lines,[])
 const requests=[]
 const client=createQuickSaleClient(()=>config,async(url,init)=>{requests.push({url,key:init.headers['Idempotency-Key'],body:JSON.parse(init.body)});return Response.json(proposed)})
 await client.interpret('two','quantity-reply',undefined,'clarify-1')
 assert.deepEqual(requests[0].body,{transcript:'two',clarification_of:'clarify-1'})
 assert.ok(requests[0].url.endsWith('/transcript'))
 assert.equal(requests[0].key,'quantity-reply')
})

test('No Cancel and ordinary words never count as affirmative catalogue approval',()=>{
 assert.equal(matchAnswer('No'),'no')
 assert.equal(matchAnswer('Cancel'),'cancel')
 assert.equal(matchAnswer('Apo Yes Napo'),'yes')
 for(const value of ['yes no','not correct','yesterday','one Coke'])assert.equal(matchAnswer(value),null)
 assert.throws(()=>confirmVoiceMatch(parseVoiceReview({...proposed,status:'needs_clarification',intent:null,lines:[],requires_match_confirmation:false},shop)))
})

test('heard product noise survives framing while only terminal nabo closes the wake command',()=>{
 const heard='Apo one coca-cola nabo marble Napo'
 assert.equal(apoCommand(heard).heardBody,'one coca-cola nabo marble')
 const wake=new WakeCommand()
 assert.equal(wake.accept('Apo one coca-cola nabo marble Napo',{apo:'apo',napo:'napo'}),'Apo one coca-cola nabo marble Napo')
 assert.equal(new WakeCommand().accept('Apo one bread glove number nabo',{apo:'apo',napo:'napo'}),'Apo one bread glove number Napo')
})

test('proposal missing intent or a whole line fails closed rather than claiming confirmation',()=>{
 assert.throws(()=>parseVoiceReview({...proposed,intent:null},shop))
 assert.throws(()=>parseVoiceReview({...proposed,lines:[]},shop))
 assert.throws(()=>parseVoiceReview({...proposed,lines:[...proposed.lines,...proposed.lines]},shop))
 assert.throws(()=>parseVoiceReview({...proposed,shop_id:'other-shop'},shop))
})
