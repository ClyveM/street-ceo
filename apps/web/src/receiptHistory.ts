import type { Product, Sale } from './api'

/** Prefer verified saved labels; quantities and stock snapshots always come from the receipt. */
export function savedReceiptLines(sale: Sale, catalogue: Pick<Product, 'id' | 'name'>[]) {
  const names = new Map(catalogue.map((product) => [product.id, product.name]))
  if (!Array.isArray(sale.lines) || sale.lines.some((line) => !line || typeof line.product_id !== 'string' || !line.product_id || !Number.isSafeInteger(line.quantity) || line.quantity <= 0)) throw new Error('Saved receipt lines could not be verified.')
  const snapshots = sale.receipt_lines
  const validSnapshots = Array.isArray(snapshots) && snapshots.length === sale.lines.length && new Set(snapshots.map(item => item?.product_id)).size === snapshots.length && snapshots.every(item => item && typeof item.product_name === 'string' && item.product_name.trim() && sale.lines.some(line => line.product_id === item.product_id && line.quantity === item.quantity))
  const savedNames = new Map(validSnapshots ? snapshots.map(item => [item.product_id,item.product_name]) : [])
  return sale.lines.map((line) => {
    const name = names.get(line.product_id), stock = sale.stock_after?.[line.product_id]
    const savedName = savedNames.get(line.product_id)
    return { productId: line.product_id, label: savedName || name || line.product_id, currentName: !savedName && !!name, ...(savedName ? { historicalName: true } : {}), quantity: line.quantity, stockAfter: Number.isSafeInteger(stock) && stock >= 0 ? stock : null }
  })
}

export function savedReceiptPayment(sale: Sale) {
  const received = sale.amount_received_cents
  const knownReceived = typeof received === 'number' && Number.isSafeInteger(received) && received >= 0 ? received : null
  const change = typeof sale.change_cents === 'number' && Number.isSafeInteger(sale.change_cents) && sale.change_cents >= 0 ? sale.change_cents : null
  // A legacy cash receipt defaults change to zero without recording received cash.
  // That is not evidence the customer paid the exact amount.
  return { received: knownReceived, change: sale.tender === 'cash' && knownReceived === null ? null : change }
}

/** Read-only history validation and ordering; never drop bad rows and imply an empty shop. */
export function sortedSavedReceipts(sales: Sale[],shopId?:string): Sale[] {
 if(!Array.isArray(sales))throw new Error('Saved receipt history could not be verified.')
 const ids=new Set<string>()
 for(const sale of sales){
  if(!sale||typeof sale.id!=='string'||!sale.id||ids.has(sale.id)||typeof sale.shop_id!=='string'||!sale.shop_id||shopId&&sale.shop_id!==shopId||typeof sale.tender!=='string'||!sale.tender.trim()||!Number.isSafeInteger(sale.total_cents)||sale.total_cents<0||typeof sale.created_at!=='string'||!Number.isFinite(Date.parse(sale.created_at)))throw new Error('Some saved receipts could not be verified. Refresh history before relying on this list.')
  ids.add(sale.id)
 }
 return [...sales].sort((a,b)=>Date.parse(b.created_at)-Date.parse(a.created_at)||b.id.localeCompare(a.id))
}
export function receiptMoney(cents:number):string { if(!Number.isSafeInteger(cents)||cents<0)return 'Unavailable';const value=BigInt(cents);return `${value/100n}.${String(value%100n).padStart(2,'0')}` }
export function receiptTender(tender:string):string { return tender==='cash'?'Cash':tender==='bank'?'Bank':tender }
