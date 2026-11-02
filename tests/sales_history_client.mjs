// Independent historical-label and saved-payment evidence acceptance.
import assert from 'node:assert/strict'
import {test} from 'node:test'
import {savedReceiptLines,savedReceiptPayment} from '../apps/web/src/receiptHistory.ts'
const sale={id:'receipt',shop_id:'shop',lines:[{product_id:'cola',quantity:2},{product_id:'deleted',quantity:1}],tender:'cash',total_cents:500,
 amount_received_cents:1000,change_cents:500,stock_after:{cola:16,deleted:4},created_at:'2026-11-02T18:00:00Z',
 receipt_lines:[{product_id:'cola',product_name:'Historic cola',sku:'OLD-COLA',quantity:2,unit_price_cents:150,line_total_cents:300},
 {product_id:'deleted',product_name:'Historic deleted product',sku:'OLD-ITEM',quantity:1,unit_price_cents:200,line_total_cents:200}]}

test('saved names, quantities and stock snapshots win over renamed or deleted current catalogue records',()=>{
 const lines=savedReceiptLines(sale,[{id:'cola',name:'Renamed cola',unit_price_cents:999999,stock_qty:999}])
 assert.deepEqual(lines.map(line=>line.label),['Historic cola','Historic deleted product'])
 assert.deepEqual(lines.map(line=>line.quantity),[2,1])
 assert.deepEqual(lines.map(line=>line.stockAfter),[16,4])
 assert.equal(sale.total_cents,500)
})

test('legacy names fall back to current catalogue or full product reference without reconstructing quantities',()=>{
 const legacy={...sale,receipt_lines:[],stock_after:{}}
 const lines=savedReceiptLines(legacy,[{id:'cola',name:'Current cola'}])
 assert.deepEqual(lines.map(line=>line.label),['Current cola','deleted'])
 assert.deepEqual(lines.map(line=>line.stockAfter),[null,null])
 assert.throws(()=>savedReceiptLines({...legacy,lines:[{product_id:'cola',quantity:0}]},[]))
})

test('legacy cash unknown received/change stays distinct from an explicit saved zero receipt',()=>{
 assert.deepEqual(savedReceiptPayment({...sale,amount_received_cents:null,change_cents:0}),{received:null,change:null})
 assert.deepEqual(savedReceiptPayment({...sale,amount_received_cents:undefined,change_cents:0}),{received:null,change:null})
 assert.deepEqual(savedReceiptPayment({...sale,total_cents:0,amount_received_cents:0,change_cents:0}),{received:0,change:0})
 assert.deepEqual(savedReceiptPayment(sale),{received:1000,change:500})
})

test('malformed saved payment values are not coerced or inferred from the sale total',()=>{
 assert.deepEqual(savedReceiptPayment({...sale,amount_received_cents:'1000',change_cents:-1}),{received:null,change:null})
 assert.deepEqual(savedReceiptPayment({...sale,amount_received_cents:Number.MAX_SAFE_INTEGER+1,change_cents:NaN}),{received:null,change:null})
})
