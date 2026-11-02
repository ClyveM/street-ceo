import assert from 'node:assert/strict'
import { test } from 'node:test'
import { migrateKnownDemoConnection, parseMuseResponse, museSourcePeriod, requestMuse, DEMO_SHOP_ID, resolveShopConnection, shopConfigurationError } from '../src/muse.ts'

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
