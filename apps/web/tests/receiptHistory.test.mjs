import assert from 'node:assert/strict'
import {test} from 'node:test'
import {savedReceiptLines,savedReceiptPayment,sortedSavedReceipts,receiptMoney,receiptTender} from '../src/receiptHistory.ts'
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

test('verified saved names outrank renamed catalogue labels without using current price or stock',()=>{
 const snapshot={...sale,receipt_lines:[{product_id:'p1',product_name:'Original bread',quantity:2,unit_price_cents:1},{product_id:'deleted',product_name:'Saved old product',quantity:1,unit_price_cents:999}]}
 const lines=savedReceiptLines(snapshot,[{id:'p1',name:'Renamed bread',unit_price_cents:99999,stock_qty:1000}])
 assert.equal(lines[0].label,'Original bread')
 assert.equal(lines[0].historicalName,true)
 assert.equal(lines[0].currentName,false)
 assert.equal(lines[0].quantity,2)
 assert.equal(lines[0].stockAfter,7)
 assert.equal(lines[1].label,'Saved old product')
 assert.equal(snapshot.total_cents,300)
})

test('mismatched or duplicate optional label snapshots fall back honestly',()=>{
 const mismatch={...sale,receipt_lines:[{product_id:'p1',product_name:'Wrong quantity label',quantity:9},{product_id:'deleted',product_name:'Old',quantity:1}]}
 assert.equal(savedReceiptLines(mismatch,[{id:'p1',name:'Current bread'}])[0].label,'Current bread')
 const duplicate={...sale,receipt_lines:[{product_id:'p1',product_name:'One',quantity:2},{product_id:'p1',product_name:'Two',quantity:2}]}
 assert.equal(savedReceiptLines(duplicate,[])[0].label,'p1')
})

test('history sorting is read-only, newest first and rejects bad or wrong-shop records rather than fake empty',()=>{
 const newer={...sale,id:'new',created_at:'2026-11-02T10:00:00Z'}
 const original=[sale,newer]
 assert.deepEqual(sortedSavedReceipts(original,'shop-1').map(row=>row.id),['new','sale-1'])
 assert.equal(original[0].id,'sale-1')
 for(const records of [[sale,sale],[{...sale,created_at:'invalid'}],[{...sale,total_cents:-1}],[{...sale,shop_id:'other'}]])assert.throws(()=>sortedSavedReceipts(records,'shop-1'))
 assert.deepEqual(sortedSavedReceipts([],'shop-1'),[])
})

test('receipt display preserves exact saved cents, valid zero and legacy unknown payment',()=>{
 assert.equal(receiptMoney(0),'0.00')
 assert.equal(receiptMoney(75000000),'750000.00')
 assert.equal(receiptMoney(Number.MAX_SAFE_INTEGER),'90071992547409.91')
 assert.equal(receiptMoney(NaN),'Unavailable')
 assert.equal(receiptTender('bank'),'Bank')
 assert.deepEqual(savedReceiptPayment({...sale,total_cents:0,amount_received_cents:0,change_cents:0}),{received:0,change:0})
})
