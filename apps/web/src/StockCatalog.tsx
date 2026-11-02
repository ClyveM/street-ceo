import type { Product } from './api'
import { useState } from 'react'
import { ProductCostEditor } from './ProductCostEditor'
import { ProductImageControl } from './ProductImageControl'
import type { useProductImages } from './useProductImages'
import './product-images.css'
import './costs.css'

export function StockCatalog({ products, isDemo, images, onOpenCosts, onChanged }: { products: Product[]; isDemo: boolean; images: ReturnType<typeof useProductImages>; onOpenCosts: (productId?: string) => void; onChanged: () => Promise<void> }) {
  const [editing, setEditing] = useState<string | null>(null)
  return <>
    <section className="section-head"><div><p className="eyebrow">INVENTORY</p><h2>Stock at a glance</h2></div><span className="counter">{products.length} products</span></section>
    <div className="stock-summary"><div><span>ON HAND</span><strong>{products.reduce((sum, product) => sum + product.stock_qty, 0)}</strong><small>units across catalogue</small></div><div><span>LOW STOCK</span><strong className="orange">{products.filter((product) => product.stock_qty < 8).length}</strong><small>under 8 units</small></div></div>
    <section className="stock-list">{products.map((product) => <div className="stock-row" key={product.id}>
      {images.photos[product.id] ? <img className="product-thumbnail" src={images.photos[product.id].previewUrl} alt={`Local preview: ${product.name}`} /> : <div className="product-avatar">{product.name.slice(0, 1)}</div>}
      <div><strong>{product.name}</strong><span>{product.sku}</span></div><b className={product.stock_qty < 8 ? 'low' : ''}>{product.stock_qty}<small> units</small></b>
      <details className="catalogue-cost"><summary>Recorded cost per base unit: <strong>{product.unit_cost_micros == null ? 'Not recorded' : (product.unit_cost_micros / 1000000).toFixed(6)}</strong></summary><p>Purchases use weighted-average cost. A confirmed correction replaces that cost. Amounts use the shop's configured currency.</p>{product.cost_source_invoice_id && <small>Source invoice: {product.cost_source_invoice_id}</small>}<div className="cost-actions"><button type="button" onClick={() => onOpenCosts(product.id)}>Receive a purchase for this product</button><button type="button" disabled={isDemo} onClick={() => setEditing(product.id)}>Edit recorded cost</button></div><p>A purchase receives additional stock. It is separate from a cost-only correction.</p>{editing === product.id && <ProductCostEditor key={product.id} product={product} disabled={isDemo} onChanged={onChanged} onClose={() => setEditing(null)} />}</details>
      <ProductImageControl name={product.name} photo={images.photos[product.id]} disabled={isDemo} onChoose={(file) => images.choose(product.id, file)} onUpload={() => images.upload(product.id)} />
    </div>)}</section>
    <section className="analysis-card"><p className="eyebrow">COST RECORDS</p><h3>Purchases, counts & daily close</h3><p>Receive multiple products with or without an invoice, count stock, and prepare cash/bank close.</p><button className="primary-action full" type="button" onClick={() => onOpenCosts()}>Open retail control →</button></section>
  </>
}
