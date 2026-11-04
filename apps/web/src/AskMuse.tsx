import { useEffect, useRef, useState, type FormEvent } from 'react'
import { apiClient, getApiConfig, type ApiConfig } from './api'
import {
  MuseJobError, SAMPLE_SHOP_ID, museJobProgressLabel, museSourcePeriod, shopConfigurationError,
  type MuseResponse, type PendingMuseJob,
} from './muse'
import { clientId } from './clientId'
import { buildMusePdf } from './musePdf'
import { deliverPdf } from './reportShare'
import './muse.css'

type Result = { state: 'idle' } | { state: 'loading'; label: string } | { state: 'error'; message: string }
type ChatTurn = { question: string; answer: MuseResponse; requestId?: string; jobId?: string }
type SavedChat = { id: string; turns: ChatTurn[] }
type ChatHistory = { activeId: string; chats: SavedChat[]; pending?: PendingMuseJob }

function completeJob(history: ChatHistory, job: PendingMuseJob, answer: MuseResponse): ChatHistory {
  const chat = history.chats.find(item => item.id === job.chatId)
  const turns = chat?.turns ?? []
  if (turns.some(turn => turn.requestId === job.requestId)) return { ...history, pending: undefined }
  const updated = { id: job.chatId, turns: [...turns, { question: job.message, answer, requestId: job.requestId, jobId: job.jobId }] }
  return { ...history, pending: undefined, chats: [updated, ...history.chats.filter(item => item.id !== job.chatId)] }
}

function readChats(key: string): ChatHistory {
  try {
    const saved = JSON.parse(localStorage.getItem(key) ?? 'null')
    if (saved && Array.isArray(saved.chats) && typeof saved.activeId === 'string') return saved
  } catch { /* Start a fresh chat if storage is unavailable. */ }
  return { activeId: clientId(), chats: [] }
}

const prompts = ['Show my stock', 'How am I doing?', 'Ndikuda chikwereti']

export function AskMuse({ config, onBack }: { config: ApiConfig; onBack: () => void }) {
  const [question, setQuestion] = useState('')
  const isSample = config.shopId.toLowerCase() === SAMPLE_SHOP_ID
  const [connectionChanged, setConnectionChanged] = useState(false)
  const historyKey = `street-ceo-muse-chats-v1:${JSON.stringify([config.baseUrl, config.shopId])}`
  const [history, setHistory] = useState(() => readChats(historyKey))
  const latest = useRef(history)
  const pending = history.pending
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

  const saveHistory = (next: ChatHistory, requirePersistence = false) => {
    try {
      localStorage.setItem(historyKey, JSON.stringify(next))
      setHistoryError(false)
    } catch {
      setHistoryError(true)
      if (requirePersistence) return false
    }
    latest.current = next
    setHistory(next)
    return true
  }
  const [result, setResult] = useState<Result>({ state: 'idle' })
  const [elapsed, setElapsed] = useState(0)
  const [attempt, setAttempt] = useState(0)
  const configurationError = shopConfigurationError(config)
  const requestId = pending?.requestId
  const startedAt = pending?.startedAt

  useEffect(() => {
    if (!startedAt || result.state !== 'loading') return
    const update = () => setElapsed(Math.max(0, Math.floor((Date.now() - startedAt) / 1000)))
    update()
    const timer = window.setInterval(update, 1000)
    return () => window.clearInterval(timer)
  }, [startedAt, result.state])

  useEffect(() => {
    if (!requestId || configurationError) return
    const controller = new AbortController()
    let timer: number | undefined
    let working = false
    let delay = 750
    let deadline = Date.now() + 5 * 60 * 1000

    const check = async () => {
      let job = latest.current.pending
      if (!job || job.requestId !== requestId || working || controller.signal.aborted) return
      const current = getApiConfig()
      if (current.shopId !== config.shopId || current.baseUrl !== config.baseUrl) {
        setConnectionChanged(true)
        setResult({ state: 'idle' })
        return
      }
      if (Date.now() >= deadline) {
        setResult({ state: 'error', message: 'Muse has not finished yet. Check the same request again when ready.' })
        return
      }
      working = true
      const checkingLabel = job.jobId ? 'Checking your Muse request…' : 'Connecting to Muse…'
      setResult(previous => previous.state === 'loading' ? previous : { state: 'loading', label: checkingLabel })
      try {
        const response = await apiClient.askMuseJob(config, job, controller.signal)
        if (controller.signal.aborted) return
        if (!job.jobId) {
          job = { ...job, jobId: response.job_id }
          saveHistory({ ...latest.current, pending: job })
        }
        // Only opaque correlation IDs, status and time enter the diagnostic console.
        console.info('muse_job', { at: new Date().toISOString(), requestId, jobId: response.job_id, status: response.status })
        if (response.result) {
          saveHistory(completeJob(latest.current, job, response.result))
          setQuestion('')
          setResult({ state: 'idle' })
          return
        }
        if (response.status === 'expired' || response.status === 'failed') {
          saveHistory({ ...latest.current, pending: undefined })
          setQuestion(job.message)
          setResult({ state: 'error', message: response.status === 'expired' ? 'This Muse request expired. You can send it again.' : 'Muse could not finish this request. You can send it again.' })
          return
        }
        setResult({ state: 'loading', label: museJobProgressLabel(response) })
      } catch (error) {
        if (controller.signal.aborted) return
        if (error instanceof MuseJobError && !error.retryable) {
          saveHistory({ ...latest.current, pending: undefined })
          setQuestion(job.message)
          setResult({ state: 'error', message: error.message })
          return
        }
        setResult({ state: 'loading', label: 'Connection interrupted. Checking again…' })
      } finally {
        working = false
      }
      timer = window.setTimeout(() => { void check() }, delay)
      delay = Math.min(delay * 2, 8000)
    }

    const resume = () => {
      if (working) return
      window.clearTimeout(timer)
      delay = 750
      deadline = Date.now() + 5 * 60 * 1000
      void check()
    }
    const onVisibility = () => { if (document.visibilityState === 'visible') resume() }
    window.addEventListener('online', resume)
    window.addEventListener('focus', resume)
    document.addEventListener('visibilitychange', onVisibility)
    void check()
    return () => {
      controller.abort()
      window.clearTimeout(timer)
      window.removeEventListener('online', resume)
      window.removeEventListener('focus', resume)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [requestId, attempt, historyKey, configurationError])

  const reset = () => setResult({ state: 'idle' })
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (configurationError || latest.current.pending || !question.trim()) return
    const current = getApiConfig()
    if (current.shopId !== config.shopId || current.baseUrl !== config.baseUrl) {
      setConnectionChanged(true)
      return
    }
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
    const pending: PendingMuseJob = {
      requestId: clientId(), startedAt: Date.now(), chatId: history.activeId,
      message, question: request, priorJobId: turns[turns.length - 1]?.jobId,
    }
    if (saveHistory({ ...latest.current, pending }, true)) {
      console.info('muse_job', { at: new Date(pending.startedAt).toISOString(), requestId: pending.requestId, status: 'saved' })
    }
  }

  return <section className="tool-placeholder ask-muse">
    <button className="back-link" onClick={onBack}>← Back to Today</button>
    <div className="tool-hero profit-tool"><span className="tool-glyph">✦</span><h2>Ask Muse</h2></div>
    <p className="muse-shop-scope"><strong>{isSample ? 'Sample shop' : 'Live shop'}</strong> <span>Shop ID {config.shopId || 'unavailable'}</span></p>
      <div className="muse-tabs" aria-label="Chat history">
        <button type="button" disabled={!!pending} onClick={() => {
          reset()
          saveHistory({ ...history, activeId: clientId() })
          setQuestion('')
        }}>New chat</button>
        {history.chats.length > 0 && <label>Chat history
          <select disabled={!!pending} value={history.activeId} onChange={event => {
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
      <form className="analysis-card" onSubmit={(event) => { submit(event) }}>
        {connectionChanged && <div className="muse-response muse-error" role="alert">
          <p>The active shop changed. Reload Street CEO before sending your question.</p>
          <button type="button" onClick={() => window.location.reload()}>Reload Street CEO</button>
        </div>}
        {configurationError && <div className="muse-response muse-error" role="alert"><h3>Shop connection needs attention</h3><p>{configurationError}</p><p>Return to Today and open Shop Connection. No question will be sent until the configuration is valid.</p></div>}
        <label htmlFor="muse-question">{turns.length ? 'Reply to Muse' : 'What would you like to ask?'}</label>
        <textarea id="muse-question" value={pending?.message ?? question} readOnly={!!pending} onChange={(event) => { reset(); setQuestion(event.target.value) }} rows={4} maxLength={1000} required aria-describedby="muse-period-note" />
        {!turns.length && <div className="muse-prompts">{prompts.map((prompt) => <button type="button" key={prompt} disabled={!!pending} onClick={() => { reset(); setQuestion(prompt) }}>{prompt}</button>)}</div>}
        <p id="muse-period-note" className="muted">{replyHint}</p>
        {pending && result.state === 'error' ? <button className="primary-action full" type="button" disabled={!!configurationError} onClick={() => setAttempt(attempt + 1)}>Check saved request</button>
          : <button className="primary-action full" disabled={!!configurationError || connectionChanged || !!pending || !question.trim()} type="submit">{pending ? 'Asking Muse…' : result.state === 'error' ? 'Retry question' : 'Send to Muse'}<span className="arrow">→</span></button>}
      </form>
      <div>
        {result.state === 'idle' && !turns.length && !pending && <p className="muse-idle">No answer requested yet. Only connected shop records will be used.</p>}
        {result.state === 'loading' && <div className="muse-response"><strong role="status">{result.label}</strong><p><span aria-hidden="true">{elapsed}s elapsed. </span>You can leave this screen and return to check your request.</p></div>}
        {result.state === 'error' && <div className="muse-response muse-error" role="alert"><h3>Could not get an answer</h3><p>{result.message}</p><p>Source period: unavailable. Data coverage: no answer received.</p></div>}
      </div>
  </section>
}

function MuseAnswer({ data }: { data: MuseResponse }) {
  const [exporting, setExporting] = useState(false)
  const [exportMessage, setExportMessage] = useState('')
  const document = data.partial === true ? null : data.document
  const sections = document?.sections ?? data.sections ?? []
  const exportPlan = async () => {
    if (!document || exporting) return
    setExporting(true)
    setExportMessage('')
    try {
      setExportMessage(await deliverPdf(buildMusePdf(document), 'Business plan'))
    } catch (error) {
      setExportMessage(error instanceof Error
        ? error.name === 'AbortError' ? 'Download cancelled.' : error.message
        : 'Could not download the business plan.')
    } finally {
      setExporting(false)
    }
  }
  const label = data.partial === true ? 'Investigation incomplete' : data.status === 'needs_data' ? 'More data needed' : data.status === 'unavailable' ? 'Muse unavailable' : 'Answer received'
  return <article className={`muse-response muse-answer muse-${data.status}`}>
    <span className="muse-status">{label}</span><h3>{data.title}</h3><p className="muse-answer-text">{data.answer}</p>
    {sections.length > 0 && <section className="muse-document" aria-label={document ? "Business plan" : "Investigation findings"}>
      {document && <div className="muse-document-header">
        <h4>{document.title}</h4>
        <button type="button" disabled={exporting} onClick={() => { void exportPlan() }}>
          {exporting ? 'Preparing PDF…' : 'Download PDF'}
        </button>
      </div>}
      {exportMessage && <p role="status">{exportMessage}</p>}
      {sections.map((section, index) => <section key={index} className="muse-document-section">
        <h4>{section.title}</h4>
        {section.body.split(/\n\s*\n/).map((paragraph, paragraphIndex) =>
          <p className="muse-answer-text" key={paragraphIndex}>{paragraph}</p>)}
        {!!section.evidence_ids?.length && <details>
          <summary>Section evidence</summary>
          <ul>{section.evidence_ids.map((id, idIndex) => <li key={idIndex}>{id}</li>)}</ul>
        </details>}
      </section>)}
    </section>}
    <details><summary>Answer details</summary><dl><div><dt>Source period</dt><dd>{museSourcePeriod(data.evidence_ids)}</dd></div><div><dt>Answer source</dt><dd>{data.source === 'meta' ? 'Meta AI using shop evidence' : data.source === 'repository' ? 'Connected shop records' : data.source === 'fallback' ? 'Service fallback — no model answer' : data.source}</dd></div><div><dt>Data coverage</dt><dd>{data.evidence_ids.length ? `${data.evidence_ids.length} evidence references supplied. Completeness has not been verified.` : 'No evidence references supplied. Coverage cannot be verified.'}</dd></div></dl>
    {data.missing_data.length > 0 && <div><h4>Missing data</h4><ul>{data.missing_data.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
    {data.evidence_ids.length > 0 && <details><summary>Evidence references</summary><ul>{data.evidence_ids.map((id, index) => <li key={index}>{id}</li>)}</ul></details>}
    </details>
  </article>
}
