import { clientId } from './clientId'
import { useEffect, useRef, useState } from 'react'
import { costsApi, type Product } from './api'
import { canConfirmInvoice, moneyToCents, type InvoiceConfirmation, type InvoiceRecord } from './costs'

type DraftLine = { key: string; description: string; sku: string; quantity: string; total: string; productId: string }
const newLine = (product?: Product): DraftLine => ({ key: clientId(), description: product?.name ?? '', sku: product?.sku ?? '', quantity: '', total: '', productId: product?.id ?? '' })
const costText = (value: number | null) => value === null ? 'Not reviewed yet' : (value / 1000000).toFixed(6)

export function Invoices({ products, disabled, initialProductId, onProductsChanged }: { products: Product[]; disabled: boolean; initialProductId?: string; onProductsChanged: () => Promise<void> }) {
  const [history, setHistory] = useState<InvoiceRecord[] | null>(null)
  const [historyError, setHistoryError] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [invoice, setInvoice] = useState<InvoiceRecord | null>(null)
  const [lines, setLines] = useState<DraftLine[]>([])
  const [dirty, setDirty] = useState(false)
  const [acknowledged, setAcknowledged] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [confirmation, setConfirmation] = useState<InvoiceConfirmation | null>(null)
  const lock = useRef(false)
  const reload = async () => { try { setHistory(await costsApi.listInvoices()); setHistoryError('') } catch (failure) { setHistoryError(failure instanceof Error ? failure.message : 'Could not load invoices.') } }
  useEffect(() => { void reload() }, [])
  const open = (item: InvoiceRecord) => {
    setInvoice(item); setConfirmation(null); setAcknowledged(false); setDirty(false); setError('')
    setLines(item.lines.length ? item.lines.map((line) => ({ key: line.id, description: line.description, sku: line.sku ?? '', quantity: String(line.quantity), total: (line.line_total_cents / 100).toFixed(2), productId: line.matched_product_id ?? '' })) : [newLine(products.find((product) => product.id === initialProductId))])
  }
  const perform = async (action: () => Promise<void>, mutation = true) => {
    if (lock.current || (mutation && disabled)) return
    lock.current = true; setBusy(true); setError('')
    try { await action() } catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not complete this invoice step.') }
    finally { lock.current = false; setBusy(false) }
  }
  const upload = () => perform(async () => { if (!file) throw new Error('Choose an invoice file first.'); open(await costsApi.uploadInvoice(file)); await reload() })
  const review = () => perform(async () => {
    if (!invoice) return
    const payload = { source: 'manual_review' as const, evidence_ref: `invoice:${invoice.id}`, lines: lines.map((line) => ({ description: line.description.trim(), sku: line.sku.trim() || null, product_id: line.productId || null, quantity: Number(line.quantity), line_total_cents: moneyToCents(line.total, true) })) }
    open(await costsApi.reviewInvoice(invoice.id, payload)); await reload()
  })
  const confirm = () => perform(async () => {
    if (!invoice || !canConfirmInvoice(invoice, dirty) || !acknowledged) return
    const result = await costsApi.confirmInvoice(invoice.id)
    setConfirmation(result); setInvoice({ ...invoice, extraction_status: 'confirmed', confirmed_at: result.confirmed_at }); setAcknowledged(false)
    await reload()
    try { await onProductsChanged() } catch { setError('Invoice confirmation was received, but catalogue refresh failed. Reload Stock before relying on quantities or costs.') }
  })
  const updateLine = (key: string, patch: Partial<DraftLine>) => { setLines((items) => items.map((line) => line.key === key ? { ...line, ...patch } : line)); setDirty(true); setAcknowledged(false) }
  const editable = invoice && !['confirmed', 'rejected', 'pending'].includes(invoice.extraction_status)
  return <section className="invoice-workflow"><h2>Supplier invoices</h2><p>Upload → review lines → match products → confirm receipt and costs.</p>
    <section className="cost-card"><h3>1. Upload a PDF or image</h3><label>Invoice file<input type="file" accept="application/pdf,image/jpeg,image/png,image/webp" disabled={busy} onChange={(event) => { setFile(event.target.files?.[0] ?? null); setError('') }} /></label><p>PDF, JPEG, PNG, or WebP · up to 10 MiB. {file ? `Selected: ${file.name}` : 'No file selected.'}</p><button className="primary-action" type="button" disabled={!file || busy || disabled} onClick={() => { void upload() }}>{busy ? 'Please wait…' : 'Upload for review'}</button><p>No stock or cost changes occur at upload. Current storage is temporary and resets with the API.</p></section>
    <section className="cost-card"><div className="cost-heading"><h3>Saved invoices</h3><button type="button" disabled={busy} onClick={() => { void reload() }}>Refresh invoices</button></div>{historyError && <p className="cost-error" role="alert">{historyError}</p>}{history === null && !historyError && <p role="status">Loading invoices…</p>}{history?.length === 0 && !historyError && <p>No invoices returned by the connected shop.</p>}<ul className="cost-history">{history?.map((item) => <li key={item.id}><button type="button" disabled={busy} onClick={() => open(item)}>{item.filename}<small>{item.extraction_status.replace(/_/g, ' ')} · {new Date(item.uploaded_at).toLocaleString()}</small></button></li>)}</ul></section>
    {invoice && <section className="cost-card"><h3>2. Review {invoice.filename}</h3><p>Invoice {invoice.id} · <strong>{invoice.extraction_status.replace(/_/g, ' ')}</strong></p><p>{invoice.extraction_source === 'ocr_provider' ? 'Provider-supplied lines still need your review and explicit matches.' : 'No OCR results are claimed. Enter the invoice lines manually and check the original document.'}</p>{invoice.extraction_status === 'pending' && <p role="status">Extraction is pending. Refresh this invoice to check for actual results.</p>}{invoice.warnings.length > 0 && <ul>{invoice.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>}
      <button type="button" disabled={busy} onClick={() => { void perform(async () => open(await costsApi.getInvoice(invoice.id)), false) }}>Reload this invoice</button>
      <div className="invoice-lines">{lines.map((line, index) => {
        const reviewed = !dirty ? invoice.lines[index] : undefined
        return <fieldset key={line.key} disabled={busy || !editable}><legend>Line {index + 1}</legend><label>Description<input value={line.description} maxLength={240} onChange={(event) => updateLine(line.key, { description: event.target.value })} /></label><div className="cost-fields"><label>SKU (optional)<input value={line.sku} maxLength={64} onChange={(event) => updateLine(line.key, { sku: event.target.value })} /></label><label>Base units received<input type="number" min="1" max="1000000" step="1" value={line.quantity} onChange={(event) => updateLine(line.key, { quantity: event.target.value })} /></label><label>Line total (shop currency)<input inputMode="decimal" value={line.total} onChange={(event) => updateLine(line.key, { total: event.target.value })} /></label></div><label>Explicit product match<select value={line.productId} onChange={(event) => updateLine(line.key, { productId: event.target.value })}><option value="">Not matched</option>{products.map((product) => <option key={product.id} value={product.id}>{product.name} · {product.sku}</option>)}</select></label>
          {reviewed?.suggested_product_id && !reviewed.matched_product_id && <p>Server suggestion: {products.find((product) => product.id === reviewed.suggested_product_id)?.name ?? reviewed.suggested_product_id}. Choose the product explicitly above to accept it.</p>}
          <p>Reviewed unit cost: <strong>{reviewed ? costText(reviewed.calculated_unit_cost_micros) : 'Save review to calculate'}</strong> · {reviewed ? reviewed.match_status : 'Unsaved manual line'}</p><button type="button" onClick={() => { setLines((items) => items.filter((item) => item.key !== line.key)); setDirty(true); setAcknowledged(false) }}>Remove line</button></fieldset>
      })}</div>
      {editable && <div className="cost-actions"><button type="button" disabled={busy || lines.length >= 200} onClick={() => { setLines((items) => [...items, newLine()]); setDirty(true); setAcknowledged(false) }}>Add manual line</button><button className="primary-action" type="button" disabled={busy || disabled || !lines.length} onClick={() => { void review() }}>Save lines for review</button></div>}
      {editable && <section className="invoice-confirm"><h3>3. Confirm receipt and costs</h3><p>Every line must have an explicit accepted product match. Saving a review alone does not change stock.</p><p><strong>Confirmation adds the received units to stock and updates weighted-average product costs.</strong> It is not a cost-only correction for stock already received.</p><label className="cost-check"><input type="checkbox" checked={acknowledged} disabled={busy || !canConfirmInvoice(invoice, dirty)} onChange={(event) => setAcknowledged(event.target.checked)} />I checked the original invoice, base-unit quantities, amounts, and every product match.</label><button className="primary-action" type="button" disabled={disabled || busy || !acknowledged || !canConfirmInvoice(invoice, dirty)} onClick={() => { void confirm() }}>Confirm receipt and costs</button></section>}
    </section>}
    {confirmation && <section className="cost-card" role="status"><h3>Invoice confirmed by the backend</h3><p>{confirmation.stock_units_added} base units added · {confirmation.cost_updates} cost updates.</p><ul>{confirmation.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul><p>Invoice receipt: {confirmation.invoice_id}</p></section>}
    {error && <p className="cost-error" role="alert">{error}</p>}
  </section>
}
