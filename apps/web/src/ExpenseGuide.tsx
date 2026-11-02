import { useEffect, useRef, useState, type FormEvent } from 'react'
import { costsApi } from './api'
import { expenseCategories, moneyToCents, type ExpenseCategory, type ExpenseRecord, type ExpenseRequest } from './costs'

const prompts: Record<ExpenseCategory, string> = { electricity: 'How much electricity did the shop use or pay for?', transport: 'What did transport for the shop cost?', rent: 'What rent covers this shop period?', wages: 'What wages relate to this shop period?', airtime: 'What airtime or data did the shop use?', supplies: 'What operating supplies did you buy?', other: 'What other operating expense did the shop incur?' }

export function ExpenseGuide({ disabled }: { disabled: boolean }) {
  const [category, setCategory] = useState<ExpenseCategory>('electricity')
  const [amount, setAmount] = useState('')
  const [occurredOn, setOccurredOn] = useState('')
  const [frequency, setFrequency] = useState<ExpenseRequest['frequency']>('one_off')
  const [periodStart, setPeriodStart] = useState('')
  const [periodEnd, setPeriodEnd] = useState('')
  const [tender, setTender] = useState<ExpenseRequest['tender']>('unpaid')
  const [notes, setNotes] = useState('')
  const [saved, setSaved] = useState<ExpenseRecord | null>(null)
  const [history, setHistory] = useState<ExpenseRecord[] | null>(null)
  const [historyError, setHistoryError] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const lock = useRef(false)
  const reload = async () => { try { setHistory(await costsApi.listExpenses()); setHistoryError('') } catch (failure) { setHistoryError(failure instanceof Error ? failure.message : 'Could not load expenses.') } }
  useEffect(() => { void reload() }, [])
  const perform = async (action: () => Promise<void>) => {
    if (disabled || lock.current) return
    lock.current = true; setBusy(true); setError('')
    try { await action() } catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not save this expense.') }
    finally { lock.current = false; setBusy(false) }
  }
  const save = (event: FormEvent) => {
    event.preventDefault()
    void perform(async () => {
      const result = await costsApi.createExpense({ category, amount_cents: moneyToCents(amount), occurred_on: occurredOn, frequency, period_start: frequency === 'recurring' ? periodStart : null, period_end: frequency === 'recurring' ? periodEnd : null, tender, notes })
      setSaved(result); await reload()
    })
  }
  const confirm = () => perform(async () => { if (!saved || saved.status !== 'draft') return; setSaved(await costsApi.confirmExpense(saved.id)); await reload() })
  const reset = () => { setSaved(null); setAmount(''); setOccurredOn(''); setPeriodStart(''); setPeriodEnd(''); setNotes(''); setError('') }
  return <section className="expense-guide"><h2>Operating expenses</h2><p>Answer the questions, save a draft, then review and confirm. This records an expense; it does not transfer money.</p>
    {!saved ? <form className="cost-card" onSubmit={save}><fieldset disabled={busy}>
      <legend>1. What is this expense for?</legend><label>Expense category<select value={category} onChange={(event) => setCategory(event.target.value as ExpenseCategory)}>{expenseCategories.map((item) => <option key={item} value={item}>{item.charAt(0).toUpperCase() + item.slice(1)}</option>)}</select></label><p>{prompts[category]}</p>
      <label>2. Amount (shop currency)<input inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="0.00" required /></label><label>3. When did the expense occur?<input type="date" value={occurredOn} onChange={(event) => setOccurredOn(event.target.value)} required /></label>
      <label>4. Is it one-off or recurring?<select value={frequency} onChange={(event) => setFrequency(event.target.value as ExpenseRequest['frequency'])}><option value="one_off">One-off</option><option value="recurring">Recurring for a period</option></select></label>
      {frequency === 'recurring' && <><div className="cost-fields"><label>Period start<input type="date" value={periodStart} onChange={(event) => setPeriodStart(event.target.value)} required /></label><label>Period end<input type="date" min={periodStart} value={periodEnd} onChange={(event) => setPeriodEnd(event.target.value)} required /></label></div><p>This records the amount for this period. It does not automatically create future expenses.</p></>}
      <label>5. How was it paid?<select value={tender} onChange={(event) => setTender(event.target.value as ExpenseRequest['tender'])}><option value="unpaid">Unpaid / not paid yet</option><option value="cash">Cash</option><option value="bank">Bank</option></select></label><label>6. Any notes or reference?<textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} maxLength={500} placeholder="Optional explanation or document reference" /></label>
      <button className="primary-action" type="submit" disabled={disabled || busy}>{busy ? 'Saving draft…' : 'Save expense draft for review'}</button></fieldset></form>
      : <section className="cost-card"><h3>Review saved expense</h3><dl className="cost-review"><dt>Category</dt><dd>{saved.category}</dd><dt>Amount (shop currency)</dt><dd>{(saved.amount_cents / 100).toFixed(2)}</dd><dt>Expense date</dt><dd>{saved.occurred_on}</dd><dt>Frequency / period</dt><dd>{saved.frequency === 'one_off' ? 'One-off' : `${saved.period_start} to ${saved.period_end}`}</dd><dt>Payment status</dt><dd>{saved.tender}</dd><dt>Notes</dt><dd>{saved.notes || 'None'}</dd><dt>Backend status</dt><dd>{saved.status}</dd></dl><p>Receipt {saved.id}. Confirm only after checking the amount, period, and category.</p>{saved.status === 'draft' && <button className="primary-action" type="button" disabled={disabled || busy} onClick={() => { void confirm() }}>{busy ? 'Confirming…' : 'Confirm this expense'}</button>}{saved.status === 'confirmed' && <p role="status">Expense confirmed by the backend. No payment transfer or future recurring charge was made.</p>}<button type="button" disabled={busy} onClick={reset}>Start a new expense</button></section>}
    {error && <p className="cost-error" role="alert">{error}</p>}
    <section className="cost-card"><div className="cost-heading"><h3>Saved expense records</h3><button type="button" disabled={busy} onClick={() => { void reload() }}>Refresh expenses</button></div>{historyError && <p className="cost-error" role="alert">{historyError}</p>}{history === null && !historyError && <p role="status">Loading expenses…</p>}{history?.length === 0 && !historyError && <p>No expense records returned by this shop.</p>}<ul className="cost-history">{history?.map((item) => <li key={item.id}><button type="button" disabled={busy} onClick={() => { setSaved(item); setError('') }}>{item.category} · {(item.amount_cents / 100).toFixed(2)}<small>{item.occurred_on} · {item.frequency.replace('_', '-')} · {item.status}</small></button></li>)}</ul><p>Only confirmed records are eligible for the backend's profit inputs. In-memory records reset on server restart.</p></section>
  </section>
}
