import { useRef, useState } from 'react'
import { retailApi, type Product } from './api'
import { validateStockTake, type StockTakeInput, type StockTakeRecord, type StockTakeResult } from './retailContracts'

export function StockTake({ products, disabled, onChanged }: { products: Product[]; disabled: boolean; onChanged: () => Promise<void> }) {
  const [mode, setMode] = useState<StockTakeInput['mode']>('on_demand'), [date, setDate] = useState(''), [actor, setActor] = useState(''), [notes, setNotes] = useState('')
  const [counts, setCounts] = useState<Record<string, string>>({}), [draft, setDraft] = useState<StockTakeRecord | null>(null)
  const [busy, setBusy] = useState(false), [error, setError] = useState('')
  const [ack, setAck] = useState(false), [uncertain, setUncertain] = useState(false), [result, setResult] = useState<StockTakeResult | null>(null)
  const lock = useRef(false)
  const save = async () => {
    if (disabled || lock.current) return
    lock.current = true; setBusy(true); setError('')
    try {
      const lines = products.filter((product) => counts[product.id]?.trim()).map((product) => {
        const value = counts[product.id].trim()
        if (!/^\d+$/.test(value) || !Number.isSafeInteger(Number(value))) throw new Error('Counts must be whole non-negative base units. Leave uncounted products blank.')
        return { product_id: product.id, counted_qty: Number(value) }
      })
      setDraft(await retailApi.createStockTake(validateStockTake({ mode, count_date: date, actor: actor.trim(), notes: notes.trim(), lines }))); setAck(false); setUncertain(false)
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not save stock count.') }
    finally { lock.current = false; setBusy(false) }
  }
  const act = async (action: () => Promise<void>) => {
    if (disabled || lock.current) return
    lock.current = true; setBusy(true); setError('')
    try { await action() } catch (failure) { setError(failure instanceof Error ? failure.message : 'Count operation unconfirmed. Reload before retrying.') }
    finally { lock.current = false; setBusy(false) }
  }
  const confirm = () => act(async () => {
    if (!draft || !ack || uncertain) return
    try { setResult(await retailApi.confirmStockTake(draft)); setDraft({ ...draft, status: 'confirmed' }); setAck(false) } catch (failure) { setUncertain(true); throw failure }
    try { await onChanged() } catch { setError('Count confirmed, but catalogue refresh failed. Reload Stock before relying on quantities.') }
  })
  return <section><h2>Count your stock</h2><p>Use a monthly or on-demand count. Enter the units physically counted; blank means not counted, never zero.</p>{!draft ? <form onSubmit={(event) => { event.preventDefault(); void save() }}><fieldset className="retail-form" disabled={disabled || busy}><legend>1. Count details</legend><div className="cost-fields"><label>Count type<select value={mode} onChange={(event) => setMode(event.target.value as typeof mode)}><option value="on_demand">On-demand</option><option value="monthly">Monthly</option></select></label><label>Count date<input type="date" value={date} onChange={(event) => setDate(event.target.value)} required /></label><label>Counted by<input value={actor} onChange={(event) => setActor(event.target.value)} maxLength={80} required /></label></div><label>Count notes / explanation<textarea required value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={500} /></label><h3>2. Count products</h3>{products.map((product) => <label className="retail-count" key={product.id}><span>{product.name} · {product.sku}<small>Last loaded catalogue: {product.stock_qty} units · {product.unit_cost_micros == null ? 'cost not recorded' : `weighted-average cost ${(product.unit_cost_micros / 1000000).toFixed(6)}`}</small></span><input aria-label={`Counted units for ${product.name}`} type="number" min="0" step="1" value={counts[product.id] ?? ''} onChange={(event) => setCounts((current) => ({ ...current, [product.id]: event.target.value }))} placeholder="Not counted" /></label>)}<button className="primary-action" type="submit">{busy ? 'Saving…' : 'Save count draft for review'}</button><p>Saving this count does not adjust stock.</p></fieldset></form> : <section className="cost-card"><h3>3. Review saved count</h3><p>{draft.mode.replace('_', ' ')} · {draft.count_date} · {draft.actor}</p><p>Draft receipt {draft.id} · {draft.status}</p><ul>{draft.lines.map((line) => <li key={line.product_id}>{products.find((product) => product.id === line.product_id)?.name ?? line.product_id}: expected {draft.expected_snapshot[line.product_id]} → <strong>{line.counted_qty} counted units</strong> · adjustment {line.counted_qty - draft.expected_snapshot[line.product_id]}</li>)}</ul><p>These expected quantities were captured by the service when the draft was saved. If stock changed since, confirmation is rejected; refresh and recount in a new draft.</p>{draft.status === 'draft' && <><label className="cost-check"><input type="checkbox" checked={ack} disabled={busy} onChange={(event) => setAck(event.target.checked)} />I reviewed every expected quantity, physical count, adjustment and explanation.</label><div className="cost-actions"><button type="button" disabled={busy} onClick={() => { void act(async () => { setDraft(await retailApi.getStockTake(draft.id)); setUncertain(false); setAck(false) }) }}>Reload saved count</button><button type="button" className="primary-action" disabled={disabled || busy || !ack || uncertain} onClick={() => { void confirm() }}>Confirm reviewed stock adjustments</button><button type="button" disabled={busy} onClick={() => { void act(async () => { await onChanged(); setDraft(null); setAck(false); setUncertain(false) }) }}>Refresh catalogue and prepare a new count</button></div>{uncertain && <p className="cost-warning">Outcome unconfirmed or baseline changed. Reload before retrying. A changed baseline requires a new physical count.</p>}</>}{result && <section role="status"><h3>Count confirmed by service</h3><p>{result.adjustments.length} audited stock adjustments. No cash or bank correction was made.</p>{result.adjustments.map((item) => <p key={item.id}>{item.product_id}: {item.expected_qty} → {item.counted_qty} · audit {item.id}</p>)}</section>}</section>}{error && <p className="cost-error" role="alert">{error}</p>}</section>
}
