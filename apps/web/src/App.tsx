import { SampleHistory } from './SampleHistory'
import { ShopIcon, type ShopIconName } from './ShopIcon'
import { PaperSales } from './DailySheetPage'
import { StockCountPage } from './StockCountPage'
import { Reports } from './Reports'
import { VoicePronunciation } from './HandsFreeVoice'
import { clientId } from './clientId'
import { useEffect, useMemo, useRef, useState } from 'react'
import { apiClient, demoProducts, formatMoney, getApiConfig, getLiveShopId, Product, Sale, saveApiConfig, ShopSummary, Tender, type SaleRequest, type ApiConfig } from './api'
import { requestSale, SaleRequestError } from './saleRequest'
import { VoiceCapture } from './VoiceCapture'
import { isNativeAndroid } from './speechRecognition'
import { AskMuse } from './AskMuse'
import { SAMPLE_SHOP_ID, migrateKnownDemoConnection } from './muse'
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


type View = 'profit-report' | 'today' | 'sell' | 'stock' | 'alerts' | 'transactions' | 'muse' | 'social' | 'profitability' | 'settings' | 'costs' | 'profile' | 'reports' | 'stock-count' | 'paper-sales'
type Basket = Record<string, number>

function Logo() {
  return <div className="brand-mark" aria-label="Street CEO logo"><img src="/street-ceo-logo.png" alt="Street CEO" /></div>
}

function App() {
  const [connectionNotice] = useState(() => { try { return migrateKnownDemoConnection(localStorage, { baseUrl: import.meta.env.VITE_API_BASE_URL, shopId: import.meta.env.VITE_SHOP_ID }, isNativeAndroid()) } catch { return null } })
  const [activeConnection] = useState(getApiConfig)
  const [view, setView] = useState<View>(() => isNativeAndroid() ? 'sell' : 'today')
  const productImages = useProductImages()
  const [costProductId, setCostProductId] = useState<string | undefined>()
  const [products, setProducts] = useState<Product[]>(demoProducts)
  const [isDemo, setIsDemo] = useState(true)
  const [shopSummary, setShopSummary] = useState<ShopSummary | null>(null)
  const [sales, setSales] = useState<Sale[]>([])
  const [salesError, setSalesError] = useState('')
  const [salesLoading,setSalesLoading]=useState(true)
  const salesGeneration=useRef(0)
  const summaryGeneration = useRef(0)
  const [saleReview, setSaleReview] = useState(false), [salePending, setSalePending] = useState(false)
  const [cashReceived, setCashReceived] = useState(''), [saleUncertain, setSaleUncertain] = useState(false), [manualReceipt, setManualReceipt] = useState<Sale | null>(null)
  const [voiceBusy, setVoiceBusy] = useState(false)
  const [countBlocking,setCountBlocking]=useState(false)
  const [stockBlocking,setStockBlocking]=useState(false)
  const [paperBlocking,setPaperBlocking]=useState(false)
  const openStockCount=()=>{setView('stock-count')}
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
  const refreshSummary = async (clearOnFailure = false) => {
    const id = ++summaryGeneration.current
    const summary = await apiClient.getSummary()
    if (id === summaryGeneration.current && (summary || clearOnFailure)) setShopSummary(summary)
    return !!summary
  }
  const refreshSales = async () => {
    const id=++salesGeneration.current;setSalesLoading(true)
    try { const records = await apiClient.listSales(); if(id===salesGeneration.current){setSales(records);setSalesError('')} return true }
    catch { if(id===salesGeneration.current)setSalesError('Could not load transactions. A failed request does not mean there were no sales.'); return false }
    finally { if(id===salesGeneration.current)setSalesLoading(false) }
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
      const [result] = await Promise.all([apiClient.listProducts(), refreshSummary(true), refreshSales()])
      setProducts(result.products)
      setIsDemo(result.isDemo)
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
    const [summary, history] = await Promise.allSettled([refreshSummary(), refreshSales()])
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
  const refreshSampleShop = async () => {
    const current = getApiConfig()
    if (activeConnection.shopId.toLowerCase() !== SAMPLE_SHOP_ID ||
      current.shopId !== activeConnection.shopId || current.baseUrl !== activeConnection.baseUrl) return true
    const [summary, history, products] = await Promise.allSettled([
      refreshSummary(), refreshSales(), refreshCostProducts(),
    ])
    return summary.status === 'fulfilled' && summary.value &&
      history.status === 'fulfilled' && history.value && products.status === 'fulfilled'
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
      <button disabled={voiceBusy || salePending || saleUncertain || countBlocking || stockBlocking || paperBlocking} className="brand brand-button" onClick={() => setView('today')} aria-label="Go to Street CEO home"><Logo /><div><strong>Street CEO</strong><span>Your shop, in control.</span></div></button>
      <button type="button" className={`connection-pill shop-connection-check ${connection?.status === 'connected' ? 'online' : 'offline'}`} disabled={checkingConnection} onClick={() => setConnectionCheck((value) => value + 1)} title="Check readiness and the configured shop from this device"><span className="status-dot" />{connection?.status === 'connected' ? 'Shop connected' : connection ? 'Shop unavailable' : 'Checking shop…'}<ShopIcon name="wifi" /></button>
    </header>

    <main className={`page view-${view}`}>
      {(view === 'profile' || view === 'settings') && <details className={`shop-connection-summary ${connection?.status === 'unavailable' ? 'unavailable' : ''}`} aria-label="Shop server connection"><summary>Shop connection & build</summary><p>Build <strong>{DEMO_BUILD_LABEL}</strong></p><p>Shop server: <code>{connection?.address ?? 'Checking configured address…'}</code></p><p>{connection ? <>Last checked <time dateTime={new Date(connection.checkedAt).toISOString()}>{new Date(connection.checkedAt).toLocaleTimeString()}</time>{checkingConnection ? ' · checking again…' : ' · tap the status above to recheck'}</> : 'Verifying readiness and your shop from this device…'}</p>{connection?.status === 'unavailable' && <><p role="status">{connection.detail}</p><p>{localShopGuidance(connection.address)}</p></>}</details>}
      {view !== 'profile' && view !== 'settings' && connection?.status === 'unavailable' && <details className="counter-connection-alert"><summary>Shop unavailable · connection help</summary><p>{connection.detail}</p><p>{localShopGuidance(connection.address)}</p><p>Server <code>{connection.address}</code> · checked {new Date(connection.checkedAt).toLocaleTimeString()}</p><button type="button" disabled={checkingConnection} onClick={() => setConnectionCheck((value) => value + 1)}>Check again</button></details>}
      {view !== 'sell' && view !== 'profile' && view !== 'reports' && view !== 'stock-count' && view !== 'stock' && view !== 'transactions' && view !== 'paper-sales' && <section className="welcome"><div><p className="eyebrow"><time dateTime={welcome.dateKey} title={welcome.timeZone}>{welcome.date}</time></p><h1>{welcome.greeting}, Tendai.</h1><p className="muted">Here’s how your shop is doing today.</p></div><button type="button" className="avatar profile-avatar" disabled={voiceBusy || salePending || saleUncertain || countBlocking || stockBlocking || paperBlocking} aria-label="Open Profile" onClick={() => setView('profile')}>T</button></section>}
      {activeConnection.shopId.toLowerCase() === SAMPLE_SHOP_ID && <div className="demo-banner"><strong>Sample shop</strong> · Synthetic sales history</div>}
      {isDemo && <div className="demo-banner"><span>✦</span><span><strong>Demo mode</strong> · Showing starter catalogue data. Connect the API to use live shop data.</span></div>}
      {connectionNotice && view === 'profile' && <div className="notice" role="status">{connectionNotice}</div>}
      {notice && <div className={`notice ${notice.type}`} role="status"><span>{notice.type === 'success' ? '✓' : '!'}</span>{notice.text}<button aria-label="Dismiss message" onClick={() => setNotice(null)}>×</button></div>}

      {view === 'sell' && <VoiceCapture photos={productImages.photos} manualBasket={itemCount>0} onStockCount={openStockCount} blocked={salePending || saleUncertain} connection={connection} checkingConnection={checkingConnection} onCheckConnection={() => setConnectionCheck((value) => value + 1)} onRequestBusy={(value) => { voiceRequestActive.current = value; if (value) { connectionProbe.current?.abort(); setCheckingConnection(false) } }} mode={voiceMode} onConfirmed={confirmedVoiceSale} onUndo={reversedVoiceSale} onBusy={setVoiceBusy} />}
      {view === 'today' && <><Today summary={shopSummary} onSell={() => setView('sell')} onAlerts={() => setView('alerts')} onTransactions={() => setView('transactions')} /><ToolEntryPoints onMuse={() => setView('muse')} onSocial={() => setView('social')} onProfitability={() => setView('profitability')} onSettings={() => setView('settings')} /></>}
      {view==='sell'&&<section className="paper-entry"><div><strong>Have a handwritten daily list?</strong><p>Import combined sales as a reviewed daily summary.</p></div><button disabled={voiceBusy||salePending||saleUncertain||itemCount>0} onClick={()=>setView('paper-sales')}>Upload daily sales sheet</button></section>}
      {view === 'sell' && <SellCheckout photos={productImages.photos} products={filteredProducts} query={query} setQuery={setQuery} basketItems={basketItems} total={total} itemCount={itemCount} tender={tender} setTender={setTender} addToBasket={addToBasket} removeFromBasket={removeFromBasket} submitSale={() => { void submitSale() }} isLoading={isLoading} review={saleReview} pending={salePending} uncertain={saleUncertain} received={cashReceived} setReceived={setCashReceived} paymentError={paymentError} receivedCents={receivedCents} receipt={manualReceipt} canPost={!isDemo && connection?.status === 'connected' && !voiceBusy} onReview={() => setSaleReview(true)} onEdit={() => setSaleReview(false)} />}
      {view === 'stock' && <StockCatalog currency={connection?.status==='connected'?connection.currency:undefined} onBlockingChange={setStockBlocking} products={products} isDemo={isDemo} images={productImages} onOpenCount={openStockCount} onOpenCosts={openCosts} onChanged={refreshCostProducts} />}
      {view === 'costs' && <RetailControl products={products} isDemo={isDemo} initialProductId={costProductId} onStockCount={openStockCount} onBack={() => setView('stock')} onChanged={refreshCostProducts} />}
      {view === 'alerts' && <StockAlerts products={products} onBack={() => setView('today')} onOpenStock={() => setView('stock')} />}
      {view==='paper-sales'&&<PaperSales products={products} isDemo={isDemo} currency={connection?.status==='connected'?connection.currency:undefined} onBlockingChange={setPaperBlocking} onBack={()=>setView('sell')} onChanged={async()=>{await refreshCostProducts();setShopSummary(await apiClient.getSummary());if(!await refreshSales())throw new Error('History refresh unavailable.')}}/>}
      {view === 'stock-count' && <StockCountPage products={products} isDemo={isDemo} onBack={()=>setView('stock')} onChanged={refreshCostProducts} onBlockingChange={setCountBlocking}/>}
      {view === 'reports' && <Reports onBack={()=>setView('today')} onCount={openStockCount}/>}
      {view === 'transactions' && <Transactions onOpenDaily={() => setView('paper-sales')} currency={connection?.status==='connected'?connection.currency:undefined} shopId={getApiConfig().shopId} loading={salesLoading} onRefresh={refreshSales} sales={sales} products={isDemo ? [] : products} error={salesError} onBack={() => setView('today')} />}
      {view === 'muse' && <AskMuse config={activeConnection} onBack={() => setView('today')} />}
      {view === 'social' && <SocialUpdate products={products} isDemo={isDemo} images={productImages} onBack={() => setView('today')} />}
      {view === 'profit-report' && <Reports initialView="profit" onBack={() => setView('profitability')} onCount={openStockCount} />}
      {view === 'profitability' && <Profitability onBack={() => setView('today')} onAnalyse={() => setView('profit-report')} />}
      {view === 'profile' && <section className="profile-page"><header><p className="eyebrow">YOUR ACCOUNT</p><h2>Profile</h2></header><VoicePronunciation /><SampleHistory config={activeConnection} onChanged={refreshSampleShop} switchDisabled={saleUncertain || salePending || voiceBusy || countBlocking || stockBlocking || paperBlocking} /><details className="profile-investigations"><summary>Activity & request history</summary><RequestHistory /></details><button className="settings-link" type="button" disabled={saleUncertain} onClick={() => setView('settings')}>Shop Connection & voice sale mode →</button></section>}
      {view === 'settings' && <ApiSettings switchDisabled={saleUncertain || salePending || voiceBusy || countBlocking || stockBlocking || paperBlocking} onBack={() => setView('today')} mode={voiceMode} onMode={setVoicePreference} />}
    </main>

    <nav className="bottom-nav" aria-label="Main navigation">{([['today', '⌂', 'Today'], ['sell', '+', 'Sell'], ['stock', '▥', 'Stock'], ['reports', '▤', 'Reports'], ['profile', '○', 'Profile']] as const).map(([key, , label]) => <button disabled={voiceBusy || salePending || saleUncertain || countBlocking || stockBlocking || paperBlocking} key={key} className={(view === key || (key==='sell'&&view==='paper-sales') || (key === 'stock' && (view === 'costs' || view === 'stock-count'))) ? 'active' : ''} onClick={() => { setView(key) }} aria-current={(view === key || (key==='sell'&&view==='paper-sales') || (key === 'stock' && (view === 'costs' || view === 'stock-count'))) ? 'page' : undefined}><span className="nav-icon"><ShopIcon name={key as ShopIconName} /></span>{label}{key === 'sell' && itemCount > 0 && <b className="basket-badge">{itemCount}</b>}</button>)}</nav>
  </div>
}

function Today({ summary, onSell, onAlerts, onTransactions }: { summary: ShopSummary | null; onSell: () => void; onAlerts: () => void; onTransactions: () => void }) {
  const total = summary ? formatMoney(summary.sales_total_cents) : '—'
  const comparison = summary?.sales_change_percent
  return <>
    <section className="hero-card today-sales"><div><span className="card-kicker">TODAY’S SALES</span><strong className="hero-amount">{total}</strong><span className="hero-meta">{comparison == null ? 'Your recorded shop sales' : `${comparison > 0 ? '+' : ''}${comparison}% vs yesterday`}</span></div><div className="today-sales-emblem" aria-hidden="true"><ShopIcon name="receipt" /></div></section>
    <section className="stat-grid"><button className="stat-card stat-card-button" onClick={onTransactions}><span className="stat-emblem"><ShopIcon name="receipt" /></span><span>CUSTOMER SALES</span><strong>{summary?.transaction_count ?? '—'}</strong><small>receipts · view history →{(summary?.daily_summary_count??0)>0&&<><br/>{summary?.daily_summary_count} daily {summary?.daily_summary_count===1?'summary':'summaries'} counted separately</>}</small></button><button className="stat-card stat-card-button" onClick={onAlerts}><span className="stat-emblem amber"><ShopIcon name="stock" /></span><span>STOCK ALERTS</span><strong className="orange">{summary?.low_stock_count ?? '—'}</strong><small>need attention · view alerts →</small></button></section>
    <div className="insight-card"><span className="insight-icon"><ShopIcon name="spark" /></span><div><p className="eyebrow">AT YOUR COUNTER</p><p>{summary?.insight ?? 'Connect the API to see a live shop insight.'}</p></div></div>
    <button className="today-apo" onClick={onSell}><span className="today-mic"><ShopIcon name="mic" /></span><span><strong>Let’s make a sale.</strong><small>Open Sell for hands-free Apo or a typed sale.</small></span><span aria-hidden="true">→</span></button>
  </>
}

function StockAlerts({ products, onBack, onOpenStock }: { products: Product[]; onBack: () => void; onOpenStock: () => void }) { const alerts = products.filter((product) => product.stock_qty < 8); return <section className="tool-placeholder"><button className="back-link" onClick={onBack}>← Back to Today</button><div className="tool-hero profit-tool"><span className="tool-glyph">!</span><p className="eyebrow">STOCK ALERTS</p><h2>{alerts.length} products need attention</h2><p>These products are below the current 8-unit alert threshold.</p></div><section className="alert-list">{alerts.length ? alerts.map((product) => <article className="alert-row" key={product.id}><div className="product-avatar">{product.name.slice(0, 1)}</div><div><strong>{product.name}</strong><span>{product.sku} · reorder before the next rush</span></div><b>{product.stock_qty}<small> left</small></b></article>) : <div className="placeholder"><strong>No stock alerts</strong><span>All products are above the current threshold.</span></div>}</section><button className="primary-action full" onClick={onOpenStock}>Open full stock & invoice upload <span className="arrow">→</span></button></section> }


function ToolEntryPoints({ onMuse, onSocial, onProfitability, onSettings }: { onMuse: () => void; onSocial: () => void; onProfitability: () => void; onSettings: () => void }) { return <section className="tool-entry-section"><div className="section-head"><div><p className="eyebrow">SHOP TOOLS</p><h2>Your shop tools</h2></div></div><div className="tool-entry-grid"><button className="tool-entry muse-tool" onClick={onMuse}><span className="tool-glyph">✦</span><span><strong>Ask Muse</strong><small>Ask about recorded sales and missing cost data</small></span><b>→</b></button><button className="tool-entry social-tool" onClick={onSocial}><span className="tool-glyph">✣</span><span><strong>Facebook Reel</strong><small>Create a product video brief</small></span><b>→</b></button><button className="tool-entry profit-tool" onClick={onProfitability}><span className="tool-glyph">↗</span><span><strong>Profitability Analysis</strong><small>Ask about your sales and costs</small></span><b>→</b></button></div><button className="settings-link" onClick={onSettings}>Shop Connection · connect this browser to Street CEO →</button></section> }

function Profitability({ onBack, onAnalyse }: { onBack: () => void; onAnalyse: () => void }) {
  return <section className="tool-placeholder">
    <button className="back-link" onClick={onBack}>← Back to Today</button>
    <div className="tool-hero profit-tool">
      <span className="tool-glyph">↗</span>
      <h2>Profitability Analysis</h2>
      <p>Review this month’s recorded sales, product costs and gross profit before expenses.</p>
    </div>
    <button className="primary-action full" onClick={onAnalyse}>Analyse this month <span className="arrow">→</span></button>
  </section>
}

function ApiSettings({ onBack, mode, onMode, switchDisabled }: { switchDisabled: boolean; onBack: () => void; mode: SaleMode; onMode: (mode: SaleMode) => void }) {
  const current = getApiConfig()
  const [baseUrl, setBaseUrl] = useState(current.baseUrl)
  const [shopId, setShopId] = useState(current.shopId)
  const [saveError, setSaveError] = useState('')
  const save = (selectedId: string) => { if (switchDisabled) return; try { saveApiConfig({ baseUrl, shopId: selectedId }); window.location.reload() } catch (error) { setSaveError(error instanceof Error ? error.message : 'Could not save connection.') } }
  return <section className="tool-placeholder">
    <button className="back-link" onClick={onBack}>← Back to Today</button>
    <div className="tool-hero social-tool"><span className="tool-glyph">⚙</span><h2>Shop connection</h2><p>Choose the server and shop this device connects to.</p></div>
    <div className="analysis-card">
      <label>Server address<input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} placeholder="http://localhost:8001" /></label>
      <p className="muted">Enter the server root without /api/v1. On a phone, use the computer’s reachable network address.</p>
      <label>Shop ID<input value={shopId} onChange={(event) => setShopId(event.target.value)} /></label>
      <p className="muted">Enter a shop ID and save, or open a shop directly using the server address above.</p>
      <div className="shop-connection-choices">
        <button type="button" disabled={switchDisabled} onClick={() => save(getLiveShopId(baseUrl))}>Open live shop</button>
        <button type="button" disabled={switchDisabled} onClick={() => save(SAMPLE_SHOP_ID)}>Open sample shop</button>
      </div>
      {saveError && <p role="alert">{saveError}</p>}
      {switchDisabled && <p role="status">Finish the current shop activity before changing the connection.</p>}
      <button className="primary-action full" disabled={switchDisabled} onClick={() => save(shopId)}>Save connection <span className="arrow">→</span></button>
    </div>
    <div className="analysis-card">
      <h3>Voice sales</h3>
      <label>Voice sale mode<select value={mode} onChange={(event) => onMode(event.target.value as SaleMode)}><option value="quick">Quick Sale · Napo ends a clear basket (default)</option><option value="review">Review · confirm the basket manually</option></select></label>
      <p>Quick Sale asks for missing payment details and exceptions. Speech needs microphone access. Typed commands use the same sale checks.</p>
    </div>
  </section>
}

export default App
