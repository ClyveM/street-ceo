import type { Product } from './api'
export function filterStockProducts(products: Product[],query: string): Product[] { const needle=query.trim().toLowerCase();return products.filter(product=>!needle||product.name.toLowerCase().includes(needle)||product.sku.toLowerCase().includes(needle)) }
export function stockPrice(cents:number):string { if(!Number.isSafeInteger(cents)||cents<0)return 'Unavailable';const n=BigInt(cents);return `${n/100n}.${String(n%100n).padStart(2,'0')}` }
