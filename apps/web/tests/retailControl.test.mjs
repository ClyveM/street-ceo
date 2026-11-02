import assert from 'node:assert/strict'
import { test } from 'node:test'
import { costToMicros, createRetailClient, parseClosePreview, parsePurchase, parseStockTake, sumPurchaseLines, validatePurchase, validateStockTake } from '../src/retailContracts.ts'

const config = { baseUrl: 'https://shop.example', shopId: 'shop-1' }, stamp = '2026-10-31T12:00:00Z'
const existing = { product_id: 'p1', sku: null, name: null, unit_price_cents: null, quantity: 2, purchase_unit_cost_micros: 1200000, line_total_micros: 2400000 }
const newProduct = { product_id: null, sku: 'NEW-1', name: 'New item', unit_price_cents: 100, quantity: 3, purchase_unit_cost_micros: 500000, line_total_micros: 1500000 }
const purchase = { kind: 'manual', reference: 'QA-PUR-1', purchase_date: '2026-10-31', actor: 'Synthetic QA', supplier: null, tender: 'unpaid', notes: 'Synthetic review only', lines: [existing, newProduct], total_cost_micros: 3900000 }
const saved = { ...purchase, id: 'pur-1', shop_id: config.shopId, status: 'draft', created_at: stamp, confirmed_at: null }
const count = { mode: 'monthly', count_date: '2026-10-31', actor: 'Synthetic QA', notes: 'Physical test count', lines: [{ product_id: 'p1', counted_qty: 0 }] }
const countRecord = { ...count, id: 'count-1', shop_id: config.shopId, status: 'draft', created_at: stamp, confirmed_at: null, expected_snapshot: { p1: 2 } }

test('purchase costs retain exact six-decimal precision without rounding or unsafe totals', () => {
  assert.equal(costToMicros('1.000001'), 1000001)
  assert.equal(costToMicros('0'), 0)
  assert.equal(sumPurchaseLines([existing, newProduct]), 3900000)
  for (const value of ['1.0000001', '-1', '1e6', '', '99999999999999999999']) assert.throws(() => costToMicros(value))
  assert.throws(() => sumPurchaseLines([{ line_total_micros: Number.MAX_SAFE_INTEGER }, { line_total_micros: 1 }]), /range/)
})

test('multi-line existing/new purchase requires exact totals, unique products/SKUs and selling prices', () => {
  assert.equal(validatePurchase(purchase), purchase)
  assert.throws(() => validatePurchase({ ...purchase, total_cost_micros: 3900001 }), /total cost/)
  assert.throws(() => validatePurchase({ ...purchase, lines: [existing, existing], total_cost_micros: 4800000 }), /duplicate/)
  assert.throws(() => validatePurchase({ ...purchase, lines: [newProduct, { ...newProduct, sku: 'new-1' }], total_cost_micros: 3000000 }), /unique/)
  assert.throws(() => validatePurchase({ ...purchase, lines: [{ ...newProduct, unit_price_cents: null }] }), /selling price/)
  assert.throws(() => validatePurchase({ ...purchase, lines: [{ ...existing, line_total_micros: 1 }] }), /multiplied/)
  assert.throws(() => validatePurchase({ ...purchase, tender: 'cash', lines: [{ ...existing, quantity: 1, purchase_unit_cost_micros: 1234567, line_total_micros: 1234567 }], total_cost_micros: 1234567 }), /silently rounded/)
})

test('save purchase draft is separate from confirmation and validates the returned review', async () => {
  const calls = []
  const client = createRetailClient(() => config, async (url, init) => { calls.push(url); assert.equal(init.headers['X-Shop-ID'], config.shopId); assert.deepEqual(JSON.parse(init.body), purchase); return Response.json(saved) })
  const result = await client.createPurchase(purchase)
  assert.equal(result.status, 'draft')
  assert.deepEqual(calls, ['https://shop.example/api/v1/shops/shop-1/purchases'])
  const mismatch = createRetailClient(() => config, async () => Response.json({ ...saved, tender: 'cash' }))
  await assert.rejects(mismatch.createPurchase(purchase), /differs/)
  assert.throws(() => parsePurchase({ ...saved, shop_id: 'another' }, config.shopId), /Unreadable/)
})

test('purchase confirmation requires matching receipt and preserves server weighted-cost insights', async () => {
  const confirmation = { purchase_id: saved.id, shop_id: config.shopId, status: 'confirmed', total_cost_micros: 3900000, confirmed_at: stamp, insights: ['Source-backed costs'], lines: [{ product_id: 'p1', quantity_received: 2, stock_before: 18, stock_after: 20, purchase_unit_cost_micros: 1200000, previous_unit_cost_micros: 1000000, new_average_unit_cost_micros: 1020000, cost_change_micros: 20000, insight: 'cost_increased' }, { product_id: 'new-id', quantity_received: 3, stock_before: 0, stock_after: 3, purchase_unit_cost_micros: 500000, previous_unit_cost_micros: null, new_average_unit_cost_micros: 500000, cost_change_micros: null, insight: 'baseline_established' }] }
  const client = createRetailClient(() => config, async (url) => { assert.match(url, /purchases\/pur-1\/confirm$/); return Response.json(confirmation) })
  assert.equal((await client.confirmPurchase(saved)).lines[0].new_average_unit_cost_micros, 1020000)
  const mismatch = createRetailClient(() => config, async () => Response.json({ ...confirmation, total_cost_micros: 1 }))
  await assert.rejects(mismatch.confirmPurchase(saved), /Unreadable/)
})

test('stock take accepts explicit zero, rejects duplicate/negative counts and requires server baseline', () => {
  assert.equal(validateStockTake(count), count)
  assert.equal(parseStockTake(countRecord, config.shopId).expected_snapshot.p1, 2)
  assert.throws(() => validateStockTake({ ...count, lines: [{ product_id: 'p1', counted_qty: -1 }] }), /non-negative/)
  assert.throws(() => validateStockTake({ ...count, lines: [...count.lines, ...count.lines] }), /once/)
  assert.throws(() => parseStockTake({ ...countRecord, expected_snapshot: {} }, config.shopId), /baseline/)
})

test('count draft does not post; confirm validates baseline/audit; conflict remains an error', async () => {
  const calls = []
  const confirmation = { stock_take_id: countRecord.id, shop_id: config.shopId, status: 'confirmed', confirmed_at: stamp, adjustments: [{ id: 'audit-1', stock_take_id: countRecord.id, shop_id: config.shopId, product_id: 'p1', expected_qty: 2, counted_qty: 0, adjustment_qty: -2, actor: count.actor, reason: count.notes, recorded_at: stamp }] }
  const client = createRetailClient(() => config, async (url) => { calls.push(url); return Response.json(url.endsWith('/confirm') ? confirmation : countRecord) })
  const draft = await client.createStockTake(count)
  assert.equal(calls.length, 1)
  assert.equal((await client.confirmStockTake(draft)).adjustments[0].adjustment_qty, -2)
  const conflict = createRetailClient(() => config, async () => new Response('', { status: 409 }))
  await assert.rejects(conflict.confirmStockTake(draft), /409/)
})

test('day-close preview is read-only and keeps sales-only limitations instead of inventing balances', async () => {
  const preview = { business_date: '2026-10-31', expected_cash_cents: 150, expected_bank_card_cents: 300, shop_timezone: 'Africa/Harare', calculation_basis: 'sales_only', warnings: ['Opening and paid movements excluded'] }
  const calls = []
  const client = createRetailClient(() => config, async (url, init) => { calls.push(url); assert.equal(init.method, 'GET'); assert.equal(init.body, undefined); return Response.json(preview) })
  assert.deepEqual(await client.previewDayClose('2026-10-31'), preview)
  assert.equal(calls.length, 1)
  assert.match(calls[0], /preview\?business_date=2026-10-31$/)
  assert.throws(() => parseClosePreview({ ...preview, calculation_basis: 'full_ledger' }, '2026-10-31'), /Unreadable/)
})

test('missing service and uncertain network outcomes never become successful/empty records', async () => {
  const missing = createRetailClient(() => config, async () => new Response('', { status: 404 }))
  await assert.rejects(missing.getPurchase('pur-1'), /unavailable/)
  const uncertain = createRetailClient(() => config, async () => { throw new TypeError('offline') })
  await assert.rejects(uncertain.createPurchase(purchase), /Outcome unconfirmed/)
})

const fullClose = { business_date: '2026-10-31', shop_timezone: 'Africa/Harare', calculation_basis: 'full_recorded_movements', warnings: [], opening_cash_cents: 1000, opening_bank_card_cents: 0, sales_cash_cents: 150, sales_bank_card_cents: 180, paid_expenses_cash_cents: 30, paid_expenses_bank_card_cents: 0, paid_purchases_cash_cents: 0, paid_purchases_bank_card_cents: 10, refunds_cash_cents: 20, refunds_bank_card_cents: 0, adjustments_cash_cents: 0, adjustments_bank_card_cents: -5, expected_cash_cents: 1100, expected_bank_card_cents: 165 }

test('full close verifies every recorded movement and signed adjustment rather than using sales alone', () => {
  assert.equal(parseClosePreview(fullClose, '2026-10-31').expected_cash_cents, 1100)
  assert.throws(() => parseClosePreview({ ...fullClose, expected_bank_card_cents: 180 }, '2026-10-31'), /reconcile/)
  assert.throws(() => parseClosePreview({ ...fullClose, opening_cash_cents: undefined }, '2026-10-31'), /components/)
})

test('day-close posting is explicit and idempotent, requires full basis and verifies counted variances/audit', async () => {
  const input = { business_date: '2026-10-31', cash_counted_cents: 1100, bank_card_counted_cents: 165, actor: 'Synthetic UI QA', notes: 'Test close only', confirmed: true }
  const receipt = { ...fullClose, ...input, id: 'close-1', audit_id: 'audit-1', shop_id: config.shopId, cash_variance_cents: 0, bank_card_variance_cents: 0, confirmed_at: stamp }
  const keys = []
  const client = createRetailClient(() => config, async (url, init) => { assert.match(url, /\/day-close$/); keys.push(init.headers['Idempotency-Key']); assert.equal(JSON.parse(init.body).confirmed, true); return Response.json(receipt) })
  assert.equal((await client.confirmDayClose(input, 'close-key')).audit_id, 'audit-1')
  await client.confirmDayClose(input, 'close-key')
  assert.deepEqual(keys, ['close-key', 'close-key'])
  await assert.rejects(client.confirmDayClose({ ...input, confirmed: false }, 'close-key'), /explicitly/)
  const wrong = createRetailClient(() => config, async () => Response.json({ ...receipt, cash_variance_cents: 50 }))
  await assert.rejects(wrong.confirmDayClose(input, 'close-key'), /unverified/)
})
