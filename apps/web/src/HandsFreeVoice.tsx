import { useEffect, useRef, useState } from 'react'
import { isNativeAndroid, openSpeech } from './speechRecognition'
import { catalogueReplyEvent, conflictingAliases, PRONUNCIATION_KEY, readPronunciation, validAlias, WakeCommand, words } from './wakePhrase'
import { endDayCommand } from './reportsClose'
import { startSpeechLoop, type SpeechLoopState } from './speechLoop'
import { readHandsFreePreference, storeHandsFreePreference } from './counterSession'

export function HandsFreeVoice({ paused, stopRequest = 0, setupOnly = false, expectingPayment = false, replyPrompt, catalogueClarification = false, replyTurn = 0, onListeningState, enabled: controlledEnabled, onEnabledChange, onToggle, onWake, showControl = true, onCommand }: { paused: boolean; stopRequest?: number; setupOnly?: boolean; expectingPayment?: boolean; replyPrompt?: string; catalogueClarification?: boolean; replyTurn?: number; onListeningState?(value: { state: SpeechLoopState; message: string; capturing?: boolean }): void; enabled?: boolean; onEnabledChange?(value: boolean): void; onToggle?(): void; onWake?(): void; showControl?: boolean; onCommand(command: string): void | Promise<void> }) {
  const [localEnabled, setLocalEnabled] = useState(() => { try { return !setupOnly && readHandsFreePreference(localStorage, isNativeAndroid()) } catch { return !setupOnly && isNativeAndroid() } }), [visible, setVisible] = useState(!document.hidden)
  const enabled = controlledEnabled ?? localEnabled
  const setEnabled = (value: boolean) => { if (onEnabledChange) onEnabledChange(value); else setLocalEnabled(value) }
  const [pronunciation, setPronunciation] = useState(() => { try { return readPronunciation(localStorage) } catch { return { apo: 'apo', napo: 'napo' } } })
  const [learning, setLearning] = useState<'apo' | 'napo' | null>(null), [candidate, setCandidate] = useState('')
  const [status, setStatus] = useState('Hands-free is off.'), [error, setError] = useState('')
  const [recognitionState, setRecognitionState] = useState<SpeechLoopState>('stopped')
  const stateObserver = useRef(onListeningState); stateObserver.current = onListeningState
  const machine = useRef(new WakeCommand()), command = useRef(onCommand), latest = useRef(pronunciation), lastStop = useRef(stopRequest), wake = useRef(onWake)
  command.current = onCommand; latest.current = pronunciation; wake.current = onWake
  useEffect(() => { if (enabled) setError('') }, [enabled])
  useEffect(() => { if (lastStop.current !== stopRequest) { lastStop.current = stopRequest; setEnabled(false); setLearning(null); machine.current.reset() } }, [stopRequest])
  useEffect(() => { const changed = () => { setVisible(!document.hidden); machine.current.reset() }; document.addEventListener('visibilitychange', changed); return () => document.removeEventListener('visibilitychange', changed) }, [])
  useEffect(() => {
    if ((!enabled && !learning) || paused || !visible) { machine.current.reset(); return }
    let finished = false
    const loop = startSpeechLoop({
      open: openSpeech,
      canStart: () => !document.hidden,
      state(value) { setRecognitionState(value); if (value === 'listening') setStatus(learning ? `Say ${learning === 'apo' ? 'Apo' : 'Napo'} once, then pause.` : catalogueClarification && machine.current.awake ? `Retry command: ${machine.current.body.trim() || '(waiting for products)'} · say Napo to finish.` : replyPrompt ?? (expectingPayment ? 'Listening for Cash and amount, or Bank…' : machine.current.awake ? 'Command listening · say Napo to finish.' : 'Waiting for Apo…')) },
      active() { machine.current.reset() },
      text(text, final) {
        if (!final) { setStatus(catalogueClarification && machine.current.awake ? `Retry command: ${machine.current.body}${text} · say Napo to finish.` : learning ? `Heard: ${text}` : replyPrompt || expectingPayment ? `Answer: ${text}` : machine.current.awake ? `Command: ${machine.current.body}${text}` : `Waiting for Apo · heard: ${text}`); return false }
        if (learning) { finished = true; setCandidate(words(text)); setStatus('Check what the recognizer heard before saving.'); return true }
        if (catalogueClarification && text.trim()) { const reply=catalogueReplyEvent(machine.current,text,latest.current); if(reply.capturing) { setStatus(`Retry command: ${machine.current.body.trim() || '(waiting for products)'} · say Napo to finish.`); return false }; if(reply.command) { finished=true; return Promise.resolve(command.current(reply.command)).then(()=>true) }; return false }
        if ((expectingPayment || replyPrompt) && text.trim()) { finished = true; return Promise.resolve(command.current(text)).then(() => true) }
        if (!machine.current.awake && endDayCommand(text)) return Promise.resolve(command.current(text)).then(() => true)
        const result = machine.current.acceptEvent(text, latest.current)
        if (result.woke) wake.current?.()
        setStatus(machine.current.awake ? `Command: ${machine.current.body} · say Napo to finish.` : 'Waiting for Apo…')
        if (result.command) { finished = true; return Promise.resolve(command.current(result.command)).then(() => true) }
        return false
      },
      error(message, fatal) { if (fatal) { finished = true; setError(message); setEnabled(false); setLearning(null); machine.current.reset() } else setStatus('No phrase heard. Waiting again…') },
    })
    const setupStart = Date.now()
    const timeout = setInterval(() => { if (learning && !finished && Date.now() - setupStart > 15000) loop.fail('No pronunciation captured. Try again and say just the requested word.'); if (machine.current.awake && Date.now() - machine.current.startedAt > 20000) { machine.current.reset(); setStatus(catalogueClarification ? 'Retry timed out. Answer the question directly, or repeat a full Apo command ending with Napo.' : 'Command timed out without Napo. Say Apo to start again.') } }, 1000)
    return () => { clearInterval(timeout); machine.current.reset(); void loop.dispose().catch(() => {}) }
  }, [enabled, learning, paused, visible, expectingPayment, replyPrompt, catalogueClarification, replyTurn])
  useEffect(() => {
    const state = !enabled && !learning || paused ? 'stopped' : !visible ? 'background' : recognitionState
    const message = !enabled && !learning ? error || 'Microphone is off. Resume voice or type below.' : !visible ? 'Paused in the background.' : paused ? 'Listening paused while processing, speaking, or typing.' : recognitionState === 'starting' ? 'Starting microphone… Wait for Listening.' : recognitionState === 'waiting' ? 'Microphone restarting…' : recognitionState === 'submitted' ? 'Answer captured. Checking…' : recognitionState === 'error' ? error : status
    stateObserver.current?.({ state, message, capturing: catalogueClarification && machine.current.awake })
  }, [enabled, learning, paused, visible, recognitionState, status, error, catalogueClarification])

  const teach = (word: 'apo' | 'napo') => { setEnabled(false); setError(''); setCandidate(''); setLearning(word) }
  const save = () => {
    if (!learning || !validAlias(candidate)) { setError('Say a short phrase of one to three words, without a sale command.'); return }
    const clean = words(candidate), other = learning === 'apo' ? pronunciation.napo : pronunciation.apo
    if (clean === other || clean === (learning === 'apo' ? 'napo' : 'apo')) { setError('Apo and Napo must sound different to the recognizer. Please try again.'); return }
    const next = { ...pronunciation, [learning]: clean }
    if (conflictingAliases(next)) { setError('Choose distinct pronunciations: neither phrase can begin with the other.'); return }
    try { localStorage.setItem(PRONUNCIATION_KEY, JSON.stringify(next)); setPronunciation(next); setLearning(null); setCandidate(''); setStatus('Pronunciation saved on this device. Enable hands-free to try it.') } catch { setError('Could not save pronunciation on this device.') }
  }
  const statusText = !paused && enabled && recognitionState === 'starting' ? 'Starting microphone…' : !paused && enabled && recognitionState === 'waiting' ? 'Microphone restarting…' : !enabled && !learning ? 'Hands-free is off.' : !visible ? 'Paused in the background.' : paused ? 'Paused while processing or playing audio.' : status
  const stage = !enabled && !learning ? 'off' : !visible ? 'background' : paused ? 'paused' : replyPrompt ? 'reply' : expectingPayment ? 'payment' : machine.current.awake ? 'capturing' : learning ? 'setup' : 'waiting'
  const headline = !paused && enabled && !['listening'].includes(recognitionState) ? recognitionState === 'submitted' ? 'Answer captured' : 'Microphone starting' : { off: 'Microphone is off', background: 'Listening paused', paused: 'Apo is responding', reply: 'Listening for your answer', payment: 'Your payment answer', capturing: 'Listening to your products', setup: 'Pronunciation setup', waiting: 'Ready — say Apo' }[stage]
  const feedback = <><div className="voice-live-state" data-stage={stage} role="status"><span className="voice-indicator" aria-hidden="true" /><div><strong>{headline}</strong><p className="voice-status">{statusText}</p></div></div>{error && <p role="alert" className="cost-error">{error}</p>}</>
  if (!setupOnly) return <section className="hands-free" aria-label="Hands-free voice">{showControl && <button type="button" className="voice-toggle" aria-label={enabled ? 'Pause hands-free voice' : 'Resume hands-free voice'} aria-pressed={enabled} onClick={() => { setError(''); machine.current.reset(); if (onToggle) onToggle(); else { setEnabled(!enabled); try { storeHandsFreePreference(localStorage, !enabled) } catch { /* Session preference still applies. */ } } }}>{enabled ? 'Voice on · Pause' : 'Voice paused · Resume'}</button>}{feedback}</section>
  return <section className="pronunciation-setup" aria-label="Voice pronunciation setup"><h3>Your Apo / Napo pronunciation</h3><p>Say each word naturally, then check what your phone heard.</p><div className="quick-actions"><button type="button" disabled={paused || !!learning} onClick={() => teach('apo')}>Pronounce Apo</button><button type="button" disabled={paused || !!learning} onClick={() => teach('napo')}>Pronounce Napo</button></div><dl className="pronunciation-saved"><dt>Apo starts listening</dt><dd>{pronunciation.apo}</dd><dt>Napo ends the command</dt><dd>{pronunciation.napo}</dd></dl>{learning && <section className="pronunciation-capture"><p>Say <strong>{learning === 'apo' ? 'Apo' : 'Napo'}</strong> once and pause.</p>{candidate && <><label>Phone heard<input value={candidate} maxLength={30} onChange={(event) => setCandidate(event.target.value)} /></label><button type="button" onClick={save}>Save pronunciation</button><button type="button" onClick={() => { setLearning(null); setCandidate(''); setTimeout(() => teach(learning), 0) }}>Try again</button></>}<button type="button" onClick={() => { setLearning(null); setCandidate('') }}>Cancel</button></section>}{feedback}<button type="button" className="back-link" disabled={!!learning} onClick={() => { try { localStorage.removeItem(PRONUNCIATION_KEY); setPronunciation({ apo: 'apo', napo: 'napo' }); machine.current.reset() } catch { setError('Could not reset saved pronunciation.') } }}>Reset pronunciation</button><details><summary>How this works</summary><p>Saved only on this device as personal phrase matches, not voice-model training. Setup cannot record a sale. A final “nabo” or “napple” is also accepted as Napo. If Napo is repeatedly misheard, use Pronounce Napo above and check the phrase before saving. Extra product words are kept for clarification. Speech recognition may use your phone’s online speech provider. Hands-free works while Sell is open.</p></details></section>
}
export function VoicePronunciation() { return <HandsFreeVoice paused={false} setupOnly onCommand={() => {}} /> }
