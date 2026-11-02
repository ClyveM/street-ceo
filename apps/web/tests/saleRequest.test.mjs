import assert from 'node:assert/strict'
import { test } from 'node:test'
import { requestSale, SaleRequestError } from '../src/saleRequest.ts'

const config = { baseUrl: 'https://shop.example', shopId: 'shop-1' }, input = { lines: [{ product_id: 'p1', quantity: 2 }], tender: 'bank' }
const receipt = { ...input, id: 'sale-1', shop_id: config.shopId, total_cents: 300, stock_after: { p1: 16 }, created_at: '2026-10-31T12:00:00Z' }

test('confirmed Cash/Bank sale sends explicit tender and stable key; returns authoritative stock', async () => {
  const keys = []
  const fetcher = async (url, init) => { assert.equal(url, 'https://shop.example/shops/shop-1/sales'); assert.equal(JSON.parse(init.body).tender, 'bank'); keys.push(init.headers['Idempotency-Key']); return Response.json(receipt) }
  assert.equal((await requestSale(config, input, 'logical-sale-1', fetcher)).stock_after.p1, 16)
  await requestSale(config, input, 'logical-sale-1', fetcher)
  assert.deepEqual(keys, ['logical-sale-1', 'logical-sale-1'])
  assert.equal((await requestSale(config, { ...input, tender: 'cash' }, 'cash-sale-1', async () => Response.json({ ...receipt, tender: 'cash' }))).tender, 'cash')
})

test('invalid tender/quantities never post; cross-shop or missing stock receipt cannot claim success', async () => {
  await assert.rejects(requestSale(config, { ...input, tender: 'card' }, 'key', async () => assert.fail('No request')), /Cash\/Bank/)
  await assert.rejects(requestSale(config, { ...input, lines: [{ product_id: 'p1', quantity: 0 }] }, 'key', async () => assert.fail('No request')), /quantities/)
  for (const value of [{ ...receipt, shop_id: 'other' }, { ...receipt, stock_after: {} }, { ...receipt, tender: 'cash' }, { ...receipt, lines: [null] }]) await assert.rejects(requestSale(config, input, 'key', async () => Response.json(value)), /Unreadable/)
})

test('ambiguous sale failure keeps uncertainty visible instead of claiming a safe fresh retry', async () => {
  await assert.rejects(requestSale(config, input, 'key', async () => { throw new TypeError('offline') }), /outcome is unknown/)
  await assert.rejects(requestSale(config, input, 'key', async () => new Response('', { status: 409 })), /Check stock and saved transactions/)
})

test('manual cash sends received amount and accepts only authoritative consistent change',async()=>{
 const cash={...input,tender:'cash',amount_received_cents:500}, saved={...receipt,tender:'cash',amount_received_cents:500,change_cents:200}
 const sale=await requestSale(config,cash,'cash-key',async(url,init)=>{assert.equal(JSON.parse(init.body).amount_received_cents,500);return Response.json(saved)})
 assert.equal(sale.change_cents,200)
 for(const invalid of [{...saved,change_cents:100},{...saved,amount_received_cents:600},{...saved,amount_received_cents:null}])await assert.rejects(requestSale(config,cash,'cash-key',async()=>Response.json(invalid)),error=>error instanceof SaleRequestError&&error.uncertain)
 for(const amount of [-1,1.5,Infinity])await assert.rejects(requestSale(config,{...cash,amount_received_cents:amount},'key',async()=>assert.fail('No network request')),error=>!error.uncertain)
})

test('manual mutation server errors remain uncertain and exact recovery keeps original payload and key',async()=>{
 const keys=[],bodies=[],cash={...input,tender:'cash',amount_received_cents:500}
 const fetcher=async(url,init)=>{keys.push(init.headers['Idempotency-Key']);bodies.push(init.body);return keys.length===1?Response.json({detail:'trace save failed'},{status:503}):Response.json({...receipt,tender:'cash',amount_received_cents:500,change_cents:200})}
 await assert.rejects(requestSale(config,cash,'original',fetcher),error=>error.uncertain)
 assert.equal((await requestSale(config,cash,'original',fetcher)).id,receipt.id)
 assert.deepEqual(keys,['original','original']);assert.equal(bodies[0],bodies[1])
})
