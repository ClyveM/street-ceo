import assert from 'node:assert/strict'
import {test} from 'node:test'
import {checkShopReachability,localShopGuidance} from '../src/shopReachability.ts'
const config={baseUrl:'http://192.168.10.213:8001',shopId:'shop-1'}
test('shop connectivity requires readiness and matching scoped shop, independent of network-online indicators',async()=>{
 const calls=[]
 const result=await checkShopReachability(config,undefined,async(url,init)=>{calls.push([url,init]);return Response.json(new URL(url).pathname.endsWith('/readyz')?{status:'ready'}:{id:'shop-1'})})
 assert.equal(result.status,'connected');assert.equal(result.address,config.baseUrl);assert.ok(result.checkedAt>0)
 assert.equal(calls.length,2);assert.equal(calls[1][1].headers['X-Shop-ID'],'shop-1');assert.equal(calls[0][1].cache,'no-store');assert.ok(new URL(calls[0][0]).searchParams.has('connection_check'))
 for(const failed of [async()=>{throw new TypeError('network')},async(url)=>Response.json(new URL(url).pathname.endsWith('/readyz')?{status:'ready'}:{id:'other'}),async()=>new Response('',{status:503}),async()=>new Response('<!doctype html><title>Old cached shell</title>')])assert.equal((await checkShopReachability(config,undefined,failed)).status,'unavailable')
})
test('invalid secret-bearing addresses are never fetched or echoed and LAN guidance makes no universal mobile-data diagnosis',async()=>{
 const result=await checkShopReachability({...config,baseUrl:'http://user:secret@192.168.10.213:8001'},undefined,async()=>assert.fail('No network'))
 assert.equal(result.status,'unavailable');assert.doesNotMatch(JSON.stringify(result),/secret/)
 assert.match(localShopGuidance(config.baseUrl),/mobile data alone may not/)
 assert.doesNotMatch(localShopGuidance('https://shop.example'),/mobile data/)
})
