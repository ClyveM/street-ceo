import assert from 'node:assert/strict'
import {test} from 'node:test'
import {requestInvestigations} from '../src/investigations.ts'
const config={baseUrl:'https://shop.example',shopId:'shop-1'},event={event_id:'e1',created_at:'2026-11-01T12:00:00Z',correlation_id:'corr-1',shop_id:'shop-1',operation:'POST /voice/transcript',phase:'completed',status_code:200,request:{transcript:'one coke'},response:{status:'needs_confirmation'}}
test('investigation requests use shop scope and encode optional correlation without changing saved payload',async()=>{
 const events=await requestInvestigations(config,'corr /1',undefined,async(url,init)=>{assert.equal(url,'https://shop.example/api/v1/shops/shop-1/investigations/requests?limit=20&correlation_id=corr+%2F1');assert.equal(init.headers['X-Shop-ID'],'shop-1');return Response.json({shop_id:'shop-1',events:[event]})})
 assert.equal(events[0].response.status,'needs_confirmation')
})
test('cross-shop, malformed timestamps and invalid event labels cannot render as verified history',async()=>{
 for(const result of [{shop_id:'other',events:[event]},{shop_id:'shop-1',events:[{...event,shop_id:'other'}]},{shop_id:'shop-1',events:[{...event,created_at:'bad'}]},{shop_id:'shop-1',events:[{...event,operation:{bad:true}}]}])await assert.rejects(requestInvestigations(config,'',undefined,async()=>Response.json(result)),/could not be verified|invalid event/)
})
test('empty history is valid but storage/network errors remain errors and never fixtures',async()=>{
 assert.deepEqual(await requestInvestigations(config,'',undefined,async()=>Response.json({shop_id:'shop-1',events:[]})),[])
 await assert.rejects(requestInvestigations(config,'',undefined,async()=>new Response('',{status:503})),/unavailable \(503\)/)
 await assert.rejects(requestInvestigations(config,'x'.repeat(121),undefined,async()=>assert.fail('No request')),/120/)
})

test('existing Muse trace with null provider metadata remains unknown rather than false or invalid',async()=>{
 const saved={...event,operation:'POST /api/v1/shops/shop-1/muse',provider_called:null,response:{status:'answered',source:'repository'}}
 const events=await requestInvestigations(config,'',undefined,async()=>Response.json({shop_id:'shop-1',events:[saved]}))
 assert.equal(events[0].provider_called,null)
 assert.equal(events[0].response.source,'repository')
 await assert.rejects(requestInvestigations(config,'',undefined,async()=>Response.json({shop_id:'shop-1',events:[{...saved,provider_called:'yes'}]})),/invalid event/)
})

test('oversized saved event preserves its partial sanitized prefix and routing metadata without inventing complete content',async()=>{
 const saved={event_id:event.event_id,created_at:event.created_at,correlation_id:event.correlation_id,shop_id:event.shop_id,operation:'muse',phase:'completed',payload:{truncated:true,sanitized_prefix:'{"response":{"text":"Partial sanitized text'}}
 const events=await requestInvestigations(config,'',undefined,async()=>Response.json({shop_id:'shop-1',events:[saved]}))
 assert.equal(events[0].payload.truncated,true)
 assert.equal(events[0].payload.sanitized_prefix,saved.payload.sanitized_prefix)
 assert.equal(events[0].response,undefined)
 for(const payload of [{truncated:false,sanitized_prefix:'text'},{truncated:true,sanitized_prefix:{}},{truncated:true,sanitized_prefix:'x'.repeat(16001)}])await assert.rejects(requestInvestigations(config,'',undefined,async()=>Response.json({shop_id:'shop-1',events:[{...saved,payload}]})),/partial request payload/)
})
