import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { apiClient, demoProducts, formatMoney, Product, Tender } from './api'

type View = 'today' | 'sell' | 'stock' | 'monitor'
type Basket = Record<number, number>

type AgentActivity = {
  name: string
  role: string
  status: 'Working' | 'Ready' | 'Review'
  task: string
  files: string[]
  lastActivity: string
  accent: string
}

type TeamStats = {
  completedTasks: number
  activeTasks: number
  commits: number
  totalUnitTests: number
  passingUnitTests: number
  warnings: string[]
}

type TeamSnapshot = { agents: AgentActivity[]; stats: TeamStats }

const fallbackTeamSnapshot: TeamSnapshot = {
  agents: [
  { name: 'Hwaro', role: 'Backend & Database', status: 'Working', task: 'Persistence adapter', files: ['services/api/persistence.py', 'services/api/app.py'], lastActivity: '2 min ago', accent: '#8a6de9' },
  { name: 'Verengai', role: 'Financial Systems', status: 'Review', task: 'MVP ledger and cash movements', files: ['services/finance/ledger.py'], lastActivity: '8 min ago', accent: '#e1843d' },
  { name: 'Dura', role: 'Inventory & Retail', status: 'Working', task: 'Weighted-average stock costs', files: ['services/inventory/movements.py', 'services/inventory/test_movements.py'], lastActivity: '4 min ago', accent: '#d05c8b' },
  { name: 'Runako', role: 'Frontend & UX', status: 'Working', task: 'Mobile-first web shell', files: ['apps/web/src/App.tsx', 'apps/web/src/styles.css', 'apps/web/src/api.ts'], lastActivity: 'Just now', accent: '#0b8f83' },
  { name: 'Fambai', role: 'Mobile & Offline', status: 'Ready', task: 'Offline queue and sync contract', files: ['apps/web/service-worker.js'], lastActivity: '12 min ago', accent: '#3d91c7' },
  { name: 'Inzwi', role: 'Voice AI', status: 'Working', task: 'Apo/Napo interaction adapter', files: ['services/voice/state_machine.py'], lastActivity: '6 min ago', accent: '#d49a29' },
  ],
  stats: { completedTasks: 7, activeTasks: 6, commits: 12, totalUnitTests: 40, passingUnitTests: 40, warnings: ['npm registry unavailable for frontend build', 'Fambai offline queue awaiting integration'] },
}

declare global { interface Window { __STREET_CEO_TEAM_ACTIVITY__?: TeamSnapshot } }

function getTeamSnapshot(): TeamSnapshot {
  return typeof window !== 'undefined' && window.__STREET_CEO_TEAM_ACTIVITY__ ? window.__STREET_CEO_TEAM_ACTIVITY__ : fallbackTeamSnapshot
}

function Logo() {
  return <div className="brand-mark" aria-label="Street CEO logo"><span>SC</span></div>
}

function App() {
  const [view, setView] = useState<View>('today')
  const [products, setProducts] = useState<Product[]>(demoProducts)
  const [isDemo, setIsDemo] = useState(true)
  const [basket, setBasket] = useState<Basket>({})
  const [tender, setTender] = useState<Tender>('cash')
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [online, setOnline] = useState(navigator.onLine)
  const [monitorMode, setMonitorMode] = useState<'2d' | '3d'>('2d')

  useEffect(() => {
    const load = async () => {
      setIsLoading(true)
      const result = await apiClient.listProducts()
      setProducts(result.products)
      setIsDemo(result.isDemo)
      setIsLoading(false)
    }
    void load()
    const update = () => setOnline(navigator.onLine)
    window.addEventListener('online', update)
    window.addEventListener('offline', update)
    return () => { window.removeEventListener('online', update); window.removeEventListener('offline', update) }
  }, [])

  const filteredProducts = useMemo(() => products.filter((product) => product.name.toLowerCase().includes(query.toLowerCase()) || product.sku.toLowerCase().includes(query.toLowerCase())), [products, query])
  const basketItems = products.filter((product) => basket[product.id]).map((product) => ({ ...product, quantity: basket[product.id] }))
  const total = basketItems.reduce((sum, product) => sum + product.unit_price_cents * product.quantity, 0)
  const itemCount = basketItems.reduce((sum, product) => sum + product.quantity, 0)

  const addToBasket = (product: Product) => setBasket((current) => ({ ...current, [product.id]: Math.min(product.stock_qty, (current[product.id] ?? 0) + 1) }))
  const removeFromBasket = (product: Product) => setBasket((current) => { const next = { ...current }; if (next[product.id] > 1) next[product.id] -= 1; else delete next[product.id]; return next })
  const submitSale = async () => {
    if (!basketItems.length) return
    setNotice(null)
    try {
      const sale = await apiClient.createSale({ lines: basketItems.map(({ id, quantity }) => ({ product_id: id, quantity })), tender })
      setBasket({})
      setNotice({ type: 'success', text: `Sale ${sale.id} recorded · ${formatMoney(total)} via ${tender}` })
    } catch {
      setNotice({ type: 'error', text: online ? 'Could not record sale. Check the API and try again.' : 'You are offline. Sale queue will be added by Fambai.' })
    }
  }

  return <div className="app-shell">
    <header className="topbar">
      <div className="brand"><Logo /><div><strong>Street CEO</strong><span>Your shop, in control.</span></div></div>
      <div className={`connection-pill ${online ? 'online' : 'offline'}`}><span className="status-dot" />{online ? 'Online' : 'Offline'}</div>
    </header>

    <main className="page">
      <section className="welcome"><div><p className="eyebrow">Thursday, 30 October</p><h1>Good morning, Tendai.</h1><p className="muted">Here’s how your shop is doing today.</p></div><div className="avatar" aria-label="Account for Tendai">T</div></section>
      {isDemo && <div className="demo-banner"><span>✦</span><span><strong>Demo mode</strong> · Showing starter catalogue data. Connect the API to use live shop data.</span></div>}
      {notice && <div className={`notice ${notice.type}`} role="status"><span>{notice.type === 'success' ? '✓' : '!'}</span>{notice.text}<button aria-label="Dismiss message" onClick={() => setNotice(null)}>×</button></div>}

      {view === 'today' && <Today onSell={() => setView('sell')} />}
      {view === 'sell' && <Sell products={filteredProducts} allProducts={products} query={query} setQuery={setQuery} basketItems={basketItems} total={total} itemCount={itemCount} tender={tender} setTender={setTender} addToBasket={addToBasket} removeFromBasket={removeFromBasket} submitSale={submitSale} isLoading={isLoading} />}
      {view === 'stock' && <Stock products={products} />}
      {view === 'monitor' && (monitorMode === '2d' ? <TeamMonitor onOpenCommandRoom={() => setMonitorMode('3d')} /> : <CommandRoom onBack={() => setMonitorMode('2d')} />)}
    </main>

    <nav className="bottom-nav" aria-label="Main navigation">{([['today', '⌂', 'Today'], ['sell', '+', 'Sell'], ['stock', '▥', 'Stock'], ['monitor', '◌', 'Team']] as const).map(([key, icon, label]) => <button key={key} className={view === key ? 'active' : ''} onClick={() => setView(key)} aria-current={view === key ? 'page' : undefined}><span className="nav-icon">{icon}</span>{label}{key === 'sell' && itemCount > 0 && <b className="basket-badge">{itemCount}</b>}</button>)}</nav>
  </div>
}

function Today({ onSell }: { onSell: () => void }) { return <><section className="hero-card"><div><span className="card-kicker">TODAY’S SALES</span><strong className="hero-amount">$42.80</strong><span className="hero-meta"><span className="up">↑ 12%</span> from yesterday</span></div><div className="sparkline" aria-label="Sales trending up"><i /><i /><i /><i /><i /><i /><i /></div></section><section className="stat-grid"><div className="stat-card"><span>SALES</span><strong>18</strong><small>transactions</small></div><div className="stat-card"><span>STOCK ALERTS</span><strong className="orange">3</strong><small>need attention</small></div></section><section className="section-head"><div><p className="eyebrow">QUICK ACTION</p><h2>Keep the tills moving.</h2></div></section><button className="primary-action full" onClick={onSell}><span className="action-icon">+</span>Record a sale<span className="arrow">→</span></button><div className="insight-card"><span className="insight-icon">✦</span><div><p className="eyebrow">STREET CEO INSIGHT</p><p>Cold drinks are moving fast today. Check your Coca-Cola stock before lunch.</p></div></div></> }

type SellProps = { products: Product[]; allProducts: Product[]; query: string; setQuery: (value: string) => void; basketItems: (Product & { quantity: number })[]; total: number; itemCount: number; tender: Tender; setTender: (value: Tender) => void; addToBasket: (product: Product) => void; removeFromBasket: (product: Product) => void; submitSale: () => void; isLoading: boolean }
function Sell({ products, allProducts, query, setQuery, basketItems, total, itemCount, tender, setTender, addToBasket, removeFromBasket, submitSale, isLoading }: SellProps) { return <><section className="section-head sell-heading"><div><p className="eyebrow">NEW SALE</p><h2>What did you sell?</h2></div><span className="counter">{itemCount} items</span></section><label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search catalogue" aria-label="Search catalogue" /><kbd>⌘ K</kbd></label><div className="product-list">{isLoading ? <div className="placeholder">Loading your catalogue…</div> : products.length ? products.map((product) => <ProductRow key={product.id} product={product} quantity={basketItems.find((item) => item.id === product.id)?.quantity ?? 0} add={addToBasket} remove={removeFromBasket} />) : <div className="placeholder"><strong>No products found</strong><span>Try a different search term.</span></div>}</div><section className="basket-panel"><div className="section-head"><div><p className="eyebrow">CURRENT BASKET</p><h2>{itemCount ? `${itemCount} item${itemCount === 1 ? '' : 's'}` : 'Basket is empty'}</h2></div><strong className="basket-total">{formatMoney(total)}</strong></div>{!itemCount && <p className="muted">Tap a product above to start a sale.</p>}{basketItems.map((item) => <div className="basket-line" key={item.id}><span>{item.name} × {item.quantity}</span><strong>{formatMoney(item.unit_price_cents * item.quantity)}</strong></div>)}<div className="tender-label">PAYMENT METHOD</div><div className="tender-toggle" role="group" aria-label="Payment method"><button className={tender === 'cash' ? 'selected' : ''} onClick={() => setTender('cash')}>◉ Cash</button><button className={tender === 'bank' ? 'selected' : ''} onClick={() => setTender('bank')}>▣ Bank</button></div><button className="primary-action full" disabled={!itemCount} onClick={submitSale}>Complete sale <span className="arrow">→</span></button><p className="offline-note">{navigator.onLine ? '✓ Ready to record' : '○ Offline queue coming soon'}</p></section></> }

function ProductRow({ product, quantity, add, remove }: { product: Product; quantity: number; add: (product: Product) => void; remove: (product: Product) => void }) { return <article className="product-row"><div className="product-avatar">{product.name.slice(0, 1)}</div><div className="product-info"><strong>{product.name}</strong><span>{product.sku} · {product.stock_qty} in stock</span></div><div className="product-price">{formatMoney(product.unit_price_cents)}</div><div className="stepper">{quantity > 0 && <><button onClick={() => remove(product)} aria-label={`Remove one ${product.name}`}>−</button><span>{quantity}</span></>}<button className={quantity ? '' : 'add'} onClick={() => add(product)} aria-label={`Add ${product.name}`}>{quantity ? '+' : 'Add'}</button></div></article> }

function Stock({ products }: { products: Product[] }) { return <><section className="section-head"><div><p className="eyebrow">INVENTORY</p><h2>Stock at a glance</h2></div><span className="counter">{products.length} products</span></section><div className="stock-summary"><div><span>ON HAND</span><strong>{products.reduce((sum, product) => sum + product.stock_qty, 0)}</strong><small>units across catalogue</small></div><div><span>LOW STOCK</span><strong className="orange">{products.filter((product) => product.stock_qty < 8).length}</strong><small>under 8 units</small></div></div><section className="stock-list">{products.map((product) => <div className="stock-row" key={product.id}><div className="product-avatar">{product.name.slice(0, 1)}</div><div><strong>{product.name}</strong><span>{product.sku}</span></div><b className={product.stock_qty < 8 ? 'low' : ''}>{product.stock_qty}<small> units</small></b></div>)}</section><div className="placeholder subtle"><strong>Stock actions coming next</strong><span>Purchases and adjustments will appear here as the inventory service lands.</span></div></> }

function TeamMonitor({ onOpenCommandRoom }: { onOpenCommandRoom: () => void }) {
  const snapshot = getTeamSnapshot()
  const [line, setLine] = useState(0)
  const simulatedLines = ['→ coordinating the next handoff…', '  checking acceptance criteria', '  updating local activity model', '✓ ready for the next review']
  useEffect(() => { const timer = window.setInterval(() => setLine((current) => (current + 1) % simulatedLines.length), 2200); return () => window.clearInterval(timer) }, [])
  return <><section className="section-head monitor-heading"><div><p className="eyebrow">LOCAL TEAM MONITOR</p><h2>Everyone in the loop.</h2><p className="muted">A quick view of the Street CEO build lanes.</p></div><div className="monitor-actions"><span className="live-chip"><i /> local</span><button className="room-button" onClick={onOpenCommandRoom}>Open 3D room →</button></div></section><div className="simulation-banner"><span>◎</span><span><strong>Simulation</strong> · Activity below is a local mock preview, not a real line-by-line subagent stream.</span></div><section className="team-lanes">{snapshot.agents.map((agent) => <article className="agent-lane" key={agent.name}><div className="agent-avatar" style={{ background: agent.accent }}>{agent.name.slice(0, 1)}</div><div className="agent-main"><div className="agent-title"><strong>{agent.name}</strong><span>{agent.role}</span><b className={`agent-status ${agent.status.toLowerCase()}`}>{agent.status}</b></div><p>{agent.task}</p><div className="agent-meta"><span>{agent.files.length} changed file{agent.files.length === 1 ? '' : 's'}</span><span>·</span><span>{agent.lastActivity}</span></div><details><summary>View changed files</summary><ul>{agent.files.map((file) => <li key={file}><code>{file}</code></li>)}</ul></details></div></article>)}</section><section className="activity-panel"><div className="activity-panel-head"><div><p className="eyebrow">CODE ACTIVITY PREVIEW</p><h3>Simulated handoff feed</h3></div><span className="sim-tag">SIMULATION</span></div><div className="terminal"><div className="terminal-dots"><i /><i /><i /><span>team-monitor.local</span></div><p><b>runako@street-ceo</b> <span>~</span> $ watch --demo-activity</p><p className="typing-line">{simulatedLines[line]}<em>▋</em></p><small>Local preview only · no live agent stream connected</small></div></section></>
}

function CommandRoom({ onBack }: { onBack: () => void }) {
  const snapshot = getTeamSnapshot()
  const desks = [{ name: 'Mutungamiri', role: 'CTO & Lead Orchestrator', status: 'Working' as const, task: 'Integrating the Wave 2 lanes', lastActivity: 'Just now', accent: '#102a43' }, ...snapshot.agents]
  return <section className="command-room"><div className="room-heading"><div><p className="eyebrow">SIMULATED COMMAND ROOM</p><h2>Street CEO control floor.</h2><p className="muted">A CSS 3D preview of the team workspace. Scene and activity are simulated.</p></div><button className="room-button" onClick={onBack}>← Back to 2D monitor</button></div><div className="wall-board"><div className="wall-title"><span>STREET CEO / WAVE 2</span><b>SHARED WALL BOARD</b></div><div className="wall-stats"><div><strong>{snapshot.stats.completedTasks}</strong><span>COMPLETED TASKS</span></div><div><strong>{snapshot.stats.activeTasks}</strong><span>ACTIVE TASKS</span></div><div><strong>{snapshot.stats.commits}</strong><span>COMMITS</span></div><div><strong>{snapshot.stats.passingUnitTests}/{snapshot.stats.totalUnitTests}</strong><span>PASSING / TOTAL UNIT TESTS</span></div><div className="warning-stat"><strong>{snapshot.stats.warnings.length}</strong><span>WARNINGS / BLOCKED</span></div></div><div className="wall-warnings">{snapshot.stats.warnings.map((warning) => <span key={warning}>! {warning}</span>)}</div></div><div className="room-legend"><span>◎ simulated scene</span><span>◌ local activity snapshot</span></div><div className="room-stage" aria-label="Simulated 3D Street CEO command room"><div className="room-ceiling" /><div className="room-floor"><div className="cto-zone"><RoomDesk desk={desks[0]} isCto /></div><div className="specialist-zone">{desks.slice(1).map((desk) => <RoomDesk key={desk.name} desk={desk} />)}</div></div></div><div className="room-warning"><strong>Simulation only.</strong> This view uses local activity data when injected and a deterministic preview fallback. It does not expose private agent thoughts or a real line-by-line generation stream.</div></section>
}

function RoomDesk({ desk, isCto = false }: { desk: { name: string; role: string; status: AgentActivity['status']; task: string; lastActivity: string; accent: string }; isCto?: boolean }) { return <article className={`room-desk ${isCto ? 'cto-desk' : ''}`}><div className="desk-top" style={{ '--desk-accent': desk.accent } as CSSProperties}><div className="desk-monitor"><span>{isCto ? 'CEO' : desk.name.slice(0, 2).toUpperCase()}</span><i /></div><div className="desk-lamp" /><div className="desk-paper" /></div><div className="desk-label"><div className="room-avatar" style={{ background: desk.accent }}>{desk.name.slice(0, 1)}</div><div><strong>{desk.name}</strong><span>{desk.role}</span></div></div><div className="planner-card"><div><span className="planner-kicker">PLANNER / TASK</span><b className={`planner-status ${desk.status.toLowerCase()}`}>{desk.status}</b></div><strong>{desk.task}</strong><small>Last activity · {desk.lastActivity}</small></div></article> }

export default App
