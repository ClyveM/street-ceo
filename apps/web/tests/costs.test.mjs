import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'
import { canConfirmInvoice, createCostsClient, expenseCategories, moneyToCents, parseExpense, parseInvoice, validateExpense, validateInvoiceFile, validateInvoiceReview, validDate } from '../src/costs.ts'

const config = { baseUrl: 'https://shop.example', shopId: 'shop-test' }
const invoice = { id: 'invoice-1', shop_id: config.shopId, filename: 'supplier.pdf', content_type: 'application/pdf', size_bytes: 20, sha256: 'a'.repeat(64), storage_backend: 'memory', storage_ref: 'memory://invoices/invoice-1', extraction_status: 'provider_unavailable', extraction_source: 'none', lines: [], warnings: ['No OCR provider configured'], uploaded_at: '2026-10-31T00:00:00Z', confirmed_at: null }
const line = { id: 'line-1', description: 'Test item', sku: 'TEST', quantity: 2, line_total_cents: 400, calculated_unit_cost_micros: 2000000, suggested_product_id: 'p1', matched_product_id: 'p1', match_status: 'accepted', source: 'manual_review', evidence_ref: 'invoice:invoice-1' }
const expense = { category: 'rent', frequency: 'recurring', occurred_on: '2026-10-31', period_start: '2026-10-01', period_end: '2026-10-31', amount_cents: 10000, notes: 'October shop rent', tender: 'unpaid' }
const expenseRecord = { ...expense, id: 'expense-1', shop_id: config.shopId, status: 'draft', created_at: '2026-10-31T00:00:00Z', confirmed_at: null }

test('money inputs convert exactly to integer cents and reject rounding/unsafe values', () => {
  assert.equal(moneyToCents('0.29'), 29)
  assert.equal(moneyToCents('12.3'), 1230)
  assert.equal(moneyToCents('0', true), 0)
  for (const value of ['0', '-1', '1.001', 'NaN', '1e3', '90071992547410']) assert.throws(() => moneyToCents(value))
})

test('expense categories and one-off/recurring periods match verified contracts', () => {
  assert.deepEqual(expenseCategories, ['electricity','transport','rent','wages','airtime','supplies','other'])
  assert.deepEqual(validateExpense(expense), expense)
  assert.equal(validDate('2026-02-30'), false)
  assert.throws(() => validateExpense({ ...expense, period_end: '2026-09-30' }), /period/)
  assert.throws(() => validateExpense({ ...expense, frequency: 'one_off' }), /One-off/)
  assert.throws(() => validateExpense({ ...expense, period_start: null, period_end: null }), /period/)
  assert.throws(() => validateExpense({ ...expense, occurred_on: '' }), /date/)
  for (const category of expenseCategories) {
    for (const tender of ['cash', 'bank', 'unpaid']) {
      assert.deepEqual(validateExpense({ ...expense, category, tender }), { ...expense, category, tender })
      assert.equal(validateExpense({ ...expense, category, tender, frequency: 'one_off', period_start: null, period_end: null }).period_start, null)
    }
  }
})

test('invoice upload accepts bounded real PDF/images without fabricating extracted lines', async () => {
  const pdf = new File(['%PDF-1.7\nTest fixture'], 'supplier invoice.pdf', { type: 'application/pdf' })
  await validateInvoiceFile(pdf)
  await validateInvoiceFile(new File([await readFile(new URL('./fixtures/product.png', import.meta.url))], 'product.png', { type: 'image/png' }))
  await assert.rejects(validateInvoiceFile(new File(['no'], 'wrong.pdf', { type: 'application/pdf' })), /contents/)
  await assert.rejects(validateInvoiceFile(new File(['x'], 'file.txt', { type: 'text/plain' })), /PDF/)
  const calls = []
  const api = createCostsClient(() => config, async (url, init) => {
    calls.push(url)
    assert.equal(init.body.get('invoice').name, 'supplier_invoice.pdf')
    assert.equal(init.headers['Content-Type'], undefined)
    assert.equal(init.headers['X-Shop-ID'], config.shopId)
    return Response.json(invoice, { status: 201 })
  })
  const result = await api.uploadInvoice(pdf)
  assert.equal(result.extraction_status, 'provider_unavailable')
  assert.deepEqual(result.lines, [])
  assert.deepEqual(calls, ['https://shop.example/api/v1/shops/shop-test/invoices'])
})

test('review saves manual lines and product matches separately from confirming stock/cost changes', async () => {
  const calls = []
  const payload = { source: 'manual_review', evidence_ref: 'invoice:invoice-1', lines: [{ description: 'Test item', sku: 'TEST', product_id: 'p1', quantity: 2, line_total_cents: 400 }] }
  const reviewed = { ...invoice, extraction_status: 'needs_review', extraction_source: 'manual_review', lines: [line] }
  const api = createCostsClient(() => config, async (url, init) => {
    calls.push(url)
    if (url.endsWith('/review')) { assert.deepEqual(JSON.parse(init.body), payload); return Response.json(reviewed) }
    return Response.json({ invoice_id: invoice.id, shop_id: config.shopId, status: 'confirmed', applied_line_ids: [line.id], stock_units_added: 2, cost_updates: 1, warnings: [], confirmed_at: '2026-10-31T01:00:00Z' })
  })
  const result = await api.reviewInvoice(invoice.id, payload)
  assert.equal(calls.length, 1)
  assert.equal(canConfirmInvoice(result, false), true)
  const receipt = await api.confirmInvoice(invoice.id)
  assert.equal(receipt.stock_units_added, 2)
  assert.equal(calls.length, 2)
  assert.match(calls[1], /\/invoices\/invoice-1\/confirm$/)
})

test('unmatched/suggested/dirty/unreviewed invoices cannot enable confirmation', () => {
  assert.equal(canConfirmInvoice(invoice, false), false)
  const reviewed = { ...invoice, extraction_status: 'needs_review', lines: [line] }
  assert.equal(canConfirmInvoice(reviewed, true), false)
  assert.equal(canConfirmInvoice({ ...reviewed, lines: [{ ...line, match_status: 'suggested', matched_product_id: null }] }, false), false)
  assert.equal(canConfirmInvoice({ ...reviewed, lines: [{ ...line, calculated_unit_cost_micros: null }] }, false), false)
  assert.throws(() => validateInvoiceReview({ source: 'ocr_provider', evidence_ref: 'x', lines: [] }), /manual invoice lines/)
})

test('expense draft creation never automatically confirms or schedules a recurring charge', async () => {
  const calls = []
  const api = createCostsClient(() => config, async (url, init) => {
    calls.push(url)
    if (url.endsWith('/confirm')) return Response.json({ ...expenseRecord, status: 'confirmed', confirmed_at: '2026-10-31T01:00:00Z' })
    assert.deepEqual(JSON.parse(init.body), expense)
    return Response.json(expenseRecord, { status: 201 })
  })
  const draft = await api.createExpense(expense)
  assert.equal(draft.status, 'draft')
  assert.equal(calls.length, 1)
  const confirmed = await api.confirmExpense(draft.id)
  assert.equal(confirmed.status, 'confirmed')
  assert.match(calls[1], /\/expenses\/expense-1\/confirm$/)
})

test('rejects cross-shop receipts and old metadata-only invoice response', () => {
  assert.throws(() => parseInvoice({ ...invoice, shop_id: 'other' }, config.shopId), /incomplete/)
  assert.throws(() => parseInvoice({ id: 'legacy-invoice', filename: 'old.pdf' }, config.shopId), /incomplete/)
  assert.throws(() => parseExpense({ ...expenseRecord, shop_id: 'other' }, config.shopId), /Unreadable/)
})

test('rejects expense receipts with a different period before allowing confirmation', async () => {
  const api = createCostsClient(() => config, async () => Response.json({ ...expenseRecord, period_end: '2026-10-30' }))
  await assert.rejects(api.createExpense(expense), /does not match the draft/)
})

test('history failures remain errors, not empty records; rejected inputs do not hit the network', async () => {
  const failed = createCostsClient(() => config, async () => new Response('', { status: 404 }))
  await assert.rejects(failed.listInvoices(), /backend version/)
  await assert.rejects(failed.listExpenses(), /backend version/)
  const oldVersion = createCostsClient(() => config, async () => new Response('', { status: 405 }))
  await assert.rejects(oldVersion.listInvoices(), /running version/)
  const unused = createCostsClient(() => config, async () => assert.fail('No request expected'))
  await assert.rejects(unused.createExpense({ ...expense, amount_cents: 0 }), /positive/)
})
