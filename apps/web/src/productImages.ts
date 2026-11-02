export const MAX_PRODUCT_IMAGE_BYTES = 10 * 1024 * 1024
export const PRODUCT_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'] as const
export type ProductImageMetadata = {
  id: string; shop_id: string; product_id: string; filename: string; content_type: string;
  size_bytes: number; sha256: string; storage_backend: 'memory'; storage_ref: string; uploaded_at: string;
}

export async function validateProductImage(file: Blob & { name?: string }): Promise<void> {
  if (!(PRODUCT_IMAGE_TYPES as readonly string[]).includes(file.type)) throw new Error('Choose a JPEG, PNG, or WebP image.')
  if (!file.size) throw new Error('This image is empty. Choose another file.')
  if (file.size > MAX_PRODUCT_IMAGE_BYTES) throw new Error('Choose an image no larger than 10 MiB.')
  const bytes = new Uint8Array(await file.slice(0, 12).arrayBuffer())
  const matches = file.type === 'image/jpeg' ? bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff
    : file.type === 'image/png' ? [137, 80, 78, 71, 13, 10, 26, 10].every((byte, index) => bytes[index] === byte)
      : String.fromCharCode(...bytes.slice(0, 4)) === 'RIFF' && String.fromCharCode(...bytes.slice(8, 12)) === 'WEBP'
  if (!matches) throw new Error('The file contents do not match the selected image type.')
  if (typeof createImageBitmap === 'function') {
    try { const bitmap = await createImageBitmap(file); bitmap.close() }
    catch { throw new Error('This image could not be decoded. Choose another JPEG, PNG, or WebP file.') }
  }
}

export function imageUploadFilename(name: string, type: string): string {
  const extension = type === 'image/jpeg' ? '.jpg' : type === 'image/png' ? '.png' : '.webp'
  const stem = name.replace(/^.*[\\/]/, '').replace(/\.[^.]*$/, '').replace(/[^A-Za-z0-9_-]/g, '_').replace(/^[_-]+/, '').slice(0, 100)
  return `${stem || 'product-image'}${extension}`
}

export function parseProductImage(value: unknown, shopId: string, productId: string): ProductImageMetadata {
  if (!value || typeof value !== 'object') throw new Error('Unreadable product image receipt.')
  const data = value as Record<string, unknown>
  if (typeof data.id !== 'string' || !data.id || data.shop_id !== shopId || data.product_id !== productId ||
    typeof data.filename !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/.test(data.filename) ||
    !(PRODUCT_IMAGE_TYPES as readonly unknown[]).includes(data.content_type) ||
    typeof data.size_bytes !== 'number' || !Number.isInteger(data.size_bytes) || data.size_bytes <= 0 || data.size_bytes > MAX_PRODUCT_IMAGE_BYTES ||
    typeof data.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(data.sha256) || data.storage_backend !== 'memory' ||
    typeof data.storage_ref !== 'string' || !data.storage_ref.startsWith('memory://product-images/') ||
    typeof data.uploaded_at !== 'string' || !Number.isFinite(Date.parse(data.uploaded_at))) throw new Error('Unreadable product image receipt.')
  return data as ProductImageMetadata
}

export async function uploadProductImage(config: { baseUrl: string; shopId: string }, productId: string, file: File, fetcher: typeof fetch = fetch): Promise<ProductImageMetadata> {
  if (!config.baseUrl || !config.shopId) throw new Error('Connect your shop before uploading a product image.')
  await validateProductImage(file)
  const form = new FormData()
  form.append('image', file, imageUploadFilename(file.name, file.type))
  let response: Response
  try {
    response = await fetcher(`${config.baseUrl.replace(/\/$/, '')}/api/v1/shops/${encodeURIComponent(config.shopId)}/products/${encodeURIComponent(productId)}/image`, {
      method: 'POST', headers: { Accept: 'application/json', 'X-Shop-ID': config.shopId }, body: form, signal: AbortSignal.timeout(20000),
    })
  } catch { throw new Error('Could not confirm the image upload. Your local preview is kept; check the connection before retrying.') }
  if (!response.ok) throw new Error(response.status === 404 ? 'The product-image service or product is unavailable (404). Your preview is still local.' : `Image upload failed (${response.status}). Your preview is still local.`)
  try { return parseProductImage(await response.json(), config.shopId, productId) } catch { throw new Error('Could not verify the image receipt. Check the backend before uploading again.') }
}
