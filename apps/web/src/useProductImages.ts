import { useEffect, useRef, useState } from 'react'
import { getApiConfig } from './api'
import { uploadProductImage, validateProductImage, type ProductImageMetadata } from './productImages'

export type ProductPhoto = { file: File; previewUrl: string; status: 'local' | 'uploading' | 'uploaded' | 'error'; metadata?: ProductImageMetadata; error?: string }
export function useProductImages() {
  const [photos, setPhotos] = useState<Record<string, ProductPhoto>>({})
  const current = useRef(photos)
  current.current = photos
  const selections = useRef<Record<string, number>>({})
  const urls = useRef(new Set<string>())
  const active = useRef(true)
  useEffect(() => { active.current = true; return () => { active.current = false; urls.current.forEach((url) => URL.revokeObjectURL(url)); urls.current.clear() } }, [])
  const choose = async (productId: string, file: File) => {
    const selection = (selections.current[productId] ?? 0) + 1
    selections.current[productId] = selection
    await validateProductImage(file)
    if (!active.current || selections.current[productId] !== selection) return
    const previewUrl = URL.createObjectURL(file)
    urls.current.add(previewUrl)
    const previous = current.current[productId]
    if (previous) { URL.revokeObjectURL(previous.previewUrl); urls.current.delete(previous.previewUrl) }
    setPhotos((items) => ({ ...items, [productId]: { file, previewUrl, status: 'local' } }))
  }
  const upload = async (productId: string) => {
    const photo = current.current[productId]
    if (!photo || photo.status === 'uploading') return
    setPhotos((items) => ({ ...items, [productId]: { ...photo, status: 'uploading' } }))
    try {
      const metadata = await uploadProductImage(getApiConfig(), productId, photo.file)
      setPhotos((items) => items[productId]?.file === photo.file ? { ...items, [productId]: { ...photo, status: 'uploaded', metadata } } : items)
    } catch (failure) {
      setPhotos((items) => items[productId]?.file === photo.file ? { ...items, [productId]: { ...photo, status: 'error', error: failure instanceof Error ? failure.message : 'Image upload failed.' } } : items)
    }
  }
  return { photos, choose, upload }
}
