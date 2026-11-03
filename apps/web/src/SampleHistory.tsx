import './sample-history.css'
import { useEffect, useState } from 'react'
import { getApiConfig, saveApiConfig } from './api'

type SampleStatus = { count: number; start: string | null; end: string | null; today: string; changed?: number }
type SampleAction = 'seed' | 'delete' | 'delete_all'

function daysBefore(iso: string, days: number): string {
  const date = new Date(iso + 'T00:00:00Z')
  date.setUTCDate(date.getUTCDate() - days)
  return date.toISOString().slice(0, 10)
}

export function SampleHistory({ shopId, switchDisabled }: { shopId: string; switchDisabled: boolean }) {
  const { baseUrl, shopId: activeShopId } = getApiConfig()
  const endpoint = baseUrl + '/api/v1/demo/sample-history'
  const [status, setStatus] = useState<SampleStatus | null>(null)
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [target, setTarget] = useState<'transactions' | 'sales'>('transactions')
  const [frequency, setFrequency] = useState<'day' | 'month'>('day')
  const [transactions, setTransactions] = useState('2')
  const [salesValue, setSalesValue] = useState('')
  const transactionLimit = frequency === 'day' ? 20 : 560
  const count = Number(transactions)
  const validTargets = target === 'transactions'
    ? Number.isInteger(count) && count >= 1 && count <= transactionLimit
    : /^\d+(?:\.\d{1,2})?$/.test(salesValue) && Number(salesValue) > 0 && Number(salesValue) <= (frequency === 'day' ? 1000 : 30000)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [confirming, setConfirming] = useState<SampleAction | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetch(endpoint, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('Sample data controls require the local demo server.')
      const current: SampleStatus = await response.json()
      setStatus(current)
      setStart(daysBefore(current.today, 119))
      setEnd(current.today)
    }).catch(error => {
      if (!controller.signal.aborted) setMessage(error.message)
    })
    return () => controller.abort()
  }, [endpoint])

  const valid = !!status && start >= daysBefore(status.today, 359) && start <= end && end <= status.today
  async function change(action: SampleAction) {
    setBusy(true)
    setConfirming(null)
    setMessage('')
    try {
      const params = new URLSearchParams({ action, confirm: String(action !== 'seed') })
      if (action !== 'delete_all') { params.set('start', start); params.set('end', end) }
      if (action === 'seed') {
        if (target === 'transactions') {
          params.set(frequency === 'day' ? 'daily_target' : 'monthly_target', transactions)
        } else {
          params.set(frequency === 'day' ? 'daily_sales_cents' : 'monthly_sales_cents', String(Math.round(Number(salesValue) * 100)))
        }
      }
      const response = await fetch(endpoint + '?' + params, { method: 'POST' })
      const result = await response.json()
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Check the date range and try again.')
      setStatus(result)
      if (action !== 'seed') {
        setMessage(`Deleted ${result.changed} sample receipts.`)
      } else if (result.changed) {
        const sales = result.generated_sales_cents / 100
        const days = (Date.parse(end) - Date.parse(start)) / 86_400_000 + 1
        setMessage(`Added ${result.changed} receipts (${(result.changed / days).toFixed(1)} per selected day), with ${result.currency} ${sales.toFixed(2)} in sales (${(sales / days).toFixed(2)} per selected day).`)
      } else {
        setMessage('No new receipts added. Check for dates already seeded or closed.')
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Sample data request failed.')
    } finally {
      setBusy(false)
    }
  }

  return <section className="analysis-card sample-history" aria-label="Sample sales data">
    <header className="sample-history-header"><span>DEMO WORKSPACE</span><h3>Sample sales data</h3></header>
    <p>Choose dates within the last 360 days, including today. Sample receipts live in a separate shop and feed Reports and Ask Muse there.</p>
    {status && <>
      <div className="sample-history-summary"><strong>{status.count.toLocaleString()}</strong><span>Sample receipts</span><small>{status.start ? `${status.start} to ${status.end}` : 'Choose a date range to get started'}</small></div>
      <div className="sample-history-dates">
      <label>Start date<input type="date" value={start} min={daysBefore(status.today, 359)} max={status.today} disabled={busy} onChange={event => { setStart(event.target.value); setConfirming(null) }} /></label>
      <label>End date<input type="date" value={end} min={start || daysBefore(status.today, 359)} max={status.today} disabled={busy} onChange={event => { setEnd(event.target.value); setConfirming(null) }} /></label>
      </div>
      <label>Generate based on<select value={target} disabled={busy} onChange={event => setTarget(event.target.value === 'sales' ? 'sales' : 'transactions')}>
        <option value="transactions">Average number of transactions</option>
        <option value="sales">Average total sales</option>
      </select></label>
      <div className="sample-history-dates">
        <label>Target period<select value={frequency} disabled={busy} onChange={event => {
          const unit = event.target.value === 'month' ? 'month' : 'day'
          setFrequency(unit)
          setTransactions(unit === 'day' ? '2' : '60')
        }}><option value="day">Day</option><option value="month">Month</option></select></label>
        {target === 'transactions' ? <label>Transaction target<input type="number" min={1} max={transactionLimit} step={1} value={transactions} disabled={busy} onChange={event => setTransactions(event.target.value)} /></label>
      : <label>Total sales per {frequency} (USD)<input inputMode="decimal" placeholder={frequency === 'day' ? 'e.g. 25.00' : 'e.g. 750.00'} value={salesValue} disabled={busy} onChange={event => setSalesValue(event.target.value)} /></label>}
      </div>
      <p>{target === 'transactions'
        ? 'Monthly targets are spread across calendar days. Receipt values vary with the products selected.'
        : 'Monthly sales are spread across calendar days. The generator uses catalogue prices to approach the total.'} Dates already seeded are skipped.</p>
      <div className="sample-history-actions">
        <button type="button" disabled={busy || !valid || !validTargets || switchDisabled} onClick={() => void change('seed')}>Generate sample sales</button></div>
      <div className="sample-history-cleanup"><span>Remove generated receipts</span>
        <button type="button" disabled={busy || !valid || !status.count || switchDisabled} onClick={() => setConfirming('delete')}>Delete selected dates</button>
        <button type="button" disabled={busy || !status.count || switchDisabled} onClick={() => setConfirming('delete_all')}>Delete all dummy data</button>
      </div>
      {confirming && <div className="sample-history-confirm" role="alert">
        <p>{confirming === 'delete_all' ? 'Delete all generated sample receipts?' : `Delete generated sample receipts from ${start} to ${end}?`}</p>
        <button type="button" disabled={busy || switchDisabled} onClick={() => void change(confirming)}>Confirm deletion</button>
        <button type="button" onClick={() => setConfirming(null)}>Cancel</button>
      </div>}
      {status.count > 0 && activeShopId !== shopId && <button className="sample-history-open" type="button" disabled={busy || switchDisabled} onClick={() => {
        try { saveApiConfig({ baseUrl, shopId }); window.location.reload() }
        catch { setMessage('Could not open the sample shop. Check your shop connection.') }
      }}>Open sample shop</button>}
    </>}
    {message && <p role="status">{message}</p>}
  </section>
}
