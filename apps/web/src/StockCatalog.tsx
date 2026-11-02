import type { Product } from './api'
import { useEffect, useRef, useState } from 'react'
import { ProductCostEditor } from './ProductCostEditor'
import { ProductImageControl } from './ProductImageControl'
import type { useProductImages } from './useProductImages'
import { filterStockProducts, stockPrice } from './stockPresentation'
import './product-images.css'
import './costs.css'
import './stock-catalog.css'

export function StockCatalog({products,isDemo,images,onOpenCosts,onOpenCount,onChanged,currency,onBlockingChange}:{products:Product[];isDemo:boolean;images:ReturnType<typeof useProductImages>;onOpenCosts(productId?:string):void;onOpenCount():void;onChanged():Promise<void>;currency?:string;onBlockingChange?(blocked:boolean):void}) {
 const [query,setQuery]=useState(''),[selectedId,setSelectedId]=useState<string|null>(null),[editing,setEditing]=useState(false),[costBlocking,setCostBlocking]=useState(false)
 const search=useRef<HTMLInputElement>(null),panel=useRef<HTMLElement>(null),rowButtons=useRef(new Map<string,HTMLButtonElement>()),lastSelected=useRef<Product|null>(null)
 const current=products.find(product=>product.id===selectedId),selected=current??(selectedId?lastSelected.current:null),photo=selected?images.photos[selected.id]:undefined
 const blocked=costBlocking||photo?.status==='uploading'
 useEffect(()=>{onBlockingChange?.(blocked)},[blocked,onBlockingChange])
 useEffect(()=>{if(selectedId){panel.current?.focus({preventScroll:true});panel.current?.scrollIntoView({block:'start'})}},[selectedId])
 const choose=(id:string)=>{if(blocked)return;const product=products.find(item=>item.id===id);if(!product)return;lastSelected.current=product;setEditing(false);setSelectedId(id);if(selectedId===id){panel.current?.focus({preventScroll:true});panel.current?.scrollIntoView({block:'start'})}}
 const close=()=>{if(blocked)return;const id=selectedId;setSelectedId(null);setEditing(false);requestAnimationFrame(()=>{const button=id?rowButtons.current.get(id):null;(button??search.current)?.focus()})}
 const filtered=filterStockProducts(products,query),low=products.filter(product=>product.stock_qty<8).length
 const price=(cents:number)=>`${currency?`${currency} `:''}${stockPrice(cents)}${currency?'':' (shop currency)'}`
 return <section className="stock-catalog-page">
  <header className="stock-catalog-heading"><div><p className="eyebrow">YOUR SHELVES, AT A GLANCE</p><h2>Stock</h2></div><span className="stock-catalog-total">{products.length} products</span></header>
  <div className="stock-catalog-toolbar"><span className="stock-low-summary">{low} low stock <small>under 8 units</small></span><div><button disabled={blocked} onClick={onOpenCount}>Stock count →</button><button disabled={blocked} onClick={()=>onOpenCosts()}>Purchases & spending →</button></div></div>
  <label className="stock-search"><span>Search stock</span><input ref={search} type="search" placeholder="Find a product or SKU" value={query} onChange={event=>setQuery(event.target.value)}/></label>
  {isDemo&&<p className="stock-demo-note" role="status">Starter catalogue · connect your shop to save changes.</p>}
  <div className="stock-table-wrap" role="region" aria-label="Stock table, scroll horizontally for wide values" tabIndex={0}><table className="stock-catalog-table"><caption>Tap a product to view its details and stock actions.</caption><colgroup><col className="stock-product-column"/><col className="stock-quantity-column"/><col className="stock-price-column"/></colgroup><thead><tr><th scope="col">Product</th><th scope="col">On hand</th><th scope="col">Sell price<small>{currency??'Shop currency'}</small></th></tr></thead><tbody>{filtered.map(product=><tr key={product.id} data-selected={selectedId===product.id||undefined} onClick={()=>choose(product.id)}><td><button ref={node=>{if(node)rowButtons.current.set(product.id,node);else rowButtons.current.delete(product.id)}} type="button" disabled={blocked} aria-expanded={selectedId===product.id} aria-controls="stock-product-details" onClick={event=>{event.stopPropagation();choose(product.id)}}><strong>{product.name}</strong><span>{product.sku}</span></button></td><td><strong className={product.stock_qty<8?'stock-quantity-low':''}>{product.stock_qty}</strong>{product.stock_qty<8&&<span className="stock-quantity-badge">{product.stock_qty===0?'Out':'Low'}</span>}</td><td className="stock-sell-price">{stockPrice(product.unit_price_cents)}</td></tr>)}</tbody></table></div>
  {filtered.length===0&&<div className="stock-search-empty"><h3>{query.trim()?'No matching products.':'No products to show.'}</h3><p>{query.trim()?'Try a product name or SKU.':'Your connected catalogue will appear here.'}</p>{query.trim()&&<button onClick={()=>{setQuery('');search.current?.focus()}}>Clear search</button>}</div>}
  {selected&&<section id="stock-product-details" ref={panel} tabIndex={-1} className="stock-product-panel" aria-labelledby="stock-product-title" onKeyDown={event=>{if(event.key==='Escape'){event.preventDefault();close()}}}><header><div><p className="eyebrow">PRODUCT DETAILS</p><h3 id="stock-product-title">{selected.name}</h3><p className="stock-product-sku">{selected.sku}</p></div><button disabled={blocked} onClick={close} aria-label="Close product details">Close</button></header>
   {!current&&<p className="cost-warning">This product is no longer in the loaded catalogue. Saved operation details are kept here; refresh Stock before making another change.</p>}
   <div className="stock-product-numbers"><div><span>On hand</span><strong>{selected.stock_qty} <small>units</small></strong></div><div><span>Sell price</span><strong>{price(selected.unit_price_cents)}</strong></div></div>
   <details className="stock-product-cost"><summary>Recorded cost per unit <strong>{selected.unit_cost_micros==null?'Not recorded':`${currency??'Shop currency'} ${(selected.unit_cost_micros/1000000).toFixed(6)}`}</strong></summary><p>Purchases use weighted-average cost. A cost correction replaces recorded unit cost without receiving stock or changing past receipt costs.</p>{selected.cost_source_invoice_id&&<p>Source invoice: {selected.cost_source_invoice_id}</p>}</details>
   <div className="stock-product-actions"><button disabled={blocked||!current} onClick={()=>onOpenCosts(selected.id)}>Receive a purchase</button><button disabled={isDemo||blocked||editing||!current} onClick={()=>setEditing(true)}>Edit recorded cost</button></div>
   {editing&&<ProductCostEditor key={`cost-${selected.id}`} product={selected} disabled={isDemo||!current} onChanged={onChanged} onClose={()=>{if(!blocked)setEditing(false)}} onBlockingChange={setCostBlocking}/>}
   {blocked&&<p className="stock-operation-note" role="status">{costBlocking?'Keep this product open until the cost request is verified.':'Uploading this product photo…'}</p>}
   <ProductImageControl key={`photo-${selected.id}`} name={selected.name} photo={photo} disabled={isDemo||costBlocking||!current} onChoose={file=>images.choose(selected.id,file)} onUpload={()=>images.upload(selected.id)}/>
  </section>}
 </section>
}
