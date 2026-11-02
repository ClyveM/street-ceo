import assert from 'node:assert/strict'
import {test} from 'node:test'
import {filterStockProducts,stockPrice} from '../src/stockPresentation.ts'
import {checkShopReachability} from '../src/shopReachability.ts'
const products=[{id:'1',name:'Coca-Cola 300ml',sku:'COKE-300'},{id:'2',name:'Bread loaf',sku:'BREAD-700'}]
test('Stock search matches names and SKU case-insensitively without changing source data',()=>{
 assert.deepEqual(filterStockProducts(products,'  bread '),[products[1]])
 assert.deepEqual(filterStockProducts(products,'coke-300'),[products[0]])
 assert.deepEqual(filterStockProducts(products,'300ml'),[products[0]])
 assert.deepEqual(filterStockProducts(products,'not found'),[])
 assert.deepEqual(filterStockProducts(products,''),products)
 assert.equal(products.length,2)
})
test('stock sell prices use exact integer cents and never invent a currency',()=>{
 assert.equal(stockPrice(0),'0.00')
 assert.equal(stockPrice(150),'1.50')
 assert.equal(stockPrice(123456789),'1234567.89')
 assert.equal(stockPrice(Number.MAX_SAFE_INTEGER),'90071992547409.91')
 for(const invalid of [-1,1.5,NaN,Infinity,Number.MAX_SAFE_INTEGER+1])assert.equal(stockPrice(invalid),'Unavailable')
 assert.doesNotMatch(stockPrice(150),/USD|\$/)
})
test('table currency comes only from the already verified shop response',async()=>{
 const config={baseUrl:'https://shop.invalid',shopId:'shop-1'}
 for(const currency of ['USD','ZWL',undefined,'invented-currency']){
  let calls=0
  const result=await checkShopReachability(config,undefined,async url=>{calls++;return Response.json(new URL(url).pathname.endsWith('/readyz')?{status:'ready'}:{id:'shop-1',currency})})
  assert.equal(calls,2)
  assert.equal(result.currency,['USD','ZWL'].includes(currency)?currency:undefined)
 }
 const rejected=await checkShopReachability(config,undefined,async url=>Response.json(new URL(url).pathname.endsWith('/readyz')?{status:'ready'}:{id:'wrong-shop',currency:'USD'}))
 assert.equal(rejected.status,'unavailable')
 assert.equal(rejected.currency,undefined)
})
