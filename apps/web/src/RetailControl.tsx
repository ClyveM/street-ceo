import { useState } from 'react'
import type { Product } from './api'
import { PurchaseEntry } from './PurchaseEntry'
import { ExpenseGuide } from './ExpenseGuide'
import './costs.css'

export function RetailControl({ products, isDemo, initialProductId, onStockCount, onBack, onChanged }: { products: Product[]; isDemo: boolean; initialProductId?: string; onStockCount: () => void; onBack: () => void; onChanged: () => Promise<void> }) {
  const [tab, setTab] = useState<'purchase' | 'expense'>('purchase')
  return <section className="costs-workspace"><button className="back-link" onClick={onBack}>← Back to Stock</button><p className="eyebrow">RETAIL CONTROL</p><h2>Stock and spending.</h2><p>Receive purchases, record spending and open your dedicated stock count page. Cash close is available from Sell → End my day. Review every change before confirmation.</p>{isDemo && <p className="cost-warning">Starter catalogue only. Connect a live shop to save records.</p>}<nav className="cost-tabs" aria-label="Retail workflows">{([['purchase', 'Receive a purchase'], ['expense', 'Operating expenses']] as const).map(([key, label]) => <button key={key} type="button" aria-pressed={tab === key} onClick={() => setTab(key)}>{label}</button>)}<button type="button" onClick={onStockCount}>Stock count →</button></nav><div hidden={tab !== 'purchase'}><PurchaseEntry products={products} disabled={isDemo} initialProductId={initialProductId} onChanged={onChanged} confirmReady={true} /></div><div hidden={tab !== 'expense'}><ExpenseGuide disabled={isDemo} /></div></section>
}
