import assert from 'node:assert/strict'
import {test} from 'node:test'
import {savedReceiptLines,savedReceiptPayment} from '../src/receiptHistory.ts'
const sale={id:'sale-1',shop_id:'shop-1',lines:[{product_id:'p1',quantity:2},{product_id:'deleted',quantity:1}],tender:'cash',total_cents:300,amount_received_cents:500,change_cents:200,stock_after:{p1:7,deleted:4},created_at:'2026-11-01T12:00:00Z'}
test('history uses current catalogue labels but persisted quantities and stock snapshots, with full ID fallback',()=>{
 const lines=savedReceiptLines(sale,[{id:'p1',name:'Renamed product',stock_qty:999}])
 assert.deepEqual(lines[0],{productId:'p1',label:'Renamed product',currentName:true,quantity:2,stockAfter:7})
 assert.deepEqual(lines[1],{productId:'deleted',label:'deleted',currentName:false,quantity:1,stockAfter:4})
 assert.equal(savedReceiptLines({...sale,stock_after:{}},[])[0].stockAfter,null)
 assert.throws(()=>savedReceiptLines({...sale,lines:[{product_id:'p1',quantity:0}]},[]),/could not be verified/)
})
test('legacy cash null received never becomes exact-payment or zero-change evidence',()=>{
 assert.deepEqual(savedReceiptPayment(sale),{received:500,change:200})
 assert.deepEqual(savedReceiptPayment({...sale,amount_received_cents:null,change_cents:0}),{received:null,change:null})
 assert.deepEqual(savedReceiptPayment({...sale,amount_received_cents:undefined,change_cents:undefined}),{received:null,change:null})
 assert.deepEqual(savedReceiptPayment({...sale,tender:'bank',amount_received_cents:null,change_cents:0}),{received:null,change:0})
 assert.deepEqual(savedReceiptPayment({...sale,amount_received_cents:1.5,change_cents:-1}),{received:null,change:null})
})
