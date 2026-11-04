import assert from 'node:assert/strict'
import { test } from 'node:test'
import { migrateKnownDemoConnection, parseMuseResponse, museSourcePeriod, museJobProgressLabel, requestMuse, requestMuseJob, DEMO_SHOP_ID, resolveShopConnection, shopConfigurationError } from '../src/muse.ts'

const config = { baseUrl: 'https://shop.example/', shopId: '8b287d40-2e1a-4fe7-94d1-e58c37cb1256' }

test('known retired native demo connection upgrades only to bundled current demo and preserves other saved fields',()=>{
 const bundled={baseUrl:'http://192.168.10.213:8001',shopId:DEMO_SHOP_ID}
 let saved=JSON.stringify({baseUrl:'http://192.168.10.213:8000',shopId:DEMO_SHOP_ID,extra:'preserved'}),writes=0
 const storage={getItem:()=>saved,setItem(key,value){assert.equal(key,'street-ceo-api-config');saved=value;writes++}}
 assert.match(migrateKnownDemoConnection(storage,bundled,true),/updated/)
 assert.deepEqual(JSON.parse(saved),{baseUrl:bundled.baseUrl,shopId:DEMO_SHOP_ID,extra:'preserved'})
 assert.equal(migrateKnownDemoConnection(storage,bundled,true),null);assert.equal(writes,1)
 for(const [old,target,native] of [[{baseUrl:'http://192.168.10.213:8000',shopId:DEMO_SHOP_ID},bundled,false],[{baseUrl:'http://custom:8000',shopId:DEMO_SHOP_ID},bundled,true],[{baseUrl:'http://192.168.10.213:8000',shopId:config.shopId},bundled,true],[{baseUrl:'http://192.168.10.213:8000',shopId:DEMO_SHOP_ID},{baseUrl:'https://new-server.example',shopId:DEMO_SHOP_ID},true]])assert.equal(migrateKnownDemoConnection({getItem:()=>JSON.stringify(old),setItem:()=>assert.fail('Custom/browser config must not change')},target,native),null)
 const notice=migrateKnownDemoConnection({getItem:()=>JSON.stringify({baseUrl:'http://192.168.10.213:8000',shopId:DEMO_SHOP_ID}),setItem(){throw Error('read only')}},bundled,true)
 assert.match(notice,/could not be updated/)
})
// Synthetic contract fixtures only; these are never bundled into the app.
const fixture = {
  status: 'needs_data', title: 'Profit needs cost data', answer: 'Cost data is missing.',
  evidence_ids: ['sales-last_30_days', 'transactions-last_30_days'],
  missing_data: ['COGS', 'Operating expenses'], source: 'repository', confidence: 1,
}

test('confirmed seeded ID is non-nil and valid for Muse requests', async () => {
  assert.equal(DEMO_SHOP_ID, '00000000-0000-0000-0000-000000000001')
  const defaults = resolveShopConnection(null, { baseUrl: config.baseUrl })
  assert.equal(defaults.shopId, DEMO_SHOP_ID)
  assert.equal(shopConfigurationError(defaults), null)
  await requestMuse(defaults, 'Question', undefined, async (url, init) => {
    assert.equal(url, `https://shop.example/api/v1/shops/${DEMO_SHOP_ID}/muse`)
    assert.equal(init.headers['X-Shop-ID'], DEMO_SHOP_ID)
    return Response.json(fixture)
  })
})

test('saved valid shop overrides win over environment/default without silently changing tenants', () => {
  const saved = { baseUrl: 'https://another-shop.example', shopId: config.shopId }
  assert.deepEqual(resolveShopConnection(saved, { baseUrl: config.baseUrl, shopId: DEMO_SHOP_ID }), saved)
  assert.equal(resolveShopConnection(null, { shopId: config.shopId }).shopId, config.shopId)
  assert.equal(resolveShopConnection({ shopId: '' }, { shopId: DEMO_SHOP_ID }).shopId, '')
  assert.equal(resolveShopConnection({ shopId: '00000000-0000-0000-0000-000000000000' }).shopId, '00000000-0000-0000-0000-000000000000')
  assert.equal(resolveShopConnection({ shopId: 42 }).shopId, DEMO_SHOP_ID)
})

test('missing, nil, malformed shop IDs and invalid backend addresses never issue a Muse request', async () => {
  const unused = () => assert.fail('Invalid shop configuration must not issue a request')
  for (const shopId of ['', ' ', '00000000-0000-0000-0000-000000000000', 'shop-1', '../other-shop']) {
    await assert.rejects(requestMuse({ ...config, shopId }, 'Question', undefined, unused), /Shop ID/)
  }
  for (const baseUrl of ['', '/api/v1', 'ftp://shop.example', 'https://user:secret@shop.example']) {
    await assert.rejects(requestMuse({ ...config, baseUrl }, 'Question', undefined, unused), /Shop Connection/)
  }
})

test('sends the verified shop-scoped request and preserves missing-data response', async () => {
  const response = await requestMuse(config, '  What was my profit?  ', undefined, async (url, init) => {
    assert.equal(url, 'https://shop.example/api/v1/shops/8b287d40-2e1a-4fe7-94d1-e58c37cb1256/muse')
    assert.equal(init.method, 'POST')
    assert.equal(init.headers['X-Shop-ID'], config.shopId)
    assert.deepEqual(JSON.parse(init.body), { question: 'What was my profit?' })
    assert.ok(init.signal)
    return Response.json(fixture)
  })
  assert.deepEqual(response, fixture)
})

test('accepts answered and unavailable states without generating fallback figures', () => {
  for (const status of ['answered', 'needs_data', 'unavailable']) {
    assert.equal(parseMuseResponse({ ...fixture, status }).status, status)
  }
})

test('rejects malformed and unrecognized responses', () => {
  for (const patch of [{ status: 'captured' }, { answer: '' }, { evidence_ids: [4] }, { missing_data: null }, { confidence: 2 }, { confidence: NaN }, { source: null }]) {
    assert.throws(() => parseMuseResponse({ ...fixture, ...patch }), /unreadable/)
  }
  assert.throws(() => parseMuseResponse(null), /unreadable/)
})

test('reports missing configuration and invalid questions before any network call', async () => {
  const unused = () => assert.fail('No network request expected')
  await assert.rejects(requestMuse({ ...config, baseUrl: '' }, 'Question', undefined, unused), /Shop Connection/)
  await assert.rejects(requestMuse(config, '   ', undefined, unused), /1–1,000/)
  await assert.rejects(requestMuse(config, 'x'.repeat(1001), undefined, unused), /1–1,000/)
})

test('shows actionable HTTP failures without displaying raw server output', async () => {
  for (const [status, expected] of [[404, /unavailable/], [403, /Shop ID/], [422, /accept this question/], [503, /try again/]]) {
    await assert.rejects(requestMuse(config, 'Question', undefined, async () => new Response('private server output', { status })), expected)
  }
})

test('handles network failure and non-JSON responses', async () => {
  await assert.rejects(requestMuse(config, 'Question', undefined, async () => { throw new TypeError('fetch failed') }), /Check your connection/)
  await assert.rejects(requestMuse(config, 'Question', undefined, async () => new Response('<html>')), /unreadable/)
})

test('forwards cancellation so old questions cannot replace a newer answer', async () => {
  const controller = new AbortController()
  controller.abort()
  await assert.rejects(requestMuse(config, 'Question', controller.signal, async (_, init) => {
    init.signal.throwIfAborted()
    assert.fail('Aborted request should not proceed')
  }), { name: 'AbortError' })
})

test('period labels come only from server evidence and explicitly handle absent coverage', () => {
  assert.equal(museSourcePeriod(fixture.evidence_ids), 'Last 30 days (UTC)')
  assert.equal(museSourcePeriod(['sales-today']), 'Today (UTC)')
  assert.equal(museSourcePeriod(['sales-this_month']), 'This month (service label)')
  assert.equal(museSourcePeriod(['sales-available']), 'All available records')
  assert.equal(museSourcePeriod([]), 'Not supplied by the service')
  assert.equal(museSourcePeriod(['unknown-id']), 'Not supplied by the service')
})

const jobId = '348d53e2-69f6-4dbd-bfe1-05f9f61d80d9'
const pending = {
  requestId: '2a4ff377-9a98-4419-a965-5772a09ba28d',
  chatId: 'test-chat', startedAt: 1700000000000,
  message: 'Current question', question: 'Exact original context and question',
}

test('lost Muse job submission retries with identical key and question, then polls the returned job', async () => {
  const signal = new AbortController().signal
  const submits = []
  const submit = async (url, init) => {
    submits.push({ url, headers: init.headers, body: init.body })
    assert.equal(init.method, 'POST')
    if (submits.length === 1) throw new TypeError('sensitive networking details')
    return Response.json({ job_id: jobId, status: 'queued', result: null, error: null }, { status: 202 })
  }
  await assert.rejects(requestMuseJob(config, pending, signal, submit), error => error.retryable && !error.message.includes('sensitive'))
  assert.equal((await requestMuseJob(config, pending, signal, submit)).job_id, jobId)
  assert.deepEqual(submits[0], submits[1])
  assert.equal(submits[0].headers['Idempotency-Key'], pending.requestId)
  assert.equal(submits[0].headers['X-Shop-ID'], config.shopId)
  assert.equal(submits[0].body, JSON.stringify({ question: pending.question }))
  const result = await requestMuseJob(config, { ...pending, jobId }, signal, async (url, init) => {
    assert.equal(url, `https://shop.example/api/v1/shops/${config.shopId}/muse/jobs/${jobId}`)
    assert.equal(init.method, 'GET')
    assert.equal(init.body, undefined)
    assert.equal(init.cache, 'no-store')
    return Response.json({ job_id: jobId, status: 'succeeded', result: fixture, error: null })
  })
  assert.deepEqual(result.result, fixture)
})

test('Muse job polling does not trust mismatched IDs, malformed successes or server error bodies', async () => {
  const signal = new AbortController().signal
  for (const body of [
    { job_id: pending.requestId, status: 'succeeded', result: fixture },
    { job_id: jobId, status: 'succeeded', result: {} },
  ]) {
    await assert.rejects(requestMuseJob(config, { ...pending, jobId }, signal, async () => Response.json(body)), error => error.retryable)
  }
  await assert.rejects(requestMuseJob(config, pending, signal, async () => Response.json({ detail: 'sensitive raw payload' }, { status: 409 })), error => !error.retryable && !error.message.includes('sensitive'))
  await assert.rejects(requestMuseJob(config, pending, signal, async () => Response.json({}, { status: 503 })), error => error.retryable)
  const failed = await requestMuseJob(config, { ...pending, jobId }, signal, async () => Response.json({ job_id: jobId, status: 'failed', error: 'sensitive provider text' }))
  assert.deepEqual(failed, { job_id: jobId, status: 'failed', result: null })
})

test('accepts a bounded structured business plan while preserving older Muse answers', () => {
  const document = { title: 'Financing plan', sections: [
    { title: 'Recorded performance', body: 'Sales from saved records.', evidence_ids: ['sales-2026-10'] },
    { title: 'Projections and limitations', body: 'This is an illustrative scenario.' },
  ] }
  assert.deepEqual(parseMuseResponse({ ...fixture, document }).document, document)
  assert.equal(parseMuseResponse(fixture).document, undefined)
  for (const malformed of [
    { ...document, sections: [] },
    { ...document, sections: [{ title: ' ', body: 'Text' }] },
    { ...document, sections: [{ title: 'Evidence', body: 'Text', evidence_ids: [1] }] },
    { ...document, sections: [{ title: 'Long text', body: 'a'.repeat(12001) }] },
  ]) {
    assert.throws(() => parseMuseResponse({ ...fixture, document: malformed }), /unreadable business plan/)
  }
})

test('Muse PDF escapes model content in HTML and bounds native PDF rows', async () => {
  const { buildMusePdf } = await import('../src/musePdf.ts')
  const body = '<script>unsafe</script> & <img src=x>\n\n' + 'a'.repeat(4200)
  const pdf = buildMusePdf({ title: 'Financing <draft>', sections: [
    { title: 'Actual & projected', body, evidence_ids: ['sales-2026-10'] },
  ] })
  assert.equal(pdf.title, 'Business plan')
  assert.equal(pdf.columns, undefined)
  assert.match(pdf.html, /Financing &lt;draft&gt;/)
  assert.match(pdf.html, /Actual &amp; projected/)
  assert.match(pdf.html, /Evidence: sales-2026-10/)
  assert.doesNotMatch(pdf.html, /<script>|<img src=x>/)
  assert.ok(pdf.rows.every(row => row.text.length <= 2000))
  assert.equal(pdf.rows.filter(row => /^a+$/.test(row.text)).map(row => row.text).join(''), 'a'.repeat(4200))
})

test('PDF delivery preserves structured report columns and sends Muse plans as native rows', async () => {
  const { deliverPdf } = await import('../src/reportShare.ts')
  const seen = []
  const previous = globalThis.window
  globalThis.window = { Capacitor: {
    getPlatform: () => 'android',
    registerPlugin: () => ({ downloadPdf: async input => {
      seen.push(input)
      return { opened: true, savedToDownloads: true }
    } }),
  } }
  try {
    const base = { filename: 'street-ceo-test', title: 'Business plan', subtitle: 'Test', html: '', rows: [{ kind: 'heading', text: 'Section' }] }
    assert.match(await deliverPdf(base, 'Business plan'), /Business plan saved to Downloads and opened/)
    assert.deepEqual(seen[0], { filename: base.filename, title: base.title, subtitle: base.subtitle, rows: base.rows })
    const structured = { ...base, title: 'Sales report', columns: ['Product', 'Quantity', 'Sales'], products: [['Sample', '2', 'USD 3']], summary: [['Sales', 'USD 3']], notes: [] }
    assert.match(await deliverPdf(structured), /Report saved to Downloads and opened/)
    assert.deepEqual(seen[1].columns, structured.columns)
    assert.deepEqual(seen[1].summary, structured.summary)
    assert.deepEqual(seen[1].products, structured.products)
  } finally {
    if (previous === undefined) delete globalThis.window
    else globalThis.window = previous
  }
})

test('Muse polling displays a known progress stage and discards arbitrary progress text', async () => {
  const signal = new AbortController().signal
  const mockJob = progress => async () => Response.json({ job_id: jobId, status: 'running', result: null, progress })
  const retrieving = await requestMuseJob(config, { ...pending, jobId }, signal, mockJob({ stage: 'retrieving', label: 'private details' }))
  assert.equal(retrieving.progress, 'retrieving')
  assert.match(museJobProgressLabel(retrieving), /reading the records/)
  const unknown = await requestMuseJob(config, { ...pending, jobId }, signal, mockJob({ stage: 'private details' }))
  assert.equal(unknown.progress, undefined)
  assert.doesNotMatch(museJobProgressLabel(unknown), /private details/)
})

test('follow-up submissions preserve the captured previous job reference on exact retries', async () => {
  const signal = new AbortController().signal
  const priorJobId = 'a69dc095-be78-4924-b6b3-b992db00bfdc'
  const followup = { ...pending, priorJobId }
  const bodies = []
  const fetcher = async (url, init) => {
    assert.equal(init.headers['Idempotency-Key'], pending.requestId)
    bodies.push(init.body)
    if (bodies.length === 1) throw new TypeError('connection dropped')
    return Response.json({ job_id: jobId, status: 'queued', result: null })
  }
  await assert.rejects(requestMuseJob(config, followup, signal, fetcher))
  await requestMuseJob(config, JSON.parse(JSON.stringify(followup)), signal, fetcher)
  assert.equal(bodies[0], bodies[1])
  assert.deepEqual(JSON.parse(bodies[0]), { question: pending.question, prior_job_id: priorJobId })
})

test('Muse PDF keeps the final section and evidence at the supported document limits', async () => {
  const { buildMusePdf } = await import('../src/musePdf.ts')
  const sections = Array.from({ length: 20 }, (_, section) => ({
    title: 'Section ' + section,
    body: section === 0 ? Array.from({ length: 3000 }, () => 'x').join('\n\n') + '\n\nEND'
      : 'a'.repeat(1799) + '📈' + 'b'.repeat(10185) + 'END',
    evidence_ids: Array.from({ length: 24 }, (_, index) => 'evidence-' + String(index).padStart(55, '0')),
  }))
  const response = parseMuseResponse({ ...fixture, document: { title: 'Test financing plan', sections } })
  const { rows, filename } = buildMusePdf(response.document)
  assert.equal(filename, 'street-ceo-business-plan')
  assert.equal(rows.filter(row => row.kind === 'heading').length, 20)
  assert.ok(rows.length <= 3000)
  assert.ok(rows.every(row => row.text.length <= 2000))
  assert.ok(rows.reduce((sum, row) => sum + row.text.length, 0) <= 500000)
  assert.equal(rows.filter(row => row.kind === 'text' && row.text.endsWith('END')).length, 20)
  assert.equal(rows.slice(1, rows.findIndex(row => row.text.startsWith('Evidence:'))).map(row => row.text).join(' '), sections[0].body.replace(/\n\n/g, ' '))
  assert.equal(rows.filter(row => row.text.includes('📈')).length, 19)
  assert.equal(rows.filter(row => row.text.startsWith('Evidence:')).length, 20)
})
