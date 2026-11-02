import { productPhotoAlt } from './productImages'
import { useState } from 'react'
import type { ProductPhoto } from './useProductImages'

export function ProductImageControl({ name, photo, disabled, onChoose, onUpload }: { name: string; photo?: ProductPhoto; disabled: boolean; onChoose: (file: File) => Promise<void>; onUpload: () => Promise<void> }) {
  const [error, setError] = useState('')
  return <details className="product-image-control"><summary>Product photo · optional</summary>
    {photo && <figure><img src={photo.previewUrl} alt={productPhotoAlt(photo.source,name)} /><figcaption>{photo.source==='server'?'Stored shop photo':'Local preview'} · {photo.file.name}</figcaption></figure>}
    <label>Choose a photo for {name}<input type="file" accept="image/jpeg,image/png,image/webp" disabled={photo?.status === 'uploading'} onChange={(event) => { const file = event.target.files?.[0]; event.target.value = ''; if (file) { setError(''); void onChoose(file).catch((failure) => setError(failure instanceof Error ? failure.message : 'Could not load image.')) } }} /></label>
    <p>JPEG, PNG, or WebP · up to 10 MiB. Preview stays on this page until you upload.</p>
    {photo && <button type="button" disabled={disabled || photo.status === 'uploading' || photo.status === 'uploaded'} onClick={() => { void onUpload() }}>{photo.status === 'uploading' ? 'Uploading…' : photo.status === 'uploaded' ? 'Image receipt verified' : 'Upload product image'}</button>}
    {disabled && <p>Connect a live catalogue before uploading. Demo previews are not saved to the shop.</p>}
    {photo?.status === 'uploaded' && <p role="status">{photo.source==='server'?'Stored shop photo loaded from this shop’s saved image.':'Image saved to the shop. This device is showing its local preview.'}</p>}
    {(error || photo?.error) && <p role="alert">{error || photo?.error}</p>}
  </details>
}
