import { useEffect, useRef, useState, type FormEvent } from 'react'
import { apiClient, getApiConfig } from './api'
import { museSourcePeriod, shopConfigurationError, type MuseResponse } from './muse'
import './muse.css'

type RequestType = 'analysis' | 'loan' | 'reel'
type Result = { state: 'idle' } | { state: 'loading' } | { state: 'error'; message: string } | { state: 'ready'; data: MuseResponse }
const prompts = ['What profit did I make in the last 30 days?', 'What were my sales today?', 'What were my sales this month?']

export function AskMuse({ onBack }: { onBack: () => void }) {
  const [question, setQuestion] = useState(prompts[0])
  const [requestType, setRequestType] = useState<RequestType>('analysis')
  const [result, setResult] = useState<Result>({ state: 'idle' })
  const pending = useRef<AbortController | null>(null)
  const configurationError = shopConfigurationError(getApiConfig())
  useEffect(() => () => { pending.current?.abort() }, [])

  const reset = () => { pending.current?.abort(); pending.current = null; setResult({ state: 'idle' }) }
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (requestType !== 'analysis' || !question.trim() || pending.current) return
    const controller = new AbortController()
    pending.current = controller
    setResult({ state: 'loading' })
    try {
      const data = await apiClient.askMuse(question, controller.signal)
      if (!controller.signal.aborted) setResult({ state: 'ready', data })
    } catch (error) {
      if (!controller.signal.aborted) setResult({ state: 'error', message: error instanceof Error ? error.message : 'Muse could not answer. Please try again.' })
    } finally {
      if (pending.current === controller) pending.current = null
    }
  }

  return <section className="tool-placeholder ask-muse">
    <button className="back-link" onClick={onBack}>← Back to Today</button>
    <div className="tool-hero profit-tool"><span className="tool-glyph">✦</span><p className="eyebrow">ASK MUSE</p><h2>Your shop assistant.</h2><p>Ask about your recorded sales. Profit answers need connected cost and expense records.</p></div>
    <div className="muse-tabs" role="group" aria-label="Muse tools">
      {([['analysis', 'Profit & sales'], ['loan', 'Loan help'], ['reel', 'Facebook Reel']] as const).map(([key, label]) => <button key={key} aria-pressed={requestType === key} className={requestType === key ? 'selected' : ''} onClick={() => { reset(); setRequestType(key) }}>{label}</button>)}
    </div>
    {requestType !== 'analysis' ? <section className="analysis-card muse-unavailable" role="status">
      <h3>{requestType === 'loan' ? 'Loan help is not connected yet' : 'Facebook Reel is not connected yet'}</h3>
      <p>{requestType === 'loan' ? 'Loan document preparation and application support are unavailable here. No application has been prepared or sent.' : 'Video generation and Facebook publishing are unavailable here. No script, video, or post has been created.'}</p>
      <p>Source period: unavailable. Data coverage: no connected service for this tool.</p>
      <button className="back-link" onClick={() => setRequestType('analysis')}>Ask about sales instead →</button>
    </section> : <>
      <form className="analysis-card" onSubmit={(event) => { void submit(event) }}>
        {configurationError && <div className="muse-response muse-error" role="alert"><h3>Shop connection needs attention</h3><p>{configurationError}</p><p>Return to Today and open Shop Connection. No question will be sent until the configuration is valid.</p></div>}
        <label htmlFor="muse-question">Ask about your sales or profit</label>
        <textarea id="muse-question" value={question} onChange={(event) => { reset(); setQuestion(event.target.value) }} rows={4} maxLength={1000} required aria-describedby="muse-period-note" />
        <div className="muse-prompts">{prompts.map((prompt) => <button type="button" key={prompt} onClick={() => { reset(); setQuestion(prompt) }}>{prompt}</button>)}</div>
        <p id="muse-period-note" className="muted">Try today, this month, or the last 30 days. Historical comparisons and exact source dates are not supplied by this service yet.</p>
        <button className="primary-action full" disabled={!!configurationError || result.state === 'loading' || !question.trim()} type="submit">{result.state === 'loading' ? 'Asking Muse…' : result.state === 'error' ? 'Retry question' : 'Send to Muse'}<span className="arrow">→</span></button>
      </form>
      <div aria-live="polite" aria-atomic="true" aria-busy={result.state === 'loading'}>
        {result.state === 'idle' && <p className="muse-idle">No answer requested yet. Only connected shop records will be used.</p>}
        {result.state === 'loading' && <div className="muse-response" role="status"><strong>Checking your connected shop records…</strong><p>Waiting for Muse. Source period and coverage will appear with the response.</p></div>}
        {result.state === 'error' && <div className="muse-response muse-error" role="alert"><h3>Could not get an answer</h3><p>{result.message}</p><p>Source period: unavailable. Data coverage: no answer received.</p></div>}
        {result.state === 'ready' && <MuseAnswer data={result.data} />}
      </div>
    </>}
  </section>
}

function MuseAnswer({ data }: { data: MuseResponse }) {
  const label = data.status === 'needs_data' ? 'More data needed' : data.status === 'unavailable' ? 'Muse unavailable' : 'Answer received'
  return <article className={`muse-response muse-answer muse-${data.status}`}>
    <span className="muse-status">{label}</span><h3>{data.title}</h3><p className="muse-answer-text">{data.answer}</p>
    <dl><div><dt>Source period</dt><dd>{museSourcePeriod(data.evidence_ids)}</dd></div><div><dt>Answer source</dt><dd>{data.source === 'meta' ? 'Meta AI using shop evidence' : data.source === 'repository' ? 'Connected shop records' : data.source === 'fallback' ? 'Service fallback — no model answer' : data.source}</dd></div><div><dt>Data coverage</dt><dd>{data.evidence_ids.length ? `${data.evidence_ids.length} evidence references supplied. Completeness has not been verified.` : 'No evidence references supplied. Coverage cannot be verified.'}</dd></div></dl>
    {data.missing_data.length > 0 && <div><h4>Missing data</h4><ul>{data.missing_data.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
    {data.evidence_ids.length > 0 && <details><summary>Evidence references</summary><ul>{data.evidence_ids.map((id, index) => <li key={index}>{id}</li>)}</ul></details>}
  </article>
}
