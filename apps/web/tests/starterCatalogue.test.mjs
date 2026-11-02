import assert from 'node:assert/strict'
import {test} from 'node:test'
import {readFile} from 'node:fs/promises'
import vm from 'node:vm'

// Read the static fallback without importing the browser/network application.
const source=await readFile(new URL('../src/api.ts',import.meta.url),'utf8')
const literal=/export const demoProducts:\s*Product\[\]\s*=\s*(\[[\s\S]*?\n\])/.exec(source)?.[1]
assert.ok(literal,'Starter fallback must remain inspectable catalogue data')
const fallback=JSON.parse(JSON.stringify(vm.runInNewContext(literal,Object.create(null),{timeout:100})))

test('frontend starter catalogue matches the canonical backend IDs, prices, stock and illustrative unit costs',async()=>{
 const canonical=JSON.parse(await readFile(new URL('../../../services/api/demo_catalogue.json',import.meta.url),'utf8'))
 const expected=canonical.products.map(product=>({...product,shop_id:canonical.shop.id}))
 const sorted=products=>[...products].sort((a,b)=>a.sku.localeCompare(b.sku))
 assert.deepEqual(sorted(fallback),sorted(expected))
 assert.equal(fallback.length,6)
 assert.ok(fallback.every(product=>Number.isSafeInteger(product.unit_cost_micros)&&product.unit_cost_micros>0))
 assert.ok(fallback.every(product=>!('cost_source_invoice_id' in product)),'Illustrative costs must not invent invoice evidence')
})
