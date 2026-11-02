import assert from 'node:assert/strict'
import { test } from 'node:test'
import { costInput, createProductCostsClient, parseCostCorrection } from '../src/productCosts.ts'
import { invoiceReviewNotice } from '../src/costs.ts'

const config = { baseUrl: 'https://shop.example', shopId: 'shop-1' }
const payload = costInput('0.420001', '2026-10-31', 'Correct supplier cost', 'Invoice QA-1', 'Shop operator')
const draft = { ...payload, id: 'correction-1', shop_id: config.shopId, product_id: 'product-1', status: 'draft', created_at: '2026-10-31T19:00:00Z', confirmed_at: null }
const confirmed = { ...draft, status: 'confirmed', confirmed_at: '2026-10-31T19:01:00Z' }

test('cost corrections preserve exact six-decimal costs including explicit zero', () => {
  assert.equal(payload.unit_cost_micros, 420001)
  assert.equal(costInput('0', '2026-10-31', ' reason ', ' source ', ' actor ').unit_cost_micros, 0)
  for (const amount of ['1.0000001', '-1', '1e6', '', '9007199255']) assert.throws(() => costInput(amount, '2026-10-31', 'reason', 'source', 'actor'))
  assert.throws(() => costInput('1', '2026-02-30', 'reason', 'source', 'actor'), /date/)
  assert.throws(() => costInput('1', '2026-10-31', ' ', 'source', 'actor'), /reason/)
})

test('draft and explicit confirmation use verified product-scoped routes without stock input', async () => {
  const calls = []
  const client = createProductCostsClient(() => config, async (url, init) => {
    calls.push(url)
    assert.equal(init.headers['X-Shop-ID'], config.shopId)
    if (url.endsWith('/confirm')) { assert.equal(init.body, undefined); return Response.json(confirmed) }
    assert.deepEqual(JSON.parse(init.body), payload)
    assert.equal('stock_qty' in JSON.parse(init.body), false)
    return Response.json(draft, { status: 201 })
  })
  const saved = await client.draft('product-1', payload)
  assert.equal(calls.length, 1)
  assert.equal(saved.status, 'draft')
  assert.equal((await client.confirm(saved)).status, 'confirmed')
  assert.deepEqual(calls, ['https://shop.example/api/v1/shops/shop-1/products/product-1/cost-corrections', 'https://shop.example/api/v1/shops/shop-1/products/product-1/cost-corrections/correction-1/confirm'])
})

test('cross-shop/product, altered amount and mismatched confirmation receipts are rejected', async () => {
  assert.throws(() => parseCostCorrection({ ...draft, shop_id: 'other' }, config, 'product-1'), /Unreadable/)
  assert.throws(() => parseCostCorrection(draft, config, 'other'), /Unreadable/)
  const changed = createProductCostsClient(() => config, async () => Response.json({ ...draft, unit_cost_micros: 1 }))
  await assert.rejects(changed.draft('product-1', payload), /differs/)
  const mismatch = createProductCostsClient(() => config, async () => Response.json({ ...confirmed, id: 'other' }))
  await assert.rejects(mismatch.confirm(draft), /differs/)
  assert.throws(() => parseCostCorrection({ ...confirmed, confirmed_at: null }, config, 'product-1'), /Unreadable/)
})

test('network and conflict errors do not retry cost posting', async () => {
  let calls = 0
  const client = createProductCostsClient(() => config, async () => { calls++; throw new TypeError('network') })
  await assert.rejects(client.confirm(draft), /outcome is unknown/)
  assert.equal(calls, 1)
  const conflict = createProductCostsClient(() => config, async () => new Response('', { status: 409 }))
  await assert.rejects(conflict.confirm(draft), /history/)
  const unused = createProductCostsClient(() => config, async () => assert.fail('Invalid cost must not post'))
  await assert.rejects(unused.draft('product-1', { ...payload, unit_cost_micros: NaN }), /safe integer/)
})

test('cost audit recovery uses verified GET and preserves server stock evidence', async () => {
  const audit = { id: 'audit-1', shop_id: config.shopId, product_id: 'product-1', source_type: 'direct_correction', new_unit_cost_micros: payload.unit_cost_micros, stock_before: 18, stock_after: 18, source_ref: payload.source_ref, reason: payload.reason, actor: payload.actor, recorded_at: confirmed.confirmed_at }
  const client = createProductCostsClient(() => config, async (url, init) => { assert.match(url, /\/products\/product-1\/cost-history$/); assert.equal(init.method, undefined); return Response.json([audit]) })
  assert.deepEqual(await client.history('product-1'), [audit])
  const wrong = createProductCostsClient(() => config, async () => Response.json([{ ...audit, product_id: 'other' }]))
  await assert.rejects(wrong.history('product-1'), /Unreadable/)
})

test('invoice extraction presentation distinguishes pending, absent, manual and real provider evidence', () => {
  const invoice = { extraction_status: 'provider_unavailable', extraction_source: 'none', lines: [] }
  assert.match(invoiceReviewNotice(invoice), /no OCR is claimed/)
  assert.match(invoiceReviewNotice({ ...invoice, extraction_status: 'pending' }), /pending/)
  assert.match(invoiceReviewNotice({ ...invoice, extraction_source: 'ocr_provider', lines: [{ id: 'actual-line' }] }), /suggestions are not accepted/)
  assert.match(invoiceReviewNotice({ ...invoice, extraction_source: 'manual_review', lines: [{ id: 'manual-line' }] }), /manual lines/)
})
