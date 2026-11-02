import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFile } from 'node:fs/promises'
import { validateProductImage, imageUploadFilename, parseProductImage, uploadProductImage, MAX_PRODUCT_IMAGE_BYTES } from '../src/productImages.ts'

const png = await readFile(new URL('./fixtures/product.png', import.meta.url))
const file = new File([png], 'My shop photo.png', { type: 'image/png' })
const config = { baseUrl: 'https://shop.example', shopId: '8b287d40-2e1a-4fe7-94d1-e58c37cb1256' }
const productId = '7f047ccf-5498-4463-b168-247c529083fa'
const metadata = { id: 'image-1', shop_id: config.shopId, product_id: productId, filename: 'My_shop_photo.png', content_type: 'image/png', size_bytes: file.size, sha256: 'a'.repeat(64), storage_backend: 'memory', storage_ref: 'memory://product-images/image-1', uploaded_at: '2026-10-31T00:00:00Z' }

test('validates supported type, size, and matching file signature', async () => {
  await validateProductImage(file)
  await assert.rejects(validateProductImage(new Blob(['x'], { type: 'image/svg+xml' })), /JPEG, PNG, or WebP/)
  await assert.rejects(validateProductImage(new Blob([], { type: 'image/png' })), /empty/)
  await assert.rejects(validateProductImage(new Blob(['wrong contents'], { type: 'image/png' })), /do not match/)
  await assert.rejects(validateProductImage(new Blob([new Uint8Array(MAX_PRODUCT_IMAGE_BYTES + 1)], { type: 'image/png' })), /10 MiB/)
})

test('normalizes upload filenames to the verified safe-basename contract', () => {
  assert.equal(imageUploadFilename(file.name, file.type), 'My_shop_photo.png')
  assert.match(imageUploadFilename('../a risky name$.jpg', 'image/jpeg'), /^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/)
  assert.equal(imageUploadFilename('你好', 'image/webp'), 'product-image.webp')
})

test('uploads multipart image to the verified shop/product route, with no invented download URL', async () => {
  const result = await uploadProductImage(config, productId, file, async (url, init) => {
    assert.equal(url, `https://shop.example/api/v1/shops/${config.shopId}/products/${productId}/image`)
    assert.equal(init.headers['X-Shop-ID'], config.shopId)
    assert.equal(init.headers['Content-Type'], undefined)
    assert.equal(init.body.get('image').name, 'My_shop_photo.png')
    return Response.json(metadata, { status: 201 })
  })
  assert.equal(result.storage_backend, 'memory')
  assert.equal(result.output_url, undefined)
})

test('rejects cross-shop/product receipts and makes upload failures actionable', async () => {
  assert.throws(() => parseProductImage({ ...metadata, shop_id: 'other' }, config.shopId, productId), /Unreadable/)
  assert.throws(() => parseProductImage({ ...metadata, product_id: 'other' }, config.shopId, productId), /Unreadable/)
  await assert.rejects(uploadProductImage(config, productId, file, async () => new Response('', { status: 404 })), /preview is still local/)
  await assert.rejects(uploadProductImage(config, productId, file, async () => { throw new TypeError('offline') }), /check the connection/)
})
