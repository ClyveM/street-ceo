import assert from 'node:assert/strict'
import {test} from 'node:test'
import {createRetailClient,parseStockTakeHistory} from '../src/retailContracts.ts'
const config={baseUrl:'https://shop.invalid',shopId:'shop-1'}
const draft={id:'a',shop_id:'shop-1',mode:'on_demand',count_date:'2026-11-02',actor:'Owner',notes:'Morning count',lines:[{product_id:'p1',counted_qty:0}],expected_snapshot:{p1:3},status:'draft',created_at:'2026-11-02T10:00:00Z',confirmed_at:null}
test('history preserves saved baselines, true zero counts, actor and notes with newest first',()=>{
 const newer={...draft,id:'b',status:'confirmed',created_at:'2026-11-02T11:00:00Z',confirmed_at:'2026-11-02T11:01:00Z'}
 const records=parseStockTakeHistory([draft,newer],config.shopId)
 assert.deepEqual(records.map(r=>r.id),['b','a'])
 assert.equal(records[0].expected_snapshot.p1,3)
 assert.equal(records[0].lines[0].counted_qty,0)
 assert.equal(records[0].notes,'Morning count')
 assert.equal(records[1].actor,'Owner')
 assert.deepEqual(parseStockTakeHistory([],config.shopId),[])
})
test('history rejects duplicate receipts, wrong shop, invalid state and absent baseline',()=>{
 assert.throws(()=>parseStockTakeHistory([draft,draft],config.shopId),/duplicate/)
 assert.throws(()=>parseStockTakeHistory([{...draft,shop_id:'other'}],config.shopId))
 assert.throws(()=>parseStockTakeHistory([{...draft,status:'confirmed'}],config.shopId),/confirmation date/)
 assert.throws(()=>parseStockTakeHistory([{...draft,confirmed_at:'2026-11-02T11:00:00Z'}],config.shopId),/confirmation date/)
 assert.throws(()=>parseStockTakeHistory([{...draft,expected_snapshot:{}}],config.shopId),/baseline/)
 assert.throws(()=>parseStockTakeHistory({items:[draft]},config.shopId))
})
test('history GET and item GET are scoped, read-only and validated before opening',async()=>{
 const calls=[]
 const client=createRetailClient(()=>config,async(url,init)=>{calls.push({url,init});return Response.json(url.endsWith('/stock-takes')?[draft]:draft)})
 assert.equal((await client.listStockTakes())[0].id,'a')
 assert.equal((await client.getStockTake('a')).status,'draft')
 assert.equal(calls[0].url,'https://shop.invalid/api/v1/shops/shop-1/stock-takes')
 assert.equal(calls[0].init.method,'GET')
 assert.equal(calls[0].init.headers['X-Shop-ID'],'shop-1')
 assert.equal(calls[0].init.body,undefined)
})
