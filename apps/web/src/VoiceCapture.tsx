import { voiceErrorSummary } from './voiceError'
import { HandsFreeVoice } from './HandsFreeVoice'
import { clientId } from './clientId'
import { speakPrompt, stopSpokenPrompt } from './speechRecognition'
import { isNativeAndroid } from './speechRecognition'
import { counterWakeTransition, readHandsFreePreference, storeHandsFreePreference } from './counterSession'
import { DEMO_BUILD_LABEL } from './buildInfo'
import { localShopGuidance, type ShopReachability } from './shopReachability'
import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { createPortal } from 'react-dom'
import { voiceClient } from './voice'
import { apoCommand, cancelPayment, catalogueMatchQuestion, confirmVoiceMatch, eligibleForQuickSale, matchAnswer, paymentCommand, QuickSaleError, tenderAnswer, type QuickReceipt, type QuickReversal, type SaleMode, type TenderAnswer, type TenderQuestion, type VoiceReview } from './quickSale'
import './quick-sale.css'

const money = (value: number) => `${Math.floor(value / 100)}.${String(value % 100).padStart(2, '0')}`
type Phase = 'idle' | 'review' | 'match' | 'clarification' | 'tender' | 'success' | 'error' | 'reversed'

export function VoiceCapture({ mode, blocked = false, connection = null, checkingConnection = false, onCheckConnection, onRequestBusy, onConfirmed, onUndo, onBusy }: { mode: SaleMode; blocked?: boolean; connection?: ShopReachability | null; checkingConnection?: boolean; onCheckConnection?(): void; onRequestBusy?(busy: boolean): void; onConfirmed: (receipt: QuickReceipt) => void; onUndo: () => Promise<void>; onBusy: (busy: boolean) => void }) {
  const [phase, setPhase] = useState<Phase>('idle'), [busy, setBusy] = useState(false), [listening, setListening] = useState(false)
  const [openingRecording, setOpeningRecording] = useState(false)
  const [command, setCommand] = useState(''), [transcript, setTranscript] = useState(''), [answer, setAnswer] = useState(''), [error, setError] = useState('')
  const [review, setReview] = useState<VoiceReview | null>(null), [question, setQuestion] = useState<TenderQuestion | null>(null), [receipt, setReceipt] = useState<QuickReceipt | null>(null), [reversal, setReversal] = useState<QuickReversal | null>(null)
  const [open, setOpen] = useState(false), [uncertain, setUncertain] = useState(false), [speech, setSpeech] = useState('')
  const [questionUnavailable, setQuestionUnavailable] = useState(false)
  const [latestReceipt, setLatestReceipt] = useState<QuickReceipt | null>(null)
  const [originalTranscript, setOriginalTranscript] = useState('')
  const [catalogueAnswer, setCatalogueAnswer] = useState('')
  const clarificationContext = useRef<string | undefined>(undefined)
  const isCatalogueReply = useRef(false)
  const mounted = useRef(true), lock = useRef(false), recorder = useRef<MediaRecorder | null>(null), stream = useRef<MediaStream | null>(null), chunks = useRef<Blob[]>([])
  const starting = useRef(false), held = useRef(false)
  const controller = useRef<AbortController | null>(null), operation = useRef<'interpret' | 'commit' | 'undo'>('interpret')
  const pending = useRef<{ review: VoiceReview; answer: TenderAnswer | null; key: string } | null>(null), undoKey = useRef('')
  const [handsFreeEnabled, setHandsFreeEnabled] = useState(() => { try { return readHandsFreePreference(localStorage, isNativeAndroid()) } catch { return isNativeAndroid() } })
  const [typingFocused, setTypingFocused] = useState(false)
  const counterRoot = useRef<HTMLElement>(null), wakeDismissed = useRef(false), handsFreeState = useRef(handsFreeEnabled)
  handsFreeState.current = handsFreeEnabled
  const promptVersion = useRef(0)
  const closeButton = useRef<HTMLButtonElement>(null)
  const prompt = (message: string) => {
    if (!mounted.current) return
    const version = ++promptVersion.current
    setSpeech('Requesting audio prompt…')
    // Allow recognition cleanup to run before output; native also stops its recognizer.
    setTimeout(() => {
      if (!mounted.current || version !== promptVersion.current) return
      setSpeech('Playing question…')
      void speakPrompt(message).then(() => { if (mounted.current && version === promptVersion.current) setSpeech('Response finished. Listening again…') }).catch(() => { if (mounted.current && version === promptVersion.current) setSpeech('Audio prompt unavailable. Read the visible response.') })
    }, 150)
  }
  useEffect(() => {
    mounted.current = true
    return () => { mounted.current = false; promptVersion.current++; controller.current?.abort(); if (recorder.current?.state === 'recording') recorder.current.stop(); stream.current?.getTracks().forEach((track) => track.stop()); void stopSpokenPrompt().catch(() => {}) }
  }, [])
  useEffect(() => { onBusy(busy || listening || openingRecording || uncertain || ['tender', 'match', 'clarification'].includes(phase)) }, [busy, listening, openingRecording, uncertain, phase, onBusy])
  useEffect(() => { onRequestBusy?.(busy); return () => onRequestBusy?.(false) }, [busy, onRequestBusy])
  useEffect(() => { if (open) { wakeDismissed.current = false; const previous = document.activeElement; closeButton.current?.focus(); return () => { if (wakeDismissed.current) { wakeDismissed.current = false; return }; if (previous instanceof HTMLElement) previous.focus() } } }, [open])
  const toggleHandsFree = () => { const next = !handsFreeEnabled; setHandsFreeEnabled(next); try { storeHandsFreePreference(localStorage, next) } catch { /* Session setting still applies. */ } }
  const startNextOnWake = () => {
    const current = { phase, open, enabled: handsFreeEnabled, hasReceipt: !!receipt, busy: busy || listening || openingRecording || speech === 'Playing question…' || speech === 'Requesting audio prompt…', blocked, uncertain }
    if (counterWakeTransition(current) === current) return
    wakeDismissed.current = open
    setOpen(false); setPhase('idle'); setReview(null); setReceipt(null); setQuestion(null); setQuestionUnavailable(false); setError(''); setAnswer(''); setCommand(''); setCatalogueAnswer(''); setTranscript(''); setOriginalTranscript(''); setTypingFocused(false)
    pending.current = null; clarificationContext.current = undefined; isCatalogueReply.current = false
    counterRoot.current?.focus({ preventScroll: true })
  }
  const closeCounterModal = () => {
    if (phase === 'success' && receipt && !uncertain) { wakeDismissed.current = true; setTypingFocused(false); counterRoot.current?.focus({ preventScroll: true }) }
    setOpen(false)
  }
  const run = async (action: (signal: AbortSignal) => Promise<void>) => {
    if (lock.current || blocked) return
    lock.current = true; setBusy(true); setError(''); controller.current = new AbortController()
    try { await action(controller.current.signal) }
    catch (failure) {
      if (!mounted.current) return
      const message = failure instanceof Error ? failure.message : 'Could not verify this sale.'
      const unknown = failure instanceof QuickSaleError && failure.uncertain && operation.current !== 'interpret'
      const unresolved = uncertain || unknown
      const unavailableQuestion = !unresolved && failure instanceof QuickSaleError && ['payment_question_connection', 'payment_question_response'].includes(failure.code)
      setUncertain((previous) => previous || unknown); setError(message); setOpen(operation.current !== 'interpret')
      setQuestionUnavailable(unavailableQuestion)
      setPhase(unavailableQuestion || question && !unresolved && operation.current === 'commit' ? 'tender' : 'error'); prompt(unavailableQuestion ? 'The payment question is unavailable. Reconnect to your shop, then say Retry, or say Cancel to discard this unpaid basket.' : voiceErrorSummary(message, unresolved))
    } finally { lock.current = false; if (mounted.current) setBusy(false) }
  }
  const commit = async (basket: VoiceReview, payment: TenderAnswer | null, signal: AbortSignal, key = `voice-sale-${basket.reviewId}`) => {
    operation.current = 'commit'; pending.current = { review: basket, answer: payment, key }
    let result
    try { result = await voiceClient.commit(basket, payment, key, signal) }
    catch (failure) {
      if (!uncertain && failure instanceof QuickSaleError && !failure.uncertain && failure.code === 'insufficient_cash') {
        pending.current = { review: basket, answer: { tender: 'cash' }, key }
        result = await voiceClient.commit(basket, { tender: 'cash' }, key, signal)
        setError(failure.message)
      } else throw failure
    }
    if (!mounted.current) return
    setReview(basket); setOpen(true); setQuestionUnavailable(false)
    if (result.kind === 'question') {
      if (uncertain) { setQuestion(null); setPhase('error'); setError('Recovery returned a payment question, not a saved receipt. The earlier sale outcome remains unverified. Keep this original request for investigation.'); prompt('No saved receipt was received. Keep the original request and check the shop connection before recovering again.'); return }
      setQuestion(result); setAnswer(''); setPhase('tender'); prompt(result.question)
    }
    else { setUncertain(false); setReceipt(result.sale); setLatestReceipt(result.sale); setQuestion(null); setPhase('success'); onConfirmed(result.sale); prompt(`Sale saved. Total ${money(result.sale.total_cents)}. Change ${money(result.sale.change_cents)}.${handsFreeState.current ? ' Say Apo for the next sale.' : ''}`) }
  }
  const process = async (raw: string, signal: AbortSignal, supplied?: VoiceReview, clarificationOf?: string, conversationReply = false) => {
    const parsed = apoCommand(raw)
    operation.current = 'interpret'
    clarificationContext.current = clarificationOf
    isCatalogueReply.current = conversationReply
    if (!clarificationOf) setOriginalTranscript(raw)
    setTranscript(raw); setReview(null); setReceipt(null); setQuestion(null); setQuestionUnavailable(false); setReversal(null); setOpen(false); setPhase('idle')
    const interpreted = supplied ?? await voiceClient.interpretTranscript(parsed.heardBody, `voice-review-${clientId()}`, signal, clarificationOf)
    if (!mounted.current) return
    setTranscript(raw); setReview(interpreted); setReceipt(null); setReversal(null); setQuestion(null); setUncertain(false); pending.current = null; setOpen(true)
    if (interpreted.status === 'needs_match_confirmation') { setCatalogueAnswer(''); setPhase('match'); prompt(interpreted.clarificationQuestion!); return }
    if (interpreted.status === 'needs_clarification') { setCatalogueAnswer(''); setPhase('clarification'); prompt(interpreted.clarificationQuestion!); return }
    if (conversationReply && interpreted.canCommit) { setCatalogueAnswer(''); setPhase('match'); prompt(catalogueMatchQuestion(interpreted)); return }
    if (mode === 'quick' && eligibleForQuickSale(parsed, interpreted)) await commit(interpreted, parsed.tender, signal)
    else {
      setPhase('review')
      if (!interpreted.canCommit) { setError('The basket is not fully resolved. Say exact quantities and catalogue names, or edit the typed command.'); prompt('Please clarify the products and quantities.') }
      else if (mode === 'quick') { setError('Quick Sale needs a complete Apo → quantities and products → Napo command. Complete it or review this basket explicitly.'); prompt('Please finish your complete sale command with Napo.') }
    }
  }
  const submitCommand = () => run(async (signal) => { await process(command, signal, undefined, clarificationContext.current, isCatalogueReply.current) })
  const submitCatalogueReply = (raw: string) => run(async (signal) => {
    const reply = paymentCommand(raw)
    if (uncertain) return
    const response = matchAnswer(reply)
    if (response === 'cancel' || phase === 'clarification' && cancelPayment(reply)) {
      pending.current = null; clarificationContext.current = undefined; setReview(null); setQuestion(null); setQuestionUnavailable(false); setOpen(false); setPhase('idle'); setTranscript(reply)
      prompt('Basket cancelled. No sale recorded. Say Apo for a new sale.'); return
    }
    if (phase === 'match') {
      if (response === 'no') { clarificationContext.current = undefined; setReview(null); setCatalogueAnswer(''); setPhase('clarification'); setTranscript(reply); prompt('Okay. Say the complete basket with quantities and catalogue product names, or Cancel.'); return }
      if (response !== 'yes' || !review) { prompt('Say Yes to accept these products, No to correct the basket, or Cancel.'); return }
      const confirmed = confirmVoiceMatch(review); setReview(confirmed); setTranscript(reply); await commit(confirmed, null, signal); return
    }
    if (phase === 'clarification') { setCommand(reply); await process(reply, signal, undefined, review?.status === 'needs_clarification' ? review.reviewId : undefined, true) }
  })
  const submitAnswer = (text = answer) => run(async (signal) => {
    if (!uncertain && phase === 'tender' && cancelPayment(text)) {
      pending.current = null; setReview(null); setQuestion(null); setQuestionUnavailable(false); setReceipt(null); setOpen(false); setPhase('idle'); setAnswer(''); setTranscript(text)
      prompt('Basket cancelled. No sale recorded. Say Apo for a new sale.'); return
    }
    if (!uncertain && phase === 'tender' && /^(retry|try again|recover)[.!?]*$/i.test(text.trim()) && pending.current) { await commit(pending.current.review, pending.current.answer, signal, pending.current.key); return }
    if (questionUnavailable) { setError('Restore the shop connection, then say Retry to retrieve the payment question, or Cancel.'); prompt('Please restore the shop connection, then say Retry or Cancel.'); return }
    const payment = tenderAnswer(text, question?.missing.includes('amount_received_cents'))
    if (!payment || !review) { setError('Please say Cash, Cash 100, or Bank.'); prompt('Cash or Bank? For cash, say the amount received.'); return }
    setTranscript(text); await commit(review, payment, signal)
  })
  const recover = () => run(async (signal) => {
    if (operation.current === 'undo' && receipt) { const result = await voiceClient.undo(receipt, undoKey.current, signal); setReversal(result); setPhase('reversed'); setUncertain(false); await onUndo() }
    else if (pending.current) await commit(pending.current.review, pending.current.answer, signal, pending.current.key)
  })
  const undo = () => run(async (signal) => {
    if (!receipt || reversal) return
    operation.current = 'undo'; undoKey.current = `voice-undo-${receipt.id}`
    const result = await voiceClient.undo(receipt, undoKey.current, signal)
    if (!mounted.current) return
    setReversal(result); setPhase('reversed'); setUncertain(false); prompt('Stock reversal recorded. Check any payment refund separately.')
    try { await onUndo() } catch { setError('Undo receipt received, but catalogue refresh failed. Reload stock before continuing.') }
  })
  const startRecording = async () => {
    if (busy || listening || uncertain || blocked || starting.current) return
    starting.current = true; held.current = true; setOpeningRecording(true)
    try {
      const local = ['localhost', '127.0.0.1'].includes(window.location.hostname)
      if (!window.isSecureContext && !local) throw new Error('Microphone access needs HTTPS or the APK. This HTTP LAN browser can use the typed command below.')
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') throw new Error('Microphone capture is unavailable. Use the typed command.')
      promptVersion.current++; await stopSpokenPrompt()
      const payment = phase === 'tender', live = await navigator.mediaDevices.getUserMedia({ audio: true })
      if (!mounted.current || !held.current) { live.getTracks().forEach((track) => track.stop()); return }
      stream.current = live; chunks.current = []; const capture = new MediaRecorder(live); recorder.current = capture
      capture.ondataavailable = (event) => { if (event.data.size) chunks.current.push(event.data) }
      capture.onstop = () => {
        live.getTracks().forEach((track) => track.stop()); stream.current = null; recorder.current = null
        if (!mounted.current) return
        setListening(false)
        void run(async (signal) => {
          operation.current = 'interpret'
          const result = await voiceClient.transcribe(new Blob(chunks.current, { type: capture.mimeType || 'audio/webm' }), `voice-audio-${clientId()}`, signal)
          if (payment) {
            const parsed = tenderAnswer(result.transcript, question?.missing.includes('amount_received_cents'))
            if (!parsed || !review) { setError('Please say Cash, Cash 100, or Bank.'); prompt('Please say Cash or Bank and the cash amount.'); return }
            setTranscript(result.transcript); await commit(review, parsed, signal)
          } else await process(result.transcript, signal, result)
        })
      }
      setError(''); setListening(true); capture.start()
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Microphone access was not granted. Use the typed command.') }
    finally { starting.current = false; if (mounted.current) setOpeningRecording(false) }
  }
  const stopRecording = () => { held.current = false; if (recorder.current?.state === 'recording') recorder.current.stop() }
  const talkButton = <button className="quick-talk" type="button" onPointerDown={() => { void startRecording() }} onPointerUp={stopRecording} onPointerCancel={stopRecording} onPointerLeave={stopRecording} onKeyDown={(event) => { if ((event.key === ' ' || event.key === 'Enter') && !event.repeat) { event.preventDefault(); void startRecording() } }} onKeyUp={(event) => { if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); stopRecording() } }} disabled={busy || uncertain} aria-label={phase === 'tender' ? 'Press and hold to answer payment question' : 'Press and hold to record an Apo sale'}>{listening ? 'Listening… release when finished' : busy ? 'Checking with shop…' : phase === 'tender' ? 'Hold to answer Cash or Bank' : 'Hold to say Apo → items → Napo'}</button>
  const modalKeys = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === 'Escape' && !busy && !listening) { event.preventDefault(); closeCounterModal() }
    if (event.key !== 'Tab') return
    const controls = [...event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),textarea:not(:disabled)')].filter((el) => el.getClientRects().length)
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls[controls.length - 1]?.focus() }
    else if (!event.shiftKey && document.activeElement === controls[controls.length - 1]) { event.preventDefault(); controls[0]?.focus() }
  }
  const total = receipt?.total_cents ?? question?.amount_due_cents
  const paid = phase === 'success' && !!receipt && !uncertain
  const entered = tenderAnswer(answer)
  const outputActive = speech === 'Playing question…' || speech === 'Requesting audio prompt…'
  const voicePaused = blocked || busy || listening || uncertain || typingFocused || outputActive
  const sourceLabel = review?.providerCalled === true ? 'Muse catalogue interpretation' : review?.resolutionSource === 'catalogue_parser' ? 'Exact catalogue match' : review?.resolutionSource === 'local_catalogue_proposal' ? 'Local catalogue proposal' : review?.resolutionSource === 'local_clarification' ? 'Catalogue clarification' : 'Source not supplied'
  const voiceToggle = <button type="button" className="voice-toggle" aria-pressed={handsFreeEnabled} aria-label={handsFreeEnabled ? 'Pause hands-free voice' : 'Resume hands-free voice'} onClick={toggleHandsFree}>{handsFreeEnabled ? 'Voice on · Pause' : 'Voice paused · Resume'}</button>
  const errorDisplay = error && <div className="voice-error"><p role="alert">{voiceErrorSummary(error, uncertain)}</p>{voiceErrorSummary(error, uncertain) !== error && <details><summary>More information</summary><p>{error}</p></details>}</div>
  const isTypingTarget = (target: EventTarget | null) => target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement
  const typingFocus = (event: { target: EventTarget | null }) => { if (isTypingTarget(event.target)) setTypingFocused(true) }
  const typingBlur = () => { queueMicrotask(() => { if (mounted.current) setTypingFocused(isTypingTarget(document.activeElement)) }) }
  return <section className="quick-sale counter-panel" ref={counterRoot} tabIndex={-1} aria-label="Apo voice counter" onFocusCapture={typingFocus} onBlurCapture={typingBlur}>
    <div className="counter-heading"><div><p className="eyebrow">APO AT YOUR COUNTER</p><h3>Ready when you are.</h3></div><span className="counter-wave" aria-hidden="true">▂ ▆ ▃ ▅</span></div>
    <HandsFreeVoice enabled={handsFreeEnabled} onEnabledChange={setHandsFreeEnabled} onToggle={toggleHandsFree} showControl={!open} onWake={startNextOnWake} replyPrompt={phase === 'match' ? 'Say Yes, No, or Cancel.' : phase === 'clarification' ? 'Answer the question, or say Cancel.' : undefined} expectingPayment={phase === 'tender'} paused={voicePaused} onCommand={(raw) => { if (phase === 'match' || phase === 'clarification') { void submitCatalogueReply(raw) } else if (phase === 'tender') { void submitAnswer(paymentCommand(raw)) } else { setCommand(raw); void run(async (signal) => { await process(raw, signal) }) } }} />
    {typingFocused && <p className="counter-hint">Voice waits while you type. It resumes when you leave the field.</p>}
    {(blocked || busy || uncertain || phase === 'tender' || phase === 'match' || phase === 'clarification' || phase === 'error') && <div className={`voice-step ${uncertain ? 'recovery-card' : ''}`} role="status"><strong>{blocked ? 'Checking your manual sale' : uncertain ? 'Check the original sale' : busy ? 'Checking your basket…' : phase === 'match' ? 'Did Apo hear that right?' : phase === 'clarification' ? 'One quick question' : phase === 'tender' ? 'How was it paid?' : 'Let’s try that again.'}</strong><p>{blocked ? 'Voice will wait.' : uncertain ? 'No saved receipt received. Restore the connection, then recover this same request. Do not enter a new sale.' : busy ? 'Please wait for your shop’s response.' : phase === 'match' && review ? catalogueMatchQuestion(review) : phase === 'clarification' ? review?.clarificationQuestion ?? 'Say the basket with quantities and product names, or Cancel.' : phase === 'tender' ? questionUnavailable ? 'Reconnect, then say Retry or Cancel.' : question?.question : voiceErrorSummary(error)}</p></div>}
    <details className="voice-fallback"><summary>Type instead</summary><label>Your command<textarea value={command} onChange={(event) => setCommand(event.target.value)} disabled={blocked || busy || listening || uncertain} rows={2} maxLength={1000} placeholder="Apo 1 Coke 2 Sugar Napo" /></label><button type="button" onClick={() => { void submitCommand() }} disabled={!command.trim() || blocked || busy || listening || uncertain}>Check basket</button><details><summary>Record a voice clip instead</summary>{talkButton}</details></details>
    {review && !open && <button type="button" className="counter-text-button" onClick={() => setOpen(true)}>{paid ? 'View receipt' : 'Open current basket'}</button>}
    {latestReceipt && !open && <details className="counter-last-sale"><summary>Last sale {money(latestReceipt.total_cents)} · change {money(latestReceipt.change_cents)}</summary><p>Received {money(latestReceipt.amount_received_cents)} · {latestReceipt.tender}</p><p>Receipt <code>{latestReceipt.id}</code></p></details>}
    {error && !open && <div>{errorDisplay}{uncertain ? <button type="button" disabled={busy || listening} onClick={() => { void recover() }}>Recover original request</button> : command.trim() && <button type="button" disabled={blocked || busy || listening} onClick={() => { void submitCommand() }}>Try again</button>}</div>}
    {open && createPortal(<div className="quick-modal-backdrop"><section className={`quick-modal counter-modal ${paid ? 'counter-paid' : ''}`} role="dialog" aria-modal="true" aria-label={paid ? 'Saved sale receipt' : 'Apo sale basket'} onKeyDown={modalKeys} onFocusCapture={typingFocus} onBlurCapture={typingBlur}>
      <header className="counter-modal-heading"><div className="counter-brand"><img src="/street-ceo-logo.png" alt="" /><div><p className="counter-kicker">{paid ? 'ALL SAVED' : uncertain ? 'NEEDS CHECKING' : 'STREET CEO'}</p><h2>{paid ? 'Sale saved.' : phase === 'reversed' ? 'Stock reversed' : phase === 'match' ? 'These products?' : phase === 'clarification' ? 'One quick question' : phase === 'tender' ? 'Payment' : 'Your basket'}</h2></div></div><button ref={closeButton} className="counter-close" disabled={busy || listening} onClick={closeCounterModal} aria-label="Close Apo sale basket">{paid ? 'Done' : 'Close'}</button></header>
      <div className="counter-voice-bar">{voiceToggle}<span role="status">{!handsFreeEnabled ? 'Typing is ready below.' : voicePaused ? busy ? 'Checking…' : outputActive ? 'Apo is speaking…' : typingFocused ? 'Waiting while you type…' : uncertain ? 'Recover the original request.' : 'Listening paused' : paid ? 'Ready for your next Apo.' : phase === 'match' ? 'Say Yes, No, or Cancel.' : phase === 'clarification' ? 'Answer, or say Cancel.' : phase === 'tender' ? 'Say Cash, Bank, or Cancel.' : 'Listening for Apo.'}</span></div>
      {(phase === 'match' || phase === 'clarification') && <section className="counter-question" aria-label="Catalogue clarification"><h3>{phase === 'match' && review ? catalogueMatchQuestion(review) : review?.clarificationQuestion ?? 'Say your basket with quantities and product names.'}</h3><p>{phase === 'match' ? 'Say Yes, No, or Cancel. Confirm the products before payment.' : 'Answer by voice, or Cancel. Apo won’t guess the quantity.'}</p><details><summary>Type instead</summary><div className="quick-actions">{phase === 'match' && <><button type="button" disabled={busy || uncertain} onClick={() => { void submitCatalogueReply('Yes') }}>Yes</button><button type="button" disabled={busy || uncertain} onClick={() => { void submitCatalogueReply('No') }}>No</button></>}<button type="button" disabled={busy || uncertain} onClick={() => { void submitCatalogueReply('Cancel') }}>Cancel basket</button></div><label>Your answer<input value={catalogueAnswer} onChange={(event) => setCatalogueAnswer(event.target.value)} maxLength={1000} disabled={busy || uncertain} /></label><button type="button" disabled={!catalogueAnswer.trim() || busy || uncertain} onClick={() => { void submitCatalogueReply(catalogueAnswer) }}>Send answer</button></details></section>}
      <ul className="quick-lines counter-items">{review?.lines.map((line) => <li key={line.product_id}><strong>{line.product_name}</strong><span>× {line.quantity}</span></li>)}</ul>
      {paid && receipt ? <section className="counter-payment-summary" aria-label="Saved receipt amounts"><dl><div><dt>Total</dt><dd>{money(receipt.total_cents)}</dd></div><div><dt>Tendered · {receipt.tender}</dt><dd>{money(receipt.amount_received_cents)}</dd></div></dl><div className="counter-change"><span>Change</span><strong>{money(receipt.change_cents)}</strong></div></section> : total !== undefined && <dl className="quick-totals"><dt>Total</dt><dd>{money(total)}</dd><dt>Tendered</dt><dd>{entered?.amount_received_cents !== undefined ? `${money(entered.amount_received_cents)} · preview` : 'Awaiting payment'}</dd></dl>}
      {paid && <p className="counter-next">{handsFreeEnabled ? 'Say Apo or Apple for the next sale.' : 'Voice is paused. Resume above, or type your next sale.'}</p>}
      {phase === 'tender' && <section className="counter-question"><h3>{questionUnavailable ? 'Payment question unavailable' : question?.question}</h3>{questionUnavailable && <><p>No complete payment was supplied. Reconnect, then say Retry or Cancel.</p><button type="button" disabled={busy || listening || uncertain} onClick={() => { void recover() }}>Retry payment question</button></>}<p>Just answer by voice. No need to say Apo again.</p><details><summary>Type instead</summary><label>Cash amount or Bank<input value={answer} onChange={(event) => setAnswer(event.target.value)} disabled={busy || listening || uncertain} placeholder="Cash 100" /></label><div className="quick-actions"><button disabled={busy || listening || uncertain || questionUnavailable} onClick={() => { void submitAnswer('Cash') }}>Cash</button><button disabled={busy || listening || uncertain || questionUnavailable} onClick={() => { void submitAnswer('Bank') }}>Bank</button><button disabled={!answer.trim() || busy || listening || uncertain} onClick={() => { void submitAnswer() }}>Send answer</button><button disabled={busy || listening || uncertain} onClick={() => { void submitAnswer('Cancel') }}>Cancel basket</button></div><details><summary>Record an answer instead</summary>{talkButton}</details></details></section>}
      {phase === 'review' && review?.canCommit && <button className="quick-primary" disabled={busy || listening} onClick={() => { void run(async (signal) => { await commit(review, apoCommand(command).tender, signal) }) }}>Confirm reviewed basket</button>}
      {uncertain && <div className="recovery-card" role="alert"><strong>No saved receipt received</strong><p>Keep this basket. Restore your shop connection, then recover the original request before entering another sale.</p><button className="quick-primary" disabled={busy || listening} onClick={() => { void recover() }}>Recover original request</button></div>}
      {errorDisplay}
      {reversal && <p role="status">Stock reversal recorded. Check any payment refund separately.</p>}
      <details className="counter-details"><summary>Details & help</summary>
        <p>Build <strong>{DEMO_BUILD_LABEL}</strong></p><p>Shop server: <code>{connection?.address ?? 'Not checked yet'}</code></p><p>{connection?.status === 'connected' ? 'Shop verified reachable' : connection ? 'Shop currently unavailable' : 'Shop connection not verified'}{connection ? ` · checked ${new Date(connection.checkedAt).toLocaleTimeString()}` : ''}</p>{connection?.status === 'unavailable' && <p>{localShopGuidance(connection.address)}</p>}{onCheckConnection && <button type="button" disabled={checkingConnection} onClick={onCheckConnection}>{checkingConnection ? 'Checking shop…' : 'Check shop connection'}</button>}
        {receipt && <><p>Receipt <code>{receipt.id}</code><br />{receipt.created_at}</p><p>Stock quantities are confirmed by the server. Bank is recorded tender, not verified settlement.</p>{!reversal && <><p>Undo restores stock only. A payment refund and financial-ledger reversal require separate verification.</p><button className="quick-undo" disabled={busy || listening || uncertain} onClick={() => { void undo() }}>Undo last sale</button></>}</>}
        {reversal && <p>Reversal <code>{reversal.reversal_id}</code> · audit <code>{reversal.audit_id}</code></p>}
        {pending.current && <><p>Basket review <code>{pending.current.review.reviewId}</code></p><p>Retry key <code>{pending.current.key}</code></p></>}
        <p>Original heard command: {originalTranscript || 'Not supplied'}</p>{transcript && transcript !== originalTranscript && <p>Latest answer: {transcript}</p>}{review && <p>Interpretation: {sourceLabel}<br />{review.transcript}</p>}
      </details>
    </section></div>, document.body)}
  </section>
}
