import { useEffect, useRef, useState, type FormEvent } from 'react'
import { getApiConfig, type Product } from './api'
import { shopConfigurationError } from './muse'
import { imageUploadFilename, validateProductImage } from './productImages'
import { ProductImageControl } from './ProductImageControl'
import { requestSocialBrief, requestSocialImage, requestSocialDraft, previewImageRef, type SocialBrief, type SocialImageRequest, type SocialImageResult, type SocialDraftResult } from './social'
import type { useProductImages } from './useProductImages'
import './social.css'

function downloadText(filename: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }))
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function SocialUpdate({ products, isDemo, images, onBack }: { products: Product[]; isDemo: boolean; images: ReturnType<typeof useProductImages>; onBack: () => void }) {
  const [selected, setSelected] = useState<string[]>([])
  const [brief, setBrief] = useState('Create a Facebook post image featuring these shop products. Use only the supplied product facts.')
  const [aspect, setAspect] = useState<SocialImageRequest['aspect_ratio']>('1:1')
  const [sourceImage, setSourceImage] = useState('')
  const [shopPhoto, setShopPhoto] = useState<File | null>(null)
  const [shopPreview, setShopPreview] = useState('')
  const [needsShopPhoto, setNeedsShopPhoto] = useState(false)
  const [verified, setVerified] = useState<SocialBrief | null>(null)
  const [imageResult, setImageResult] = useState<SocialImageResult | null>(null)
  const [busy, setBusy] = useState<'brief' | 'image' | 'draft' | null>(null)
  const [error, setError] = useState('')
  const [caption, setCaption] = useState('')
  const [script, setScript] = useState('')
  const [shots, setShots] = useState('')
  const [draft, setDraft] = useState<SocialDraftResult | null>(null)
  const [imageError, setImageError] = useState('')
  const [exporting, setExporting] = useState(false)
  const pending = useRef<AbortController | null>(null)
  const shopPhotoSelection = useRef(0)
  const configError = shopConfigurationError(getApiConfig())
  useEffect(() => () => { pending.current?.abort(); shopPhotoSelection.current += 1 }, [])
  useEffect(() => () => { if (shopPreview) URL.revokeObjectURL(shopPreview) }, [shopPreview])
  useEffect(() => {
    if (sourceImage && !selected.some((id) => images.photos[id]?.metadata?.id === sourceImage)) { setSourceImage(''); setImageResult(null) }
  }, [sourceImage, selected, images.photos])
  const clearEvidence = () => { pending.current?.abort(); pending.current = null; setBusy(null); setVerified(null); setImageResult(null); setDraft(null); setError('') }
  const chooseProduct = (id: string) => {
    clearEvidence(); setSourceImage('')
    setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length < 12 ? [...current, id] : current)
  }
  const verify = async (event: FormEvent) => {
    event.preventDefault()
    if (isDemo || configError || busy) return
    if (needsShopPhoto && !shopPhoto) { setError('Choose a shop photo, or turn off the shop-photo option.'); return }
    const request = new AbortController(); pending.current = request; setBusy('brief'); setError('')
    try {
      const result = await requestSocialBrief(getApiConfig(), { product_ids: selected, shop_image: needsShopPhoto && shopPhoto ? { filename: imageUploadFilename(shopPhoto.name, shopPhoto.type), content_type: shopPhoto.type, size_bytes: shopPhoto.size } : null }, request.signal)
      if (!request.signal.aborted) setVerified(result)
    } catch (failure) { if (!request.signal.aborted) setError(failure instanceof Error ? failure.message : 'Could not verify the brief.') }
    finally { if (pending.current === request) { pending.current = null; setBusy(null) } }
  }
  const generateImage = async () => {
    if (!verified || busy || isDemo || configError) return
    const request = new AbortController(); pending.current = request; setBusy('image'); setError(''); setImageResult(null); setImageError('')
    try {
      const shopPhotoData = needsShopPhoto && shopPhoto ? await readShopPhoto(shopPhoto) : undefined
      if (request.signal.aborted) return
      const result = await requestSocialImage(getApiConfig(), { product_ids: selected, brief, aspect_ratio: aspect, shop_photo_data: shopPhotoData, ...(sourceImage ? { source_image_id: sourceImage } : {}) }, request.signal)
      if (!request.signal.aborted) setImageResult(result)
    } catch (failure) { if (!request.signal.aborted) setError(failure instanceof Error ? failure.message : 'Could not request an image.') }
    finally { if (pending.current === request) { pending.current = null; setBusy(null) } }
  }
  const generateDraft = async () => {
    if (!verified || busy || isDemo || configError) return
    const request = new AbortController(); pending.current = request; setBusy('draft'); setError(''); setDraft(null)
    try {
      const result = await requestSocialDraft(getApiConfig(), { product_ids: selected, brief, duration_seconds: 40, ...(sourceImage ? { source_image_id: sourceImage } : {}) }, request.signal)
      if (!request.signal.aborted) { setDraft(result); if (result.status === 'draft') { setCaption(result.caption); setScript(result.voiceover_script); setShots(result.shot_list.join('\n')) } }
    } catch (failure) { if (!request.signal.aborted) setError(failure instanceof Error ? failure.message : 'Could not request a social draft.') }
    finally { if (pending.current === request) { pending.current = null; setBusy(null) } }
  }
  const imageUrl = previewImageRef(imageResult?.output_url ?? null)
  const downloadImage = async () => {
    if (!imageUrl || exporting) return
    setExporting(true); setImageError('')
    try {
      const response = await fetch(imageUrl)
      if (!response.ok) throw new Error()
      const blob = await response.blob()
      if (!['image/png', 'image/jpeg', 'image/webp'].includes(blob.type.split(';')[0])) throw new Error()
      const url = URL.createObjectURL(blob), anchor = document.createElement('a')
      anchor.href = url; anchor.download = `social-draft.${blob.type.includes('jpeg') ? 'jpg' : blob.type.includes('webp') ? 'webp' : 'png'}`; anchor.click()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch { setImageError('Could not download the image from this browser. Open the returned image and save it there.') }
    finally { setExporting(false) }
  }
  const sourcePhotos = selected.flatMap((id) => images.photos[id]?.metadata ? [{ product: products.find((item) => item.id === id)!, metadata: images.photos[id].metadata! }] : [])
  return <section className="social-workflow"><button className="back-link" onClick={onBack}>← Back to Today</button><div className="tool-hero social-tool"><p className="eyebrow">SOCIAL UPDATE</p><h2>Prepare a post or Reel brief.</h2><p>Choose real shop products, review the inputs, then request a draft. Nothing is published automatically.</p></div>
    {(isDemo || configError) && <p className="social-warning" role="status">{configError ?? 'Starter catalogue preview only. Connect a live shop catalogue before submitting a draft request.'}</p>}
    <form className="analysis-card" onSubmit={(event) => { void verify(event) }}><h3>1. Choose products</h3><p>Choose up to 12. Photos are optional and never imply sales popularity.</p><div className="social-product-list">{products.map((product) => <article key={product.id}><label><input type="checkbox" checked={selected.includes(product.id)} disabled={!!busy || (!selected.includes(product.id) && selected.length >= 12)} onChange={() => chooseProduct(product.id)} />{images.photos[product.id] && <img src={images.photos[product.id].previewUrl} alt={`Local preview: ${product.name}`} />}<span><strong>{product.name}</strong><small>{product.sku}</small></span></label><ProductImageControl name={product.name} photo={images.photos[product.id]} disabled={isDemo || !!busy} onChoose={(file) => images.choose(product.id, file)} onUpload={() => images.upload(product.id)} /></article>)}</div>
      <h3>2. Shop photo</h3><label className="social-check"><input type="checkbox" checked={needsShopPhoto} onChange={(event) => { clearEvidence(); setNeedsShopPhoto(event.target.checked) }} />Use a shop photo in the generated image</label>
      {needsShopPhoto && <><label>Choose a shop photo<input type="file" accept="image/jpeg,image/png,image/webp" disabled={!!busy} onChange={(event) => { const file = event.target.files?.[0]; event.target.value = ''; if (file) { clearEvidence(); const selection = ++shopPhotoSelection.current; setShopPhoto(null); setShopPreview(''); void validateProductImage(file).then(() => { if (shopPhotoSelection.current === selection) { setShopPhoto(file); setShopPreview(URL.createObjectURL(file)) } }).catch((failure) => { if (shopPhotoSelection.current === selection) setError(failure instanceof Error ? failure.message : 'Invalid image.') }) } }} /></label>{shopPreview && <figure><img className="shop-photo-preview" src={shopPreview} alt="Local shop-photo preview" /><figcaption>This photo will be sent to Muse as an image reference when you request a draft image.</figcaption></figure>}</>}
      <button type="submit" className="primary-action full" disabled={isDemo || !!configError || !selected.length || !!busy}>{busy === 'brief' ? 'Verifying catalogue…' : 'Verify selected products'}</button>
    </form>
    {verified && <section className="analysis-card"><h3>Catalogue verified</h3><p>Source: connected repository · verified {new Date(verified.created_at).toLocaleString()}.</p><ul>{verified.products.map((product) => <li key={product.product_id}>{product.name} · {product.stock_qty} units recorded</li>)}</ul><p>This verifies product facts only. It is not an AI-generated draft.</p></section>}
    <section className="analysis-card"><h3>3. Muse post-image request</h3><label>Describe the image<textarea value={brief} maxLength={1000} rows={4} disabled={!!busy} onChange={(event) => { setBrief(event.target.value); setImageResult(null) }} /></label><label>Image shape<select value={aspect} disabled={!!busy} onChange={(event) => { setAspect(event.target.value as SocialImageRequest['aspect_ratio']); setImageResult(null) }}><option value="1:1">Square · 1:1</option><option value="4:5">Portrait post · 4:5</option><option value="9:16">Reel cover · 9:16</option><option value="16:9">Landscape · 16:9</option></select></label><label>Product-image reference<select value={sourceImage} disabled={!!busy} onChange={(event) => { setSourceImage(event.target.value); setImageResult(null) }}><option value="">No image reference</option>{sourcePhotos.map((item) => <option key={item.metadata.id} value={item.metadata.id}>{item.product.name} · uploaded this API session</option>)}</select></label><p>Choose a product photo reference if you want Muse to use it alongside the shop photo.</p><button className="primary-action full" type="button" disabled={!verified || !!busy || !brief.trim() || isDemo || !!configError} onClick={() => { void generateImage() }}>{busy === 'image' ? 'Requesting image…' : imageResult?.status === 'draft' ? 'Regenerate image' : imageResult ? 'Retry image request' : 'Request Muse image'}</button>
      <div className="generated-image-preview" role="status">{busy === 'image' ? 'Waiting for the image service…' : imageResult?.status === 'draft' && imageUrl ? <figure><img className="shop-photo-preview" src={imageUrl} alt="Provider-generated social draft for review" onError={() => setImageError('The returned image could not be displayed.')} /><figcaption>Draft image · provider: {imageResult.provider} · model: {imageResult.model ?? 'not supplied'}</figcaption></figure> : imageResult ? `No preview available · ${imageResult.status.replace(/_/g, ' ')}.` : 'No generated image yet. Verify products, then request an image.'}</div>
      {imageResult && <ul>{imageResult.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>}
      <button type="button" disabled={!imageUrl || imageResult?.status !== 'draft' || exporting} onClick={() => { void downloadImage() }}>{exporting ? 'Downloading…' : 'Download generated draft image'}</button>{imageUrl && <p><a href={imageUrl} target="_blank" rel="noopener noreferrer">Open returned image for review</a></p>}{imageError && <p role="alert">{imageError}</p>}<p>Image generation requires a configured provider. An image returned as a provider file ID needs a URL before this browser can preview or download it. Nothing is published.</p>
    </section>
    <section className="analysis-card"><h3>4. Editable post / Reel copy</h3><p>Request a 40-second draft using the verified products and the brief above, or write a manual draft. Review names, prices, and every claim before export.</p><button className="primary-action full" type="button" disabled={!verified || !!busy || !brief.trim() || isDemo || !!configError} onClick={() => { void generateDraft() }}>{busy === 'draft' ? 'Requesting draft…' : draft?.status === 'draft' ? 'Regenerate text draft' : 'Request Muse text draft'}</button>
      {draft && <div role="status"><h4>{draft.title}</h4><p>{draft.status === 'draft' ? `AI draft · ${draft.provider} · ${draft.model ?? 'model not supplied'}` : `Draft unavailable · ${draft.source}`}</p><ul>{draft.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>{draft.status === 'unavailable' && <p>{draft.caption}</p>}</div>}
      <label>{draft?.status === 'draft' ? 'Review/edit caption' : 'Your manual caption'}<textarea rows={5} value={caption} onChange={(event) => setCaption(event.target.value)} placeholder="Write your caption…" /></label><label>Review/edit Reel voiceover<textarea rows={5} value={script} onChange={(event) => setScript(event.target.value)} /></label><label>Review/edit shot list (one shot per line)<textarea rows={4} value={shots} onChange={(event) => setShots(event.target.value)} /></label>
      {draft?.claims.length ? <details><summary>Product evidence for returned claims</summary><ul>{draft.claims.map((claim, index) => <li key={index}>{claim.claim} · {claim.source_field} · {claim.product_id}</li>)}</ul></details> : null}
      <button type="button" disabled={!caption.trim() && !script.trim()} onClick={() => downloadText('social-draft.txt', [caption, script, shots].filter(Boolean).join('\n\n'))}>Export reviewed draft</button><button type="button" disabled={!verified} onClick={() => downloadText('social-product-brief.txt', JSON.stringify({ ...verified, image_request: brief, draft_only: true }, null, 2))}>Export verified brief</button><p>Exports download a local file. Facebook publishing, scheduling, and video rendering are not connected.</p>
    </section>
    {error && <p className="social-error" role="alert">{error}</p>}
  </section>
}

function readShopPhoto(file: File): Promise<string> {
  if (file.size > 5 * 1024 * 1024) throw new Error('Choose a shop photo no larger than 5 MiB.')
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result))
    reader.onerror = () => reject(new Error('Could not read the shop photo.'))
    reader.readAsDataURL(file)
  })
}
