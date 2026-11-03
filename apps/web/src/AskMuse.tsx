import { useEffect, useRef, useState, type FormEvent } from 'react'
import { apiClient, getApiConfig } from './api'
import { museSourcePeriod, shopConfigurationError, type MuseResponse } from './muse'
import { clientId } from './clientId'
import './muse.css'

type Result = { state: 'idle' } | { state: 'loading' } | { state: 'error'; message: string } | { state: 'ready'; data: MuseResponse }
type ChatTurn = { question: string; answer: MuseResponse }
type SavedChat = { id: string; turns: ChatTurn[] }
type ChatHistory = { activeId: string; chats: SavedChat[] }

function readChats(key: string): ChatHistory {
  try {
    const saved = JSON.parse(localStorage.getItem(key) ?? 'null')
    if (saved && Array.isArray(saved.chats) && typeof saved.activeId === 'string') return saved
  } catch { /* Start a fresh chat if storage is unavailable. */ }
  return { activeId: clientId(), chats: [] }
}

const prompts = ['Show my stock', 'How am I doing?', 'Ndikuda chikwereti']

export function AskMuse({ onBack }: { onBack: () => void }) {
  const [question, setQuestion] = useState('')
  const config = getApiConfig()
  const historyKey = `street-ceo-muse-chats-v1:${JSON.stringify([config.baseUrl, config.shopId])}`
  const [history, setHistory] = useState(() => readChats(historyKey))
  const turns = history.chats.find(chat => chat.id === history.activeId)?.turns ?? []
  const lastAnswer = turns[turns.length - 1]?.answer
  const needsLoanDetails = lastAnswer?.missing_data.some(item => item === 'Loan amount and purpose' || item === 'Loan amount in USD')
  const needsLoanTerms = lastAnswer?.missing_data.some(item => /repayment term|interest rate|upfront fees/i.test(item))
  const replyHint = lastAnswer?.missing_data.includes('Monthly repayment budget')
    ? 'Enter your monthly repayment budget and the lender’s term, annual rate and fees.'
    : needsLoanDetails ? 'Example: USD 500 for stock'
    : needsLoanTerms ? 'Enter the term, interest rate and fees the lender quoted.'
    : turns.length ? 'Type your follow-up.' : 'Ask a question about your shop.'
  const [historyError, setHistoryError] = useState(false)

  const saveHistory = (next: ChatHistory) => {
    setHistory(next)
    try {
      localStorage.setItem(historyKey, JSON.stringify(next))
      setHistoryError(false)
    } catch {
      setHistoryError(true)
    }
  }
  const [result, setResult] = useState<Result>({ state: 'idle' })
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    if (result.state !== 'loading') return
    const started = Date.now()
    const timer = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000)
    return () => window.clearInterval(timer)
  }, [result.state])
  const pending = useRef<AbortController | null>(null)
  const configurationError = shopConfigurationError(getApiConfig())
  useEffect(() => () => { pending.current?.abort() }, [])

  const reset = () => { pending.current?.abort(); pending.current = null; setResult({ state: 'idle' }) }
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (configurationError || !question.trim() || pending.current) return
    const controller = new AbortController()
    pending.current = controller
    setElapsed(0)
    setResult({ state: 'loading' })
    try {
      const message = question.trim()
      const historyBudget = Math.max(0, 1000 - message.length - 40)
      const contextLines = turns.map(turn => `User: ${turn.question.slice(0, 190)}`)
      const selected = contextLines.length && contextLines[0].length <= historyBudget ? [contextLines[0]] : []
      let remaining = historyBudget - (selected[0]?.length ?? 0)
      const recent = []
      for (const line of contextLines.slice(selected.length).slice(-4).reverse()) {
        if (line.length + 1 > remaining) break
        recent.unshift(line)
        remaining -= line.length + 1
      }
      const recentContext = [...selected, ...recent].join('\n')
      const request = historyBudget && recentContext
        ? `Recent conversation:\n${recentContext}\nUser: ${message}`
        : message
      const data = await apiClient.askMuse(request, controller.signal)
      if (!controller.signal.aborted) {
        const updated = { id: history.activeId, turns: [...turns, { question: message, answer: data }] }
        saveHistory({ activeId: updated.id, chats: [updated, ...history.chats.filter(chat => chat.id !== updated.id)] })
        setQuestion('')
        setResult({ state: 'idle' })
      }
    } catch (error) {
      if (!controller.signal.aborted) setResult({ state: 'error', message: error instanceof Error ? error.message : 'Muse could not answer. Please try again.' })
    } finally {
      if (pending.current === controller) pending.current = null
    }
  }

  return <section className="tool-placeholder ask-muse">
    <button className="back-link" onClick={onBack}>← Back to Today</button>
    <div className="tool-hero profit-tool"><span className="tool-glyph">✦</span><h2>Ask Muse</h2></div>
      <div className="muse-tabs" aria-label="Chat history">
        <button type="button" onClick={() => {
          reset()
          saveHistory({ ...history, activeId: clientId() })
          setQuestion('')
        }}>New chat</button>
        {history.chats.length > 0 && <label>Chat history
          <select value={history.activeId} onChange={event => {
            reset()
            saveHistory({ ...history, activeId: event.target.value })
            setQuestion('')
          }}>
            {!turns.length && <option value={history.activeId}>New conversation</option>}
            {history.chats.map(chat => <option key={chat.id} value={chat.id}>{chat.turns[0]?.question.slice(0, 80) || 'Conversation'}</option>)}
          </select>
        </label>}
      </div>
      {historyError && <p role="status">This browser could not save your chat history.</p>}
      {turns.length > 0 && <section aria-label="Conversation">
        {turns.map((turn, index) => <div key={index}>
          <p><strong>You</strong> {turn.question}</p>
          <MuseAnswer data={turn.answer} />
        </div>)}
      </section>}
      <form className="analysis-card" onSubmit={(event) => { void submit(event) }}>
        {configurationError && <div className="muse-response muse-error" role="alert"><h3>Shop connection needs attention</h3><p>{configurationError}</p><p>Return to Today and open Shop Connection. No question will be sent until the configuration is valid.</p></div>}
        <label htmlFor="muse-question">{turns.length ? 'Reply to Muse' : 'What would you like to ask?'}</label>
        <textarea id="muse-question" value={question} onChange={(event) => { reset(); setQuestion(event.target.value) }} rows={4} maxLength={1000} required aria-describedby="muse-period-note" />
        {!turns.length && <div className="muse-prompts">{prompts.map((prompt) => <button type="button" key={prompt} onClick={() => { reset(); setQuestion(prompt) }}>{prompt}</button>)}</div>}
        <p id="muse-period-note" className="muted">{replyHint}</p>
        <button className="primary-action full" disabled={!!configurationError || result.state === 'loading' || !question.trim()} type="submit">{result.state === 'loading' ? 'Asking Muse…' : result.state === 'error' ? 'Retry question' : 'Send to Muse'}<span className="arrow">→</span></button>
      </form>
      <div aria-live="polite" aria-atomic="true" aria-busy={result.state === 'loading'}>
        {result.state === 'idle' && !turns.length && <p className="muse-idle">No answer requested yet. Only connected shop records will be used.</p>}
        {result.state === 'loading' && <div className="muse-response" role="status"><strong>{elapsed < 12 ? 'Muse is choosing which shop records to use…' : 'Muse is still working on your answer…'}</strong><p>{elapsed < 12 ? 'It can request sales, inventory, cash or forecast data.' : 'The request is still running. Detailed answers can take longer.'} {elapsed}s elapsed.</p></div>}
        {result.state === 'error' && <div className="muse-response muse-error" role="alert"><h3>Could not get an answer</h3><p>{result.message}</p><p>Source period: unavailable. Data coverage: no answer received.</p></div>}
        {result.state === 'ready' && <MuseAnswer data={result.data} />}
      </div>
  </section>
}

function MuseAnswer({ data }: { data: MuseResponse }) {
  const label = data.status === 'needs_data' ? 'More data needed' : data.status === 'unavailable' ? 'Muse unavailable' : 'Answer received'
  return <article className={`muse-response muse-answer muse-${data.status}`}>
    <span className="muse-status">{label}</span><h3>{data.title}</h3><p className="muse-answer-text">{data.answer}</p>
    <details><summary>Answer details</summary><dl><div><dt>Source period</dt><dd>{museSourcePeriod(data.evidence_ids)}</dd></div><div><dt>Answer source</dt><dd>{data.source === 'meta' ? 'Meta AI using shop evidence' : data.source === 'repository' ? 'Connected shop records' : data.source === 'fallback' ? 'Service fallback — no model answer' : data.source}</dd></div><div><dt>Data coverage</dt><dd>{data.evidence_ids.length ? `${data.evidence_ids.length} evidence references supplied. Completeness has not been verified.` : 'No evidence references supplied. Coverage cannot be verified.'}</dd></div></dl>
    {data.missing_data.length > 0 && <div><h4>Missing data</h4><ul>{data.missing_data.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
    {data.evidence_ids.length > 0 && <details><summary>Evidence references</summary><ul>{data.evidence_ids.map((id, index) => <li key={index}>{id}</li>)}</ul></details>}
    </details>
  </article>
}
