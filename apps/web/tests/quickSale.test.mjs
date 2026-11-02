import assert from 'node:assert/strict'
import { test } from 'node:test'
import { apoCommand, cashAmountCents, cancelPayment, catalogueMatchQuestion, confirmVoiceMatch, createQuickSaleClient, eligibleForQuickSale, matchAnswer, parseQuickReceipt, parseVoiceReview, paymentCommand, QuickSaleError, readSaleMode, spokenCashCents, tenderAnswer } from '../src/quickSale.ts'

const config = { baseUrl: 'https://shop.example', shopId: 'shop-1' }
const response = { request_id: 'review-1', shop_id: config.shopId, transcript: '1 coke', status: 'needs_confirmation', intent: { action: 'record_sale', needs_confirmation: true }, lines: [{ product_id: 'p1', product_name: 'Coca-Cola', quantity: 1 }] }
const review = parseVoiceReview(response, config.shopId)
const question = { status: 'needs_tender', review_id: review.reviewId, question: 'Cash or Bank?', amount_due_cents: 150, allowed_tenders: ['cash', 'bank'], missing: ['tender'] }
const receipt = { id: 'sale-1', shop_id: config.shopId, lines: [{ product_id: 'p1', quantity: 1 }], tender: 'cash', total_cents: 150, amount_received_cents: 10000, change_cents: 9850, stock_after: { p1: 17 }, created_at: '2026-10-31T19:00:00Z' }

test('Quick Sale is the default; Review persists only when explicitly selected', () => {
  assert.equal(readSaleMode(), 'quick')
  assert.equal(readSaleMode({ getItem: () => null }), 'quick')
  assert.equal(readSaleMode({ getItem: () => 'review' }), 'review')
  assert.equal(readSaleMode({ getItem: () => 'old-invalid-mode' }), 'quick')
  assert.equal(readSaleMode({ getItem: () => { throw new Error('storage denied') } }), 'quick')
})

test('only complete closing Apo plus verified catalogue quantities is eligible for automatic progression', () => {
  assert.equal(eligibleForQuickSale(apoCommand('Apo 1 Coke Apo'), review), true)
  assert.equal(eligibleForQuickSale(apoCommand('1 Coke'), review), false)
  assert.equal(eligibleForQuickSale(apoCommand('Apo 1 Coke'), review), false)
  assert.equal(eligibleForQuickSale(apoCommand('Apo 1 Coke and maybe more Apo'), review), false)
  assert.equal(eligibleForQuickSale(apoCommand('Apo 2 Coke Apo'), review), false)
  assert.equal(eligibleForQuickSale(apoCommand('Apo 1 Coke Apo'), { ...review, canCommit: false }), false)
  assert.deepEqual(apoCommand('Apo 1 Coke Cash 100 Apo').tender, { tender: 'cash', amount_received_cents: 10000 })
})

test('Cash, Cash 100 and Bank answers are exact, bounded and never guessed from ambiguous speech', () => {
  assert.deepEqual(tenderAnswer('Cash'), { tender: 'cash' })
  assert.deepEqual(tenderAnswer('Cash 100'), { tender: 'cash', amount_received_cents: 10000 })
  assert.deepEqual(tenderAnswer('cash 2.50.'), { tender: 'cash', amount_received_cents: 250 })
  assert.deepEqual(tenderAnswer('Bank'), { tender: 'bank' })
  for (const value of ['maybe bank', 'cash five fifty', 'cash 1.001', 'cash -5', 'cash 99999999999999999']) assert.equal(tenderAnswer(value), null)
})

test('cash words and decimal phrases preserve cents exactly and reject ambiguous or excessive precision',()=>{
 for(const [phrase,cents] of [['five point five',550],['five point five zero',550],['five dollars and fifty cents',550],['twenty-five dollars',2500],['one hundred and five dollars',10500],['fifty cents',50],['zero dollars one cent',1],['10.05',1005]])assert.equal(spokenCashCents(phrase),cents,phrase)
 for(const phrase of ['five fifty','five point fifty','five point five zero zero','five dollars one hundred cents','minus five','one one','one hundred and','5.001','-5'])assert.equal(spokenCashCents(phrase),null,phrase)
 for(const [value,cents] of [['0',0],['1.05',105],['100.5',10050]])assert.equal(cashAmountCents(value),cents)
 for(const value of ['','1e2','1.001','1,000','-1','Infinity','99999999999999999'])assert.equal(cashAmountCents(value),null)
 assert.equal(tenderAnswer(paymentCommand('Apo cash one hundred dollars Napo')).amount_received_cents,10000)
 assert.equal(tenderAnswer(paymentCommand('cash five dollars and fifty cents')).amount_received_cents,550)
 assert.equal(apoCommand('Apo one Coke cash five dollars and fifty cents Napo').tender.amount_received_cents,550)
})

test('hands-free framed tender answers preserve the whole payment answer', () => {
  assert.deepEqual(tenderAnswer(apoCommand('Apo Cash 100 Napo').body), { tender: 'cash', amount_received_cents: 10000 })
  assert.deepEqual(tenderAnswer(apoCommand('Apo Cash 1.50 Napo').body), { tender: 'cash', amount_received_cents: 150 })
  assert.deepEqual(tenderAnswer(apoCommand('Apo Bank Napo').body), { tender: 'bank' })
  assert.equal(tenderAnswer(apoCommand('Apo 1 Coke Cash 100 Napo').body), null)
})

test('spoken quantity words and full catalogue names can progress only with matching reviewed lines', () => {
  const basket = { ...review, lines: [review.lines[0], { product_id: 'p2', product_name: 'Bath soap', quantity: 2 }] }
  const command = apoCommand('Apo sell one Coke and two Bath soap Napo')
  assert.equal(command.body, '1 Coke 2 Bath soap')
  assert.equal(eligibleForQuickSale(command, basket), true)
  assert.equal(eligibleForQuickSale(apoCommand('Apo one Coke and two unknown Napo'), basket), false)
  assert.equal(eligibleForQuickSale(command, { ...basket, lines: [basket.lines[0]] }), false)
  assert.equal(eligibleForQuickSale(apoCommand('Apo one Coke maybe more Napo'), review), false)
  assert.equal(eligibleForQuickSale(apoCommand('Apo one Coca Cola Napo'), review), true)
})

test('prompted cash can use a spoken amount; a bare amount is never tender without an amount question', () => {
  assert.deepEqual(tenderAnswer('cash five'), { tender: 'cash', amount_received_cents: 500 })
  assert.deepEqual(tenderAnswer('cash ten dollars'), { tender: 'cash', amount_received_cents: 1000 })
  assert.deepEqual(tenderAnswer('five dollars', true), { tender: 'cash', amount_received_cents: 500 })
  assert.deepEqual(tenderAnswer('5.50', true), { tender: 'cash', amount_received_cents: 550 })
  assert.equal(tenderAnswer('five dollars'), null)
  assert.equal(tenderAnswer('maybe five', true), null)
  assert.deepEqual(apoCommand('Apo one Coke cash five Napo').tender, { tender: 'cash', amount_received_cents: 500 })
})

test('missing-product responses retain investigation code and cannot become a sale review', () => {
  assert.throws(() => parseVoiceReview({ ...response, status: 'rejected', error: 'Product not found', error_code: 'product_not_found' }, config.shopId), (error) => error.code === 'product_not_found' && !error.uncertain)
})

test('only explicit cancellation phrases discard an unpaid basket',()=>{
 for(const phrase of ['cancel','Cancel sale.','cancel basket'])assert.equal(cancelPayment(phrase),true)
 for(const phrase of ['do not cancel','cash','cancelled','cancel and sell one coke'])assert.equal(cancelPayment(phrase),false)
})

test('transcript and audio connectivity failures are retryable without unknown-sale claims', async () => {
  for (const fetcher of [async () => { throw new TypeError('network failed') }, async () => new Response('not json')]) {
    const failed = createQuickSaleClient(() => config, fetcher)
    for (const request of [() => failed.interpret('1 coke', 'review-key'), () => failed.audio('YQ==', 'audio/webm', 'audio-key')]) {
      await assert.rejects(request(), (error) => error instanceof QuickSaleError && !error.uncertain && error.code === 'voice_connection' && /No sale was submitted/.test(error.message) && !/outcome is unknown/.test(error.message))
    }
  }
})

test('uncertain commit and undo recover through their original unchanged key', async () => {
  const keys = [], paths = []
  const client = createQuickSaleClient(() => config, async (url, init) => { keys.push(init.headers['Idempotency-Key']); paths.push(url); throw new TypeError('network failed') })
  for (let i = 0; i < 2; i++) await assert.rejects(client.commit(review, { tender: 'cash', amount_received_cents: 10000 }, 'original-sale-key'), (error) => error.uncertain)
  for (let i = 0; i < 2; i++) await assert.rejects(client.undo(receipt, 'original-undo-key'), (error) => error.uncertain)
  assert.deepEqual(keys, ['original-sale-key', 'original-sale-key', 'original-undo-key', 'original-undo-key'])
  assert.ok(paths.slice(0, 2).every((url) => url.endsWith('/commit')))
  assert.ok(paths.slice(2).every((url) => url.endsWith('/undo')))
})

test('mutating server errors freeze new sales and retain original keys for recovery, while interpretation remains retryable', async () => {
 const keys=[]
 const client=createQuickSaleClient(()=>config,async(url,init)=>{keys.push(init.headers['Idempotency-Key']);return Response.json({detail:'Trace persistence failed; retry the same key'},{status:503})})
 for(let i=0;i<2;i++)await assert.rejects(client.commit(review,{tender:'cash',amount_received_cents:10000},'stable-commit'),error=>error.uncertain&&error.code==='503')
 for(let i=0;i<2;i++)await assert.rejects(client.undo(receipt,'stable-undo'),error=>error.uncertain&&error.code==='503')
 assert.deepEqual(keys,['stable-commit','stable-commit','stable-undo','stable-undo'])
 await assert.rejects(client.interpret('1 Coke','review'),error=>!error.uncertain)
})

test('actual needs_tender 200 response is a payment question, never a receipt or uncertain outcome',async()=>{
 const payload={status:'needs_tender',review_id:review.reviewId,question:'Should I record this sale as cash or bank?',allowed_tenders:['cash','bank'],amount_due_cents:150,missing:['tender']}
 const client=createQuickSaleClient(()=>config,async()=>Response.json(payload))
 const result=await client.commit(review,null,'question-key')
 assert.equal(result.kind,'question');assert.equal(result.amount_due_cents,150);assert.equal(result.question,payload.question);assert.equal(result.sale,undefined)
 const cashClient=createQuickSaleClient(()=>config,async()=>Response.json({...payload,question:'How much cash did you receive? The total is 150 cents.',missing:['amount_received_cents']}))
 assert.deepEqual((await cashClient.commit(review,{tender:'cash'},'question-key')).missing,['amount_received_cents'])
})

test('failed question-only requests are safely retryable with same reference; complete cash, bank and undo stay uncertain',async()=>{
 for(const answer of [null,{tender:'cash'}]){
  for(const failed of [async()=>{throw new TypeError('network')},async()=>Response.json({detail:'unavailable'},{status:503}),async()=>new Response('not json')]){
   const client=createQuickSaleClient(()=>config,failed)
   await assert.rejects(client.commit(review,answer,'same-question'),error=>!error.uncertain&&error.code==='payment_question_connection'&&!/outcome is unknown/.test(error.message))
  }
 }
 for(const answer of [{tender:'bank'},{tender:'cash',amount_received_cents:0},{tender:'cash',amount_received_cents:500}]){
  const client=createQuickSaleClient(()=>config,async()=>{throw new TypeError('network')})
  await assert.rejects(client.commit(review,answer,'paid-key'),error=>error.uncertain)
 }
 const bodies=[],keys=[]
 const retry=createQuickSaleClient(()=>config,async(url,init)=>{bodies.push(init.body);keys.push(init.headers['Idempotency-Key']);return bodies.length===1?Response.json({}, {status:503}):Response.json(question)})
 await assert.rejects(retry.commit(review,null,'question-reference'),error=>!error.uncertain)
 assert.equal((await retry.commit(review,null,'question-reference')).kind,'question')
 assert.deepEqual(keys,['question-reference','question-reference']);assert.equal(bodies[0],bodies[1])
})

test('invalid runtime tender or amount cannot be sent and misclassified as a safe payment question',async()=>{
 const client=createQuickSaleClient(()=>config,async()=>assert.fail('Invalid payment must not reach server'))
 for(const tender of ['cash','bank'])for(const amount of [true,'500',1.5,-1,Number.MAX_SAFE_INTEGER+1])await assert.rejects(client.commit(review,{tender,amount_received_cents:amount},'key'),error=>!error.uncertain&&/No payment request was sent/.test(error.message))
 for(const tender of ['card','cash or bank'])await assert.rejects(client.commit(review,{tender},'key'),/No payment request was sent/)
})

test('interpretation is shop-scoped; unavailable/ambiguous responses cannot authorize a sale', () => {
  assert.throws(() => parseVoiceReview({ ...response, shop_id: 'other' }, config.shopId), /verified/)
  assert.throws(() => parseVoiceReview({ ...response, lines: [...response.lines, ...response.lines] }, config.shopId), /quantities/)
  assert.equal(parseVoiceReview({ ...response, intent: { action: 'unknown' } }, config.shopId).canCommit, false)
  assert.throws(() => parseVoiceReview({ status: 'unavailable', error: 'Speech service unavailable' }, config.shopId), /Speech service unavailable/)
})

test('nonexact catalogue proposals require explicit yes before tender and exact legacy requests omit the new flag',async()=>{
 const proposal=parseVoiceReview({...response,transcript:'1 bread glove number',status:'needs_match_confirmation',requires_match_confirmation:true,resolution_source:'muse_catalogue',provider_called:true,clarification_question:'Did you mean 1 Bread loaf? Say yes or no.',lines:[{product_id:'bread',product_name:'Bread loaf',quantity:1}]},config.shopId)
 assert.equal(proposal.canCommit,false);assert.equal(proposal.providerCalled,true)
 const bodies=[]
 const client=createQuickSaleClient(()=>config,async(url,init)=>{const body=JSON.parse(init.body);bodies.push(body);return Response.json({...question,review_id:body.review_id})})
 await assert.rejects(client.commit(proposal,null,'proposal'),/verified sale review/)
 await assert.rejects(client.commit({...proposal,canCommit:true},null,'proposal'),/Say Yes/)
 assert.equal(bodies.length,0)
 const confirmed=confirmVoiceMatch(proposal)
 assert.equal(proposal.canCommit,false);assert.equal(confirmed.matchConfirmed,true)
 assert.equal((await client.commit(confirmed,null,'proposal')).kind,'question')
 assert.equal(bodies[0].match_confirmed,true);assert.equal(bodies[0].tender,undefined)
 await client.commit(review,null,'exact');assert.equal('match_confirmed' in bodies[1],false)
  const exactCorrection=confirmVoiceMatch(review)
  assert.equal(exactCorrection.requiresMatchConfirmation,false)
  assert.match(catalogueMatchQuestion(exactCorrection),/Did you mean 1 Coca-Cola/)
 for(const reply of ['yes and add sugar','not yes','maybe','no idea','cancel and sell'])assert.equal(matchAnswer(reply),null,reply)
 assert.equal(matchAnswer('Yes.'),'yes');assert.equal(matchAnswer('Apo No Napo'),'no');assert.equal(matchAnswer('Cancel'),'cancel')
})

test('quantity followup sends explicit reply plus prior review context without guessing or auto-confirming',async()=>{
 const first=parseVoiceReview({...response,transcript:'coca-cola',status:'needs_clarification',intent:null,lines:[],requires_match_confirmation:false,clarification_question:'How many Coca-Cola 300ml?',resolution_source:'muse_catalogue',provider_called:true},config.shopId)
 assert.equal(first.canCommit,false);assert.equal(first.lines.length,0)
 assert.throws(()=>confirmVoiceMatch(first),/no grounded product proposal/)
 const client=createQuickSaleClient(()=>config,async(url,init)=>{assert.deepEqual(JSON.parse(init.body),{transcript:'one',clarification_of:first.reviewId});return Response.json({...response,transcript:'one coca-cola',status:'needs_match_confirmation',requires_match_confirmation:true,clarification_question:'Did you mean 1 Coca-Cola?',resolution_source:'local_clarification',provider_called:false})})
 const next=await client.interpret('one','followup',undefined,first.reviewId)
 assert.equal(next.requiresMatchConfirmation,true);assert.equal(next.canCommit,false);assert.equal(next.resolutionSource,'local_clarification')
 assert.equal(parseVoiceReview({...response,resolution_source:null,provider_called:false},config.shopId).canCommit,true)
})

test('actual noisy catalogue phrases retain every heard product word for grounded clarification',()=>{
 for(const phrase of ['1 bread glove number','1 coca-cola nabo marble','bath soap nabo maple map','coca-cola']){
  const parsed=apoCommand(`Apo ${phrase} Napo`)
  assert.equal(parsed.heardBody,phrase)
  assert.equal(eligibleForQuickSale(parsed,review),false)
 }
 assert.equal(apoCommand('Apo one Coke and two sugar Napo').heardBody,'one Coke and two sugar')
})

test('closing-Apo boundary asks missing tender then accepts Cash 100 without another confirmation endpoint', async () => {
  const calls = []
  const client = createQuickSaleClient(() => config, async (url, init) => {
    calls.push({ url, key: init.headers['Idempotency-Key'], body: JSON.parse(init.body) })
    return Response.json(calls.length === 1 ? question : receipt)
  })
  const first = await client.commit(review, null, 'voice-sale-review-1')
  assert.equal(first.kind, 'question')
  assert.equal(calls[0].body.tender, undefined)
  const final = await client.commit(review, tenderAnswer('Cash 100'), 'voice-sale-review-1')
  assert.equal(final.kind, 'sale')
  assert.equal(final.sale.change_cents, 9850)
  assert.ok(calls.every((call) => call.url.endsWith('/voice/commit') && call.key === 'voice-sale-review-1'))
  assert.equal(calls[1].body.amount_received_cents, 10000)
})

test('Bank receipt is exact total with zero change; insufficient cash remains a recoverable question exception', async () => {
  const bank = { ...receipt, tender: 'bank', amount_received_cents: 150, change_cents: 0 }
  const client = createQuickSaleClient(() => config, async () => Response.json(bank))
  assert.equal((await client.commit(review, { tender: 'bank' }, 'bank-key')).sale.change_cents, 0)
  const short = createQuickSaleClient(() => config, async () => Response.json({ detail: { code: 'insufficient_cash', message: 'Cash received is less than the sale total.' } }, { status: 409 }))
  await assert.rejects(short.commit(review, { tender: 'cash', amount_received_cents: 100 }, 'cash-key'), (error) => error instanceof QuickSaleError && !error.uncertain && error.code === 'insufficient_cash')
})

test('no fake success for missing stock, incorrect change, cross-shop receipt or uncertain transport', async () => {
  for (const value of [{ ...receipt, stock_after: {} }, { ...receipt, change_cents: 0 }, { ...receipt, shop_id: 'other' }]) assert.throws(() => parseQuickReceipt(value, review), (error) => error.uncertain === true)
  const offline = createQuickSaleClient(() => config, async () => { throw new TypeError('offline') })
  await assert.rejects(offline.commit(review, { tender: 'bank' }, 'same-key'), (error) => error.uncertain === true)
  const unused = createQuickSaleClient(() => config, async () => assert.fail('No POST expected'))
  await assert.rejects(unused.commit({ ...review, canCommit: false }, null, 'key'), /verified sale review/)
})

test('Undo uses the verified reversal route and matching receipt; exact retry keeps its key', async () => {
  const reversed = { reversal_id: 'rev-1', audit_id: 'audit-1', original_sale_id: receipt.id, shop_id: config.shopId, status: 'reversed', lines: receipt.lines, actor: 'Shop operator', reason: 'User selected Undo last sale', created_at: receipt.created_at }
  const keys = []
  const client = createQuickSaleClient(() => config, async (url, init) => { assert.match(url, /voice\/commit\/sale-1\/undo$/); assert.equal(JSON.parse(init.body).confirmed, true); keys.push(init.headers['Idempotency-Key']); return Response.json(reversed) })
  assert.equal((await client.undo(receipt, 'undo-sale-1')).audit_id, 'audit-1')
  await client.undo(receipt, 'undo-sale-1'); assert.deepEqual(keys, ['undo-sale-1', 'undo-sale-1'])
  const wrong = createQuickSaleClient(() => config, async () => Response.json({ ...reversed, original_sale_id: 'another-sale' }))
  await assert.rejects(wrong.undo(receipt, 'key'), /unverified/)
})

test('fast local catalogue proposal retains provenance and cannot reach payment before explicit Yes', async () => {
  const proposal = parseVoiceReview({ ...response, status: 'needs_match_confirmation', requires_match_confirmation: true, resolution_source: 'local_catalogue_proposal', provider_called: false, clarification_question: 'Did you mean 1 Coca-Cola? Say yes or no.' }, config.shopId)
  assert.equal(proposal.providerCalled, false)
  assert.equal(proposal.resolutionSource, 'local_catalogue_proposal')
  assert.equal(proposal.canCommit, false)
  const calls = []
  const client = createQuickSaleClient(() => config, async (_url, init) => { calls.push(JSON.parse(init.body)); return Response.json(question) })
  await assert.rejects(client.commit(proposal, null, 'proposal-key'), /verified sale review/)
  assert.equal(calls.length, 0)
  const confirmed = confirmVoiceMatch(proposal)
  assert.equal((await client.commit(confirmed, null, 'proposal-key')).kind, 'question')
  assert.equal(calls[0].match_confirmed, true)
  assert.equal(calls[0].tender, undefined)
})
