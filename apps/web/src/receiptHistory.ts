import type { Product, Sale } from './api'

/** Product names are current labels; quantities and stock snapshots come only from the receipt. */
export function savedReceiptLines(sale: Sale, catalogue: Pick<Product, 'id' | 'name'>[]) {
  const names = new Map(catalogue.map((product) => [product.id, product.name]))
  if (!Array.isArray(sale.lines) || sale.lines.some((line) => !line || typeof line.product_id !== 'string' || !line.product_id || !Number.isSafeInteger(line.quantity) || line.quantity <= 0)) throw new Error('Saved receipt lines could not be verified.')
  return sale.lines.map((line) => {
    const name = names.get(line.product_id), stock = sale.stock_after?.[line.product_id]
    return { productId: line.product_id, label: name || line.product_id, currentName: !!name, quantity: line.quantity, stockAfter: Number.isSafeInteger(stock) && stock >= 0 ? stock : null }
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
