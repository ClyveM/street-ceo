import { clientId } from './clientId'
import { useRef, useState } from 'react'
import { moneyToCents, validDate } from './costs'
import { retailApi } from './api'
import { closeComponentKeys, type DayCloseInput, type DayClosePreview, type DayCloseRecord } from './retailContracts'

const money = (value: number) => {
  const amount = BigInt(value), absolute = amount < 0n ? -amount : amount
  return `${amount < 0n ? '-' : ''}${absolute / 100n}.${String(absolute % 100n).padStart(2, '0')}`
}
const samePreview = (a: DayClosePreview, b: DayClosePreview) => a.business_date === b.business_date && a.calculation_basis === b.calculation_basis && a.shop_timezone === b.shop_timezone && a.expected_cash_cents === b.expected_cash_cents && a.expected_bank_card_cents === b.expected_bank_card_cents && closeComponentKeys.every((key) => a[key] === b[key])

function CloseBreakdown({ value }: { value: DayClosePreview }) {
  const rows = [
    ['Opening recorded balance', value.opening_cash_cents, value.opening_bank_card_cents],
    ['Sales received', value.sales_cash_cents, value.sales_bank_card_cents],
    ['Paid operating expenses', value.paid_expenses_cash_cents, value.paid_expenses_bank_card_cents],
    ['Paid purchases', value.paid_purchases_cash_cents, value.paid_purchases_bank_card_cents],
    ['Refunds', value.refunds_cash_cents, value.refunds_bank_card_cents],
    ['Signed adjustments', value.adjustments_cash_cents, value.adjustments_bank_card_cents],
    ['Expected closing record', value.expected_cash_cents, value.expected_bank_card_cents],
  ] as const
  return <div className="retail-reconciliation" role="table" aria-label="Recorded cash and bank movements"><div role="row"><b role="columnheader">Shop currency</b><b role="columnheader">Cash</b><b role="columnheader">Bank/card</b></div>{rows.map(([label, cash, bank]) => <div role="row" key={label}><span role="rowheader">{label}</span><span role="cell">{cash === undefined ? 'Not supplied' : money(cash)}</span><span role="cell">{bank === undefined ? 'Not supplied' : money(bank)}</span></div>)}</div>
}

export function DayClose({ disabled = false }: { disabled?: boolean }) {
  const [date, setDate] = useState(''), [cash, setCash] = useState(''), [bank, setBank] = useState(''), [actor, setActor] = useState(''), [notes, setNotes] = useState('')
  const [review, setReview] = useState<DayCloseInput | null>(null), [error, setError] = useState('')
  const [preview, setPreview] = useState<DayClosePreview | null>(null), [busy, setBusy] = useState(false), [ack, setAck] = useState(false)
  const [receipt, setReceipt] = useState<DayCloseRecord | null>(null), [uncertain, setUncertain] = useState(false)
  const lock = useRef(false), key = useRef('')
  const perform = async (action: () => Promise<void>) => {
    if (disabled || lock.current) return
    lock.current = true; setBusy(true); setError('')
    try { await action() } catch (failure) { setError(failure instanceof Error ? failure.message : 'Daily close outcome unconfirmed.') }
    finally { lock.current = false; setBusy(false) }
  }
  const prepare = () => perform(async () => {
    if (!validDate(date) || !actor.trim()) throw new Error('Choose the business date and enter who counted the balances.')
    const input = { business_date: date, cash_counted_cents: moneyToCents(cash, true), bank_card_counted_cents: moneyToCents(bank, true), actor: actor.trim(), notes: notes.trim(), confirmed: false }
    setPreview(await retailApi.previewDayClose(date)); setReview(input); setAck(false); setUncertain(false); key.current = `web-close-${clientId()}`
  })
  const confirm = () => perform(async () => {
    if (!review || !preview || !ack || preview.calculation_basis !== 'full_recorded_movements') return
    if (!uncertain) {
      const fresh = await retailApi.previewDayClose(review.business_date)
      if (!samePreview(preview, fresh)) { setPreview(fresh); setAck(false); setError('Recorded movements changed. Review the updated breakdown and counts before confirming.'); return }
    }
    try { setReceipt(await retailApi.confirmDayClose({ ...review, confirmed: true }, key.current)); setAck(false); setUncertain(false) }
    catch (failure) { setUncertain(true); throw failure }
  })
  const value = receipt ?? preview
  return <section><h2>End-of-day cash & bank close</h2><p>Count cash separately from your bank/card record, then compare every recorded movement in the shop's business day. Bank records do not verify settlement.</p>
    {!review ? <form onSubmit={(event) => { event.preventDefault(); void prepare() }}><fieldset className="retail-form" disabled={disabled || busy}><legend>1. Your actual closing count</legend><label>Business date<input type="date" value={date} onChange={(event) => setDate(event.target.value)} required /></label><div className="cost-fields"><label>Cash physically counted (shop currency)<input inputMode="decimal" value={cash} onChange={(event) => setCash(event.target.value)} required /></label><label>Bank / card recorded amount (shop currency)<input inputMode="decimal" value={bank} onChange={(event) => setBank(event.target.value)} required /></label></div><label>Counted by<input value={actor} onChange={(event) => setActor(event.target.value)} maxLength={80} required /></label><label>Notes / variance explanation<textarea value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={500} /></label><button type="submit">{busy ? 'Loading movements…' : 'Review recorded movements and counts'}</button><p>This step reads the expected totals; it does not save or lock a close.</p></fieldset></form>
    : <section className="cost-card"><h3>{receipt ? 'Daily close saved by service' : '2. Review before locking the close'}</h3><p>{review.business_date} · {review.actor} · shop timezone: {value?.shop_timezone}</p>{value?.calculation_basis === 'full_recorded_movements' ? <p>Full recorded movements. Verify opening balances and all entries; this does not prove that missing transactions were captured.</p> : <p className="cost-warning">This service supplied sales-only totals. Full daily close is unavailable; no closing balance or variance is verified.</p>}{value && <CloseBreakdown value={value} />}<dl className="cost-review"><dt>Actual cash / bank-card count</dt><dd>{money(review.cash_counted_cents)} / {money(review.bank_card_counted_cents)}</dd><dt>Cash difference / bank-card difference</dt><dd>{value?.calculation_basis === 'full_recorded_movements' ? `${money(review.cash_counted_cents - value.expected_cash_cents)} / ${money(review.bank_card_counted_cents - value.expected_bank_card_cents)}` : 'Not verified'}</dd><dt>Notes</dt><dd>{review.notes || 'None'}</dd></dl><ul>{value?.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>
    {receipt ? <section role="status"><p>Close receipt {receipt.id} · audit {receipt.audit_id} · {receipt.confirmed_at}</p><p>This date is locked. No variance correction or transfer was automatically posted. Records are temporary until durable storage is integrated.</p></section> : <><label className="cost-check"><input type="checkbox" checked={ack} disabled={busy || preview?.calculation_basis !== 'full_recorded_movements'} onChange={(event) => setAck(event.target.checked)} />I reviewed the date, recorded movements, physical counts and differences. Lock this close without posting a variance correction.</label><div className="cost-actions"><button type="button" disabled={busy || uncertain} onClick={() => { setReview(null); setAck(false) }}>Edit counts</button><button className="primary-action" type="button" disabled={busy || disabled || !ack || preview?.calculation_basis !== 'full_recorded_movements'} onClick={() => { void confirm() }}>{busy ? 'Confirming…' : uncertain ? 'Recover close with original request reference' : 'Confirm and lock daily close'}</button></div>{uncertain && <p className="cost-warning">Outcome uncertain or date already locked. Keep this review unchanged; use the original reference above to recover a successful request. Do not create another close.</p>}</>}
    </section>}{error && <p role="alert" className="cost-error">{error}</p>}</section>
}
