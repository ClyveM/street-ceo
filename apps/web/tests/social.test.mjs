import assert from 'node:assert/strict'
import { test } from 'node:test'
import { parseSocialBrief, parseSocialImageResult, requestSocialBrief, requestSocialImage, requestSocialDraft, parseSocialDraft, previewImageRef } from '../src/social.ts'

const config = { baseUrl: 'https://shop.example', shopId: 'shop-1' }
const briefFixture = { shop_id: config.shopId, catalogue_source: 'repository', created_at: '2026-10-31T00:00:00Z', products: [{ product_id: 'p1', sku: 'TEST', name: 'Synthetic test product', unit_price_cents: 120, stock_qty: 3 }], shop_image: null }
const imageRequest = { product_ids: ['p1'], brief: 'Use supplied catalogue facts', aspect_ratio: '1:1' }
const imageFixture = { id: 'request-1', shop_id: config.shopId, ...imageRequest, source_image_id: null, status: 'provider_not_configured', provider: 'none', model: null, image_refs: [], warnings: ['Image provider is not configured'], draft_only: true, output_url: null, created_at: '2026-10-31T00:00:00Z' }

test('verified image draft accepts returned refs, while preview rejects unsafe and unresolved refs', () => {
  const output = 'https://images.example/test.png'
  const result = parseSocialImageResult({ ...imageFixture, status: 'draft', provider: 'test-provider', model: 'test-model', image_refs: [output], output_url: output, warnings: [] }, config.shopId, imageRequest)
  assert.equal(previewImageRef(result.output_url), output)
  for (const value of ['javascript:alert(1)', 'file_test', 'data:image/svg+xml;base64,AAAA', 'https://user:password@example.com/a.png']) assert.equal(previewImageRef(value), null)
  assert.equal(previewImageRef('data:image/png;base64,AAAA'), 'data:image/png;base64,AAAA')
  assert.throws(() => parseSocialImageResult({ ...result, draft_only: false }, config.shopId, imageRequest), /Unreadable/)
})

test('verified text-draft endpoint preserves provider evidence and never publishes', async () => {
  const fixture = { id: 'draft-1', shop_id: config.shopId, title: 'Test draft', caption: 'Synthetic test caption', voiceover_script: 'Synthetic voiceover', shot_list: ['Show the selected product'], selected_product_ids: ['p1'], claims: [{ product_id: 'p1', claim: 'Synthetic test product', source_field: 'name' }], status: 'draft', source: 'provider', provider: 'test-provider', model: 'test-model', warnings: [], draft_only: true, created_at: '2026-10-31T00:00:00Z' }
  const result = await requestSocialDraft(config, { product_ids: ['p1'], brief: 'Draft only' }, undefined, async (url, init) => {
    assert.equal(url, 'https://shop.example/api/v1/shops/shop-1/social/draft')
    assert.deepEqual(JSON.parse(init.body), { product_ids: ['p1'], brief: 'Draft only', duration_seconds: 40 })
    return Response.json(fixture)
  })
  assert.equal(result.status, 'draft')
  assert.throws(() => parseSocialDraft({ ...fixture, selected_product_ids: ['unselected'] }, config.shopId, ['p1']), /Unreadable/)
  assert.throws(() => parseSocialDraft({ ...fixture, draft_only: false }, config.shopId, ['p1']), /Unreadable/)
  assert.equal(parseSocialDraft({ ...fixture, status: 'unavailable', source: 'fallback', selected_product_ids: [], claims: [] }, config.shopId, ['p1']).status, 'unavailable')
})

test('catalogue verification sends only selected IDs and declared image metadata to the verified brief route', async () => {
  const payload = { product_ids: ['p1'], shop_image: { filename: 'shop.png', content_type: 'image/png', size_bytes: 12 } }
  const result = await requestSocialBrief(config, payload, undefined, async (url, init) => {
    assert.equal(url, 'https://shop.example/api/v1/shops/shop-1/social/brief')
    assert.equal(init.headers['X-Shop-ID'], config.shopId)
    assert.deepEqual(JSON.parse(init.body), payload)
    return Response.json(briefFixture)
  })
  assert.equal(result.catalogue_source, 'repository')
})

test('rejects guessed or mismatched catalogue data', () => {
  assert.throws(() => parseSocialBrief({ ...briefFixture, shop_id: 'another-shop' }, config.shopId, ['p1']), /Unreadable/)
  assert.throws(() => parseSocialBrief(briefFixture, config.shopId, ['p2']), /Unreadable/)
  assert.throws(() => parseSocialBrief({ ...briefFixture, products: [{ ...briefFixture.products[0], stock_qty: -1 }] }, config.shopId, ['p1']), /Unreadable/)
})

test('image generation request preserves unavailable provider state and null output', async () => {
  const result = await requestSocialImage(config, imageRequest, undefined, async (url, init) => {
    assert.equal(url, 'https://shop.example/api/v1/shops/shop-1/social/image-generation')
    assert.deepEqual(JSON.parse(init.body), imageRequest)
    return Response.json(imageFixture)
  })
  assert.equal(result.status, 'provider_not_configured')
  assert.equal(result.output_url, null)
})

test('does not manufacture or accept an unverified generated-image success/URL', () => {
  assert.throws(() => parseSocialImageResult({ ...imageFixture, status: 'generated', output_url: 'https://image.example/fake.png' }, config.shopId, imageRequest), /Unreadable/)
  assert.throws(() => parseSocialImageResult({ ...imageFixture, source_image_id: 'other' }, config.shopId, imageRequest), /Unreadable/)
})

test('bounds product selection and image brief before any request', async () => {
  const unused = () => assert.fail('No request expected')
  await assert.rejects(requestSocialBrief(config, { product_ids: [] }, undefined, unused), /1–12/)
  await assert.rejects(requestSocialBrief(config, { product_ids: ['p1', 'p1'] }, undefined, unused), /1–12/)
  await assert.rejects(requestSocialImage(config, { ...imageRequest, brief: '  ' }, undefined, unused), /1–1,000/)
  await assert.rejects(requestSocialImage(config, { ...imageRequest, aspect_ratio: '3:7' }, undefined, unused), /aspect ratio/)
})

test('surface service errors and stale route failures without provider claims', async () => {
  await assert.rejects(requestSocialBrief(config, { product_ids: ['p1'] }, undefined, async () => new Response('', { status: 404 })), /backend version/)
  await assert.rejects(requestSocialImage(config, imageRequest, undefined, async () => { throw new TypeError('offline') }), /connection/)
})
