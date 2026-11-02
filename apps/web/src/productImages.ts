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

export async function listStoredProductImages(config:{baseUrl:string;shopId:string},fetcher:typeof fetch=fetch,signal?:AbortSignal):Promise<ProductImageMetadata[]> {
 const response=await fetcher(`${config.baseUrl.replace(/\/$/,'')}/api/v1/shops/${encodeURIComponent(config.shopId)}/product-images`,{headers:{Accept:'application/json','X-Shop-ID':config.shopId},signal,cache:'no-store'})
 if(!response.ok)throw new Error('Stored shop photos could not be loaded.')
 const values:unknown=await response.json();if(!Array.isArray(values))throw new Error('Stored shop photo index is unreadable.')
 const ids=new Set<string>();return values.map(value=>{if(!value||typeof value.product_id!=='string'||!value.product_id.trim())throw new Error('Stored image product reference is missing.');const item=parseProductImage(value,config.shopId,value?.product_id);if(ids.has(item.product_id))throw new Error('Stored photo index contains duplicate products.');ids.add(item.product_id);return item})
}
export async function fetchStoredProductImage(config:{baseUrl:string;shopId:string},metadata:ProductImageMetadata,fetcher:typeof fetch=fetch,signal?:AbortSignal):Promise<File> {
 if(metadata.shop_id!==config.shopId)throw new Error('Photo shop scope differs.')
 const response=await fetcher(`${config.baseUrl.replace(/\/$/,'')}/api/v1/shops/${encodeURIComponent(config.shopId)}/products/${encodeURIComponent(metadata.product_id)}/image/content`,{headers:{Accept:metadata.content_type,'X-Shop-ID':config.shopId},signal,cache:'no-store'})
 if(!response.ok)throw new Error('Stored shop photo is unavailable.')
 const mime=response.headers.get('Content-Type')?.split(';')[0],etag=response.headers.get('ETag')?.replace(/^W\//,'').replace(/"/g,'')
 if(mime!==metadata.content_type||etag&&etag!==metadata.sha256)throw new Error('Stored photo changed. Refresh it before relying on this preview.')
 const blob=await response.blob();if(blob.size!==metadata.size_bytes||blob.size>MAX_PRODUCT_IMAGE_BYTES)throw new Error('Stored photo size differs from its receipt.')
 await validateProductImage(blob)
 if(globalThis.crypto?.subtle){const digest=await crypto.subtle.digest('SHA-256',await blob.arrayBuffer());const hash=Array.from(new Uint8Array(digest),byte=>byte.toString(16).padStart(2,'0')).join('');if(hash!==metadata.sha256)throw new Error('Stored photo checksum differs from its receipt.')}
 return new File([blob],metadata.filename,{type:metadata.content_type})
}
export function productPhotoAlt(source:string|undefined,name:string):string { return `${source==='server'?'Stored shop photo':'Local preview'} for ${name}` }
