import { useEffect, useRef, useState } from 'react'
import { getApiConfig } from './api'
import { fetchStoredProductImage, listStoredProductImages, uploadProductImage, validateProductImage, type ProductImageMetadata } from './productImages'

export type ProductPhoto = { source?: 'server'|'local'; file: File; previewUrl: string; status: 'local' | 'uploading' | 'uploaded' | 'error'; metadata?: ProductImageMetadata; error?: string }
export function useProductImages() {
  const [photos, setPhotos] = useState<Record<string, ProductPhoto>>({})
  const current = useRef(photos)
  current.current = photos
  const selections = useRef<Record<string, number>>({})
  const urls = useRef(new Set<string>())
  const active = useRef(true)
  const [error,setError]=useState('')
  const config=getApiConfig(),scope=`${config.baseUrl}|${config.shopId}`
  useEffect(()=>{let cancelled=false;const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),20000);current.current={};setPhotos({});selections.current={};urls.current.forEach(url=>URL.revokeObjectURL(url));urls.current.clear();setError('');
    void listStoredProductImages(config,fetch,controller.signal).then(async records=>{for(const record of records){if(cancelled)return;try{const selection=selections.current[record.product_id]??0;const file=await fetchStoredProductImage(config,record,fetch,controller.signal);if(cancelled||(selections.current[record.product_id]??0)!==selection||current.current[record.product_id]?.source==='local')continue;const previewUrl=URL.createObjectURL(file);urls.current.add(previewUrl);setPhotos(items=>{if((selections.current[record.product_id]??0)!==selection||items[record.product_id]?.source==='local'){URL.revokeObjectURL(previewUrl);urls.current.delete(previewUrl);return items};return {...items,[record.product_id]:{file,previewUrl,status:'uploaded',metadata:record,source:'server'}}})}catch{if(!cancelled)setError('Some stored shop photos could not be loaded. Local previews are kept.')}}}).catch(()=>{if(!cancelled)setError('Stored shop photos are unavailable. Local previews are kept.')}).finally(()=>clearTimeout(timer));
    return()=>{cancelled=true;controller.abort();clearTimeout(timer)}
  },[scope])
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
    setPhotos((items) => ({ ...items, [productId]: { file, previewUrl, status: 'local', source: 'local' } }))
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
  return { photos, choose, upload, error }
}
