import { useState } from 'react'
import type { Product } from './api'
import { Invoices } from './Invoices'
import { ExpenseGuide } from './ExpenseGuide'
import './costs.css'

export function CostsWorkspace({ products, isDemo, initialProductId, onBack, onProductsChanged }: { products: Product[]; isDemo: boolean; initialProductId?: string; onBack: () => void; onProductsChanged: () => Promise<void> }) {
  const [tab, setTab] = useState<'invoices' | 'expenses'>('invoices')
  return <section className="costs-workspace"><button className="back-link" onClick={onBack}>← Back to Stock</button><p className="eyebrow">COST RECORDS</p><h2>Invoices & operating expenses</h2><p>Review the source and confirm each change. Amounts use the shop's configured currency.</p>{isDemo && <p className="cost-warning" role="status">Starter catalogue only. Connect a live shop before uploading, reviewing, or confirming cost records.</p>}<div className="cost-tabs" role="group" aria-label="Cost workflows"><button aria-pressed={tab === 'invoices'} onClick={() => setTab('invoices')}>Supplier invoices</button><button aria-pressed={tab === 'expenses'} onClick={() => setTab('expenses')}>Operating expenses</button></div><div hidden={tab !== 'invoices'}><Invoices products={products} disabled={isDemo} initialProductId={initialProductId} onProductsChanged={onProductsChanged} /></div><div hidden={tab !== 'expenses'}><ExpenseGuide disabled={isDemo} /></div></section>
}
