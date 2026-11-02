import { useState } from 'react'
import type { Product } from './api'
import { PurchaseEntry } from './PurchaseEntry'
import { StockTake } from './StockTake'
import { ExpenseGuide } from './ExpenseGuide'
import './costs.css'

export function RetailControl({ products, isDemo, initialProductId, initialTab = 'purchase', onBack, onChanged }: { products: Product[]; isDemo: boolean; initialProductId?: string; initialTab?: 'purchase'|'count'; onBack: () => void; onChanged: () => Promise<void> }) {
  const [tab, setTab] = useState<'purchase' | 'count' | 'expense'>(initialTab)
  return <section className="costs-workspace"><button className="back-link" onClick={onBack}>← Back to Stock</button><p className="eyebrow">RETAIL CONTROL</p><h2>Stock and spending.</h2><p>Receive purchases, review stock counts and record spending. Cash close is available from Sell → End my day. Review every change before confirmation.</p>{isDemo && <p className="cost-warning">Starter catalogue only. Connect a live shop to save records.</p>}<nav className="cost-tabs" aria-label="Retail workflows">{([['purchase', 'Receive a purchase'], ['count', 'Stock take'], ['expense', 'Operating expenses']] as const).map(([key, label]) => <button key={key} type="button" aria-pressed={tab === key} onClick={() => setTab(key)}>{label}</button>)}</nav><div hidden={tab !== 'purchase'}><PurchaseEntry products={products} disabled={isDemo} initialProductId={initialProductId} onChanged={onChanged} confirmReady={true} /></div><div hidden={tab !== 'count'}><StockTake products={products} disabled={isDemo} onChanged={onChanged} /></div><div hidden={tab !== 'expense'}><ExpenseGuide disabled={isDemo} /></div></section>
}
