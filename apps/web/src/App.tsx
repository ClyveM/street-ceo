import { VoicePronunciation } from './HandsFreeVoice'
import { clientId } from './clientId'
import { useEffect, useMemo, useRef, useState } from 'react'
import { apiClient, demoProducts, formatMoney, getApiConfig, Product, Sale, saveApiConfig, ShopSummary, Tender, type SaleRequest, type ApiConfig } from './api'
import { requestSale, SaleRequestError } from './saleRequest'
import { VoiceCapture } from './VoiceCapture'
import { isNativeAndroid } from './speechRecognition'
import { AskMuse } from './AskMuse'
import { DEMO_SHOP_ID, migrateKnownDemoConnection } from './muse'
import { StockCatalog } from './StockCatalog'
import { useProductImages } from './useProductImages'
import { SocialUpdate } from './SocialUpdate'
import { RetailControl } from './RetailControl'
import { formatShopWelcome, watchShopWelcome } from './shopDate'
import { SellCheckout } from './SellCheckout'
import { cashAmountCents, readSaleMode, SALE_MODE_KEY, type QuickReceipt, type SaleMode } from './quickSale'
import { RequestHistory } from './RequestHistory'
import { Transactions } from './Transactions'
import { checkShopReachability, localShopGuidance, type ShopReachability } from './shopReachability'
import { DEMO_BUILD_LABEL } from './buildInfo'
import './demo-ux.css'
import './counter-polish.css'

type View = 'today' | 'sell' | 'stock' | 'alerts' | 'transactions' | 'muse' | 'social' | 'profitability' | 'settings' | 'costs' | 'profile'
type Basket = Record<string, number>

function Logo() {
  return <div className="brand-mark" aria-label="Street CEO logo"><img src="/street-ceo-logo.png" alt="Street CEO" /></div>
}

function App() {
  const [connectionNotice] = useState(() => { try { return migrateKnownDemoConnection(localStorage, { baseUrl: import.meta.env.VITE_API_BASE_URL, shopId: import.meta.env.VITE_SHOP_ID }, isNativeAndroid()) } catch { return null } })
  const [view, setView] = useState<View>(() => isNativeAndroid() ? 'sell' : 'today')
  const productImages = useProductImages()
  const [costProductId, setCostProductId] = useState<string | undefined>()
  const [products, setProducts] = useState<Product[]>(demoProducts)
  const [isDemo, setIsDemo] = useState(true)
  const [shopSummary, setShopSummary] = useState<ShopSummary | null>(null)
  const [sales, setSales] = useState<Sale[]>([])
  const [salesError, setSalesError] = useState('')
  const [saleReview, setSaleReview] = useState(false), [salePending, setSalePending] = useState(false)
  const [cashReceived, setCashReceived] = useState(''), [saleUncertain, setSaleUncertain] = useState(false), [manualReceipt, setManualReceipt] = useState<Sale | null>(null)
  const [voiceBusy, setVoiceBusy] = useState(false)
  const voiceRequestActive = useRef(false)
  const connectionProbe = useRef<AbortController | null>(null)
  const [voiceMode, setVoiceMode] = useState<SaleMode>(() => { if (isNativeAndroid()) return 'quick'; try { return readSaleMode(localStorage) } catch { return 'quick' } })
  const saleLock = useRef(false), saleAttempt = useRef<{ fingerprint: string; key: string; payload: SaleRequest; config: ApiConfig } | null>(null)
  const [basket, setBasket] = useState<Basket>({})
  const [tender, setTender] = useState<Tender>('cash')
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [connection, setConnection] = useState<ShopReachability | null>(null), [checkingConnection, setCheckingConnection] = useState(true), [connectionCheck, setConnectionCheck] = useState(0)
  const [welcome, setWelcome] = useState(() => formatShopWelcome(Date.now()))
  const refreshSales = async () => {
    try { const records = await apiClient.listSales(); setSales(records); setSalesError(''); return true }
    catch { setSalesError('Could not load transactions. A failed request does not mean there were no sales.'); return false }
  }

  useEffect(() => {
    const clock = watchShopWelcome(setWelcome)
    window.addEventListener('focus', clock.refresh)
    document.addEventListener('visibilitychange', clock.refresh)
    return () => { clock.stop(); window.removeEventListener('focus', clock.refresh); document.removeEventListener('visibilitychange', clock.refresh) }
  }, [])

  useEffect(() => {
    const load = async () => {
      setIsLoading(true)
      const [result, summary] = await Promise.all([apiClient.listProducts(), apiClient.getSummary(), refreshSales()])
      setProducts(result.products)
      setIsDemo(result.isDemo)
      setShopSummary(summary)
      setIsLoading(false)
    }
    void load()
  }, [])

  useEffect(() => {
    let disposed = false, active: AbortController | null = null
    const check = async () => {
      if (document.hidden || active) return
      if (voiceRequestActive.current) { setCheckingConnection(false); return }
      const controller = new AbortController(); active = controller; connectionProbe.current = controller; setCheckingConnection(true)
      const result = await checkShopReachability(getApiConfig(), controller.signal)
      if (!disposed && !controller.signal.aborted) { setConnection(result); setCheckingConnection(false) }
      if (active === controller) active = null
      if (connectionProbe.current === controller) connectionProbe.current = null
    }
    void check()
    const timer = setInterval(() => { void check() }, 15000), refresh = () => { void check() }
    window.addEventListener('online', refresh); window.addEventListener('offline', refresh); window.addEventListener('focus', refresh); document.addEventListener('visibilitychange', refresh)
    return () => { disposed = true; active?.abort(); clearInterval(timer); window.removeEventListener('online', refresh); window.removeEventListener('offline', refresh); window.removeEventListener('focus', refresh); document.removeEventListener('visibilitychange', refresh) }
  }, [connectionCheck])

  useEffect(() => {
    if (connection?.status !== 'connected') return
    void apiClient.listProducts().then((result) => { if (!result.isDemo) { setProducts(result.products); setIsDemo(false) } }).catch(() => {})
    void refreshSales()
  }, [connection?.status])

  const filteredProducts = useMemo(() => products.filter((product) => product.name.toLowerCase().includes(query.toLowerCase()) || product.sku.toLowerCase().includes(query.toLowerCase())), [products, query])
  const basketItems = products.filter((product) => basket[product.id]).map((product) => ({ ...product, quantity: basket[product.id] }))
  const total = basketItems.reduce((sum, product) => sum + product.unit_price_cents * product.quantity, 0)
  const itemCount = basketItems.reduce((sum, product) => sum + product.quantity, 0)
  const receivedCents = tender === 'cash' ? cashAmountCents(cashReceived) : total
  const paymentError = tender === 'cash' && (receivedCents === null ? 'Enter the cash received using at most two decimal places.' : receivedCents < total ? 'Cash received is below the basket total.' : '')

  const refreshConfirmedSale = async (sale: Sale | QuickReceipt, label: string) => {
    const [summary, history] = await Promise.allSettled([apiClient.getSummary(), refreshSales()])
    if (summary.status === 'fulfilled' && summary.value) setShopSummary(summary.value)
    if (summary.status === 'rejected' || !summary.value || history.status === 'rejected' || !history.value) setNotice({ type: 'success', text: `${label} ${sale.id} recorded. Stock is updated from its receipt; summary or history refresh is unavailable. Do not record this sale again.` })
  }

  const addToBasket = (product: Product) => setBasket((current) => ({ ...current, [product.id]: Math.min(product.stock_qty, (current[product.id] ?? 0) + 1) }))
  const removeFromBasket = (product: Product) => setBasket((current) => { const next = { ...current }; if (next[product.id] > 1) next[product.id] -= 1; else delete next[product.id]; return next })
  const submitSale = async () => {
    if ((!saleUncertain && (!basketItems.length || !saleReview || paymentError)) || saleLock.current || isDemo) return
    saleLock.current = true; setSalePending(true)
    setNotice(null)
    try {
      if (!saleUncertain) {
        const payload: SaleRequest = { lines: basketItems.map(({ id, quantity }) => ({ product_id: id, quantity })), tender, ...(tender === 'cash' && receivedCents !== null ? { amount_received_cents: receivedCents } : {}) }
        const config = getApiConfig(), fingerprint = JSON.stringify({ config, payload })
        if (saleAttempt.current?.fingerprint !== fingerprint) saleAttempt.current = { fingerprint, key: `web-sale-${clientId()}`, payload, config }
      }
      if (!saleAttempt.current) return
      const attempt = saleAttempt.current, sale = await requestSale(attempt.config, attempt.payload, attempt.key)
      setProducts((current) => current.map((product) => sale.stock_after[product.id] === undefined ? product : { ...product, stock_qty: sale.stock_after[product.id] }))
      setBasket({})
      setSaleReview(false); saleAttempt.current = null; setSaleUncertain(false); setCashReceived(''); setManualReceipt(sale)
      setNotice({ type: 'success', text: `Sale saved · ${formatMoney(sale.total_cents)}${sale.change_cents !== undefined ? ` · change ${formatMoney(sale.change_cents)}` : ''}.` })
      void refreshConfirmedSale(sale, 'Sale')
    } catch (failure) { setSaleUncertain((previous) => previous || failure instanceof SaleRequestError && failure.uncertain); setNotice({ type: 'error', text: failure instanceof Error ? failure.message : 'Sale outcome unconfirmed. Check transactions before retrying.' }) }
    finally { saleLock.current = false; setSalePending(false) }
  }
  const refreshCostProducts = async () => {
    const result = await apiClient.listProducts()
    if (result.isDemo) throw new Error('Could not refresh live catalogue.')
    setProducts(result.products)
  }
  const openCosts = (productId?: string) => { setCostProductId(productId); setView('costs') }
  const setVoicePreference = (mode: SaleMode) => { setVoiceMode(mode); try { localStorage.setItem(SALE_MODE_KEY, mode) } catch { setNotice({ type: 'error', text: 'Sale mode applies for this session; this browser could not save the preference.' }) } }
  const confirmedVoiceSale = (receipt: QuickReceipt) => {
    setProducts((current) => current.map((product) => receipt.stock_after[product.id] === undefined ? product : { ...product, stock_qty: receipt.stock_after[product.id] }))
    setNotice({ type: 'success', text: `Sale saved · ${formatMoney(receipt.total_cents)} · change ${formatMoney(receipt.change_cents)}.` })
    void refreshConfirmedSale(receipt, 'Apo sale')
  }
  const reversedVoiceSale = async () => { await refreshCostProducts(); setShopSummary(await apiClient.getSummary()); await refreshSales(); setNotice({ type: 'success', text: 'Voice-sale stock reversal recorded. Payment refund and financial-ledger reversal are not verified.' }) }

  return <div className="app-shell">
    <header className="topbar">
      <button disabled={voiceBusy || salePending || saleUncertain} className="brand brand-button" onClick={() => setView('today')} aria-label="Go to Street CEO home"><Logo /><div><strong>Street CEO</strong><span>Your shop, in control.</span></div></button>
      <button type="button" className={`connection-pill shop-connection-check ${connection?.status === 'connected' ? 'online' : 'offline'}`} disabled={checkingConnection} onClick={() => setConnectionCheck((value) => value + 1)} title="Check readiness and the configured shop from this device"><span className="status-dot" />{connection?.status === 'connected' ? 'Shop connected' : connection ? 'Shop unavailable' : 'Checking shop…'}</button>
    </header>

    <main className="page">
      {(view === 'profile' || view === 'settings') && <section className={`shop-connection-summary ${connection?.status === 'unavailable' ? 'unavailable' : ''}`} aria-label="Shop server connection"><p>Build <strong>{DEMO_BUILD_LABEL}</strong></p><p>Shop server: <code>{connection?.address ?? 'Checking configured address…'}</code></p><p>{connection ? <>Last checked <time dateTime={new Date(connection.checkedAt).toISOString()}>{new Date(connection.checkedAt).toLocaleTimeString()}</time>{checkingConnection ? ' · checking again…' : ' · tap the status above to recheck'}</> : 'Verifying readiness and your shop from this device…'}</p>{connection?.status === 'unavailable' && <><p role="status">{connection.detail}</p><p>{localShopGuidance(connection.address)}</p></>}</section>}
      {view !== 'profile' && view !== 'settings' && connection?.status === 'unavailable' && <details className="counter-connection-alert"><summary>Shop unavailable · connection help</summary><p>{connection.detail}</p><p>{localShopGuidance(connection.address)}</p><p>Server <code>{connection.address}</code> · checked {new Date(connection.checkedAt).toLocaleTimeString()}</p><button type="button" disabled={checkingConnection} onClick={() => setConnectionCheck((value) => value + 1)}>Check again</button></details>}
      {view !== 'sell' && view !== 'profile' && <section className="welcome"><div><p className="eyebrow"><time dateTime={welcome.dateKey} title={welcome.timeZone}>{welcome.date}</time></p><h1>{welcome.greeting}, Tendai.</h1><p className="muted">Here’s how your shop is doing today.</p></div><button type="button" className="avatar profile-avatar" disabled={voiceBusy || salePending || saleUncertain} aria-label="Open Profile" onClick={() => setView('profile')}>T</button></section>}
      {isDemo && <div className="demo-banner"><span>✦</span><span><strong>Demo mode</strong> · Showing starter catalogue data. Connect the API to use live shop data.</span></div>}
      {connectionNotice && view === 'profile' && <div className="notice" role="status">{connectionNotice}</div>}
      {notice && <div className={`notice ${notice.type}`} role="status"><span>{notice.type === 'success' ? '✓' : '!'}</span>{notice.text}<button aria-label="Dismiss message" onClick={() => setNotice(null)}>×</button></div>}

      {view === 'sell' && <VoiceCapture blocked={salePending || saleUncertain} connection={connection} checkingConnection={checkingConnection} onCheckConnection={() => setConnectionCheck((value) => value + 1)} onRequestBusy={(value) => { voiceRequestActive.current = value; if (value) { connectionProbe.current?.abort(); setCheckingConnection(false) } }} mode={voiceMode} onConfirmed={confirmedVoiceSale} onUndo={reversedVoiceSale} onBusy={setVoiceBusy} />}
      {view === 'today' && <><Today summary={shopSummary} onSell={() => setView('sell')} onAlerts={() => setView('alerts')} onTransactions={() => setView('transactions')} /><ToolEntryPoints onMuse={() => setView('muse')} onSocial={() => setView('social')} onProfitability={() => setView('profitability')} onSettings={() => setView('settings')} /></>}
      {view === 'sell' && <SellCheckout products={filteredProducts} query={query} setQuery={setQuery} basketItems={basketItems} total={total} itemCount={itemCount} tender={tender} setTender={setTender} addToBasket={addToBasket} removeFromBasket={removeFromBasket} submitSale={() => { void submitSale() }} isLoading={isLoading} review={saleReview} pending={salePending} uncertain={saleUncertain} received={cashReceived} setReceived={setCashReceived} paymentError={paymentError} receivedCents={receivedCents} receipt={manualReceipt} canPost={!isDemo && connection?.status === 'connected' && !voiceBusy} onReview={() => setSaleReview(true)} onEdit={() => setSaleReview(false)} />}
      {view === 'stock' && <StockCatalog products={products} isDemo={isDemo} images={productImages} onOpenCosts={openCosts} onChanged={refreshCostProducts} />}
      {view === 'costs' && <RetailControl products={products} isDemo={isDemo} initialProductId={costProductId} onBack={() => setView('stock')} onChanged={refreshCostProducts} />}
      {view === 'alerts' && <StockAlerts products={products} onBack={() => setView('today')} onOpenStock={() => setView('stock')} />}
      {view === 'transactions' && <Transactions sales={sales} products={isDemo ? [] : products} error={salesError} onBack={() => setView('today')} />}
      {view === 'muse' && <AskMuse onBack={() => setView('today')} />}
      {view === 'social' && <SocialUpdate products={products} isDemo={isDemo} images={productImages} onBack={() => setView('today')} />}
      {view === 'profitability' && <Profitability summary={shopSummary} onBack={() => setView('today')} />}
      {view === 'profile' && <section className="profile-page"><header><p className="eyebrow">YOUR ACCOUNT</p><h2>Profile</h2></header><VoicePronunciation /><RequestHistory /><button className="settings-link" type="button" disabled={saleUncertain} onClick={() => setView('settings')}>Shop Connection & voice sale mode →</button></section>}
      {view === 'settings' && <ApiSettings onBack={() => setView('today')} mode={voiceMode} onMode={setVoicePreference} />}
    </main>

    <nav className="bottom-nav" aria-label="Main navigation">{([['today', '⌂', 'Today'], ['sell', '+', 'Sell'], ['stock', '▥', 'Stock'], ['profile', '○', 'Profile']] as const).map(([key, icon, label]) => <button disabled={voiceBusy || salePending || saleUncertain} key={key} className={(view === key || (key === 'stock' && view === 'costs')) ? 'active' : ''} onClick={() => { setView(key) }} aria-current={(view === key || (key === 'stock' && view === 'costs')) ? 'page' : undefined}><span className="nav-icon">{icon}</span>{label}{key === 'sell' && itemCount > 0 && <b className="basket-badge">{itemCount}</b>}</button>)}</nav>
  </div>
}

function Today({ summary, onSell, onAlerts, onTransactions }: { summary: ShopSummary | null; onSell: () => void; onAlerts: () => void; onTransactions: () => void }) { const total = summary ? formatMoney(summary.sales_total_cents) : '—'; const change = summary?.sales_change_percent == null ? 'No prior-day comparison' : `↑ ${summary.sales_change_percent}%`; return <><section className="hero-card"><div><span className="card-kicker">TODAY’S SALES</span><strong className="hero-amount">{total}</strong><span className="hero-meta"><span className={summary?.sales_change_percent == null ? '' : 'up'}>{change}</span></span></div><div className="sparkline" aria-label="Live sales summary"><i /><i /><i /><i /><i /><i /><i /></div></section><section className="stat-grid"><button className="stat-card stat-card-button" onClick={onTransactions}><span>SALES</span><strong>{summary?.transaction_count ?? '—'}</strong><small>transactions · view history →</small></button><button className="stat-card stat-card-button" onClick={onAlerts}><span>STOCK ALERTS</span><strong className="orange">{summary?.low_stock_count ?? '—'}</strong><small>need attention · view alerts →</small></button></section><section className="section-head"><div><p className="eyebrow">QUICK ACTION</p><h2>Keep the tills moving.</h2></div></section><button className="primary-action full" onClick={onSell}><span className="action-icon">+</span>Record a sale<span className="arrow">→</span></button><div className="insight-card"><span className="insight-icon">✦</span><div><p className="eyebrow">STREET CEO INSIGHT</p><p>{summary?.insight ?? 'Connect the API to see a live shop insight.'}</p></div></div></> }

function StockAlerts({ products, onBack, onOpenStock }: { products: Product[]; onBack: () => void; onOpenStock: () => void }) { const alerts = products.filter((product) => product.stock_qty < 8); return <section className="tool-placeholder"><button className="back-link" onClick={onBack}>← Back to Today</button><div className="tool-hero profit-tool"><span className="tool-glyph">!</span><p className="eyebrow">STOCK ALERTS</p><h2>{alerts.length} products need attention</h2><p>These products are below the current 8-unit alert threshold.</p></div><section className="alert-list">{alerts.length ? alerts.map((product) => <article className="alert-row" key={product.id}><div className="product-avatar">{product.name.slice(0, 1)}</div><div><strong>{product.name}</strong><span>{product.sku} · reorder before the next rush</span></div><b>{product.stock_qty}<small> left</small></b></article>) : <div className="placeholder"><strong>No stock alerts</strong><span>All products are above the current threshold.</span></div>}</section><button className="primary-action full" onClick={onOpenStock}>Open full stock & invoice upload <span className="arrow">→</span></button></section> }


function ToolEntryPoints({ onMuse, onSocial, onProfitability, onSettings }: { onMuse: () => void; onSocial: () => void; onProfitability: () => void; onSettings: () => void }) { return <section className="tool-entry-section"><div className="section-head"><div><p className="eyebrow">SHOP TOOLS</p><h2>Turn today’s work into momentum.</h2></div></div><div className="tool-entry-grid"><button className="tool-entry muse-tool" onClick={onMuse}><span className="tool-glyph">✦</span><span><strong>Ask Muse</strong><small>Ask about recorded sales and missing cost data</small></span><b>→</b></button><button className="tool-entry social-tool" onClick={onSocial}><span className="tool-glyph">✣</span><span><strong>Facebook Reel</strong><small>Create a product video brief</small></span><b>→</b></button><button className="tool-entry profit-tool" onClick={onProfitability}><span className="tool-glyph">↗</span><span><strong>Profitability Analysis</strong><small>Ask about your sales and costs</small></span><b>→</b></button></div><button className="settings-link" onClick={onSettings}>Shop Connection · connect this browser to Street CEO →</button></section> }

function Profitability({ summary, onBack }: { summary: ShopSummary | null; onBack: () => void }) {
  const [revenue, setRevenue] = useState(summary ? (summary.sales_total_cents / 100).toFixed(2) : '')
  const [cogs, setCogs] = useState('')
  const [expenses, setExpenses] = useState('')
  const [question, setQuestion] = useState('What was my profit this month?')
  const revenueValue = Number(revenue) || 0
  const gross = revenueValue - (Number(cogs) || 0)
  const net = gross - (Number(expenses) || 0)
  const margin = revenueValue > 0 ? (net / revenueValue) * 100 : 0
  return <section className="tool-placeholder"><button className="back-link" onClick={onBack}>← Back to Today</button><div className="tool-hero profit-tool"><span className="tool-glyph">↗</span><p className="eyebrow">ASK MUSE</p><h2>Profitability Analysis</h2><p>Ask a question, then give Muse the month’s sales, cost of stock, and expenses.</p></div><div className="analysis-card"><label>Question<input value={question} onChange={(event) => setQuestion(event.target.value)} /></label><div className="analysis-fields"><label>Sales / revenue<input inputMode="decimal" value={revenue} onChange={(event) => setRevenue(event.target.value)} placeholder="0.00" /></label><label>Stock cost / COGS<input inputMode="decimal" value={cogs} onChange={(event) => setCogs(event.target.value)} placeholder="0.00" /></label><label>Other expenses<input inputMode="decimal" value={expenses} onChange={(event) => setExpenses(event.target.value)} placeholder="0.00" /></label></div><button className="primary-action full" onClick={() => undefined}>Analyse this month <span className="arrow">→</span></button><div className="analysis-result"><p className="eyebrow">TRANSPARENT SUMMARY</p><div><span>Gross profit</span><strong>{formatMoney(Math.round(gross * 100))}</strong></div><div><span>Net profit</span><strong>{formatMoney(Math.round(net * 100))}</strong></div><div><span>Net margin</span><strong>{margin.toFixed(1)}%</strong></div></div><p className="muted">This calculation uses the inputs above. Full Muse recommendations will be connected when the finance API supplies monthly COGS and expense records.</p></div></section>
}

function ApiSettings({ onBack, mode, onMode }: { onBack: () => void; mode: SaleMode; onMode: (mode: SaleMode) => void }) {
  const current = getApiConfig()
  const [baseUrl, setBaseUrl] = useState(current.baseUrl)
  const [shopId, setShopId] = useState(current.shopId)
  const [saveError, setSaveError] = useState('')
  const save = () => { try { saveApiConfig({ baseUrl, shopId }); window.location.reload() } catch (error) { setSaveError(error instanceof Error ? error.message : 'Could not save connection.') } }
  return <section className="tool-placeholder"><button className="back-link" onClick={onBack}>← Back to Today</button><div className="tool-hero social-tool"><span className="tool-glyph">⚙</span><p className="eyebrow">SHOP CONNECTION</p><h2>Connect Street CEO</h2><p>This connects the browser to your Street CEO backend. It is not the Muse/Meta AI setup.</p></div><div className="analysis-card"><label>Voice sale mode<select value={mode} onChange={(event) => onMode(event.target.value as SaleMode)}><option value="quick">Quick Sale · Napo ends a clear basket (default)</option><option value="review">Review · confirm the basket manually</option></select></label><p>Quick Sale asks for missing payment details and exceptions. Speech needs supported microphone/audio access; typed commands use the same verified sale boundary.</p><label>Street CEO API base URL<input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} placeholder="http://localhost:8000" /></label><p className="muted">Enter the backend root without /api/v1. A phone needs the computer’s reachable network address.</p>{saveError && <p role="alert">{saveError}</p>}<label>Shop ID<input value={shopId} onChange={(event) => setShopId(event.target.value)} /></label><p className="muted">Use your shop’s non-zero UUID. The confirmed local demo ID is {DEMO_SHOP_ID}.</p><button className="back-link" type="button" onClick={() => { setShopId(DEMO_SHOP_ID); setSaveError('') }}>Use confirmed local demo shop ID</button><button className="primary-action full" onClick={save}>Save connection <span className="arrow">→</span></button><p className="muted">AI setup is managed securely in the Street CEO backend. You do not need to enter it here.</p></div></section>
}

export default App
