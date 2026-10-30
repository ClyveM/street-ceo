import { useRef, useState } from 'react'
import { voiceClient } from './voice'

type CaptureState = 'idle' | 'listening' | 'transcribing' | 'confirmation' | 'success' | 'failure'

export function VoiceCapture({ onConfirmed }: { onConfirmed: (command: string) => void }) {
  const [state, setState] = useState<CaptureState>('idle')
  const [transcript, setTranscript] = useState('')
  const [textCommand, setTextCommand] = useState('')
  const [error, setError] = useState('')
  const recorder = useRef<MediaRecorder | null>(null)
  const stream = useRef<MediaStream | null>(null)
  const chunks = useRef<Blob[]>([])

  const startListening = async () => {
    if (state === 'listening' || state === 'transcribing') return
    setError('')
    setTranscript('')
    try {
      const localHost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      if (!window.isSecureContext && !localHost) throw new Error('Microphone access requires HTTPS. This local network URL is HTTP; use Chrome/Edge on the host at http://localhost:5173 or enable HTTPS for phone access.')
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) throw new Error('This browser does not expose microphone capture. Open the app in Chrome or Edge and use the text fallback here.')
      stream.current = await navigator.mediaDevices.getUserMedia({ audio: true })
      chunks.current = []
      const nextRecorder = new MediaRecorder(stream.current)
      recorder.current = nextRecorder
      nextRecorder.ondataavailable = (event) => { if (event.data.size) chunks.current.push(event.data) }
      nextRecorder.onstop = () => { void finishRecording(nextRecorder) }
      nextRecorder.start()
      setState('listening')
    } catch (captureError) {
      const name = captureError instanceof DOMException ? captureError.name : ''
      const message = name === 'NotAllowedError' ? 'Microphone permission was blocked. Allow microphone access in the browser address-bar settings and try again.' : name === 'NotFoundError' ? 'No microphone was found. Connect a microphone or use the text fallback.' : captureError instanceof Error ? captureError.message : 'Microphone permission was not granted.'
      setError(message)
      setState('failure')
    }
  }

  const finishRecording = async (finishedRecorder: MediaRecorder) => {
    stream.current?.getTracks().forEach((track) => track.stop())
    stream.current = null
    recorder.current = null
    if (!chunks.current.length) { setError('No audio was captured. Try holding the button while you speak.'); setState('failure'); return }
    setState('transcribing')
    try {
      const result = await voiceClient.transcribe(new Blob(chunks.current, { type: finishedRecorder.mimeType || 'audio/webm' }))
      setTranscript(result.transcript)
      setState('confirmation')
    } catch (transcriptionError) {
      setError(transcriptionError instanceof Error ? transcriptionError.message : 'Transcription failed. Use the text fallback.')
      setState('failure')
    }
  }

  const stopListening = () => { if (recorder.current?.state === 'recording') recorder.current.stop() }
  const confirm = (command: string) => { const clean = command.trim(); if (!clean) return; onConfirmed(clean); setTranscript(clean); setState('success') }
  const useTextFallback = () => { if (!textCommand.trim()) return; setTranscript(textCommand.trim()); setState('confirmation') }
  const reset = () => { setState('idle'); setError(''); setTranscript(''); setTextCommand('') }

  return <section className={`voice-capture voice-${state}`} aria-labelledby="voice-title">
    <div className="voice-heading"><div><p className="eyebrow">APO / NAPO VOICE INPUT</p><h3 id="voice-title">Say it, then check it.</h3></div><span className="voice-boundary">Provider-neutral</span></div>
    <p className="voice-help">Press and hold to speak a short command. Release to transcribe. Nothing posts until you confirm.</p>
    <button className="talk-button" onPointerDown={() => { void startListening() }} onPointerUp={stopListening} onPointerCancel={stopListening} onPointerLeave={() => { if (state === 'listening') stopListening() }} onKeyDown={(event) => { if ((event.key === ' ' || event.key === 'Enter') && state !== 'listening') { event.preventDefault(); void startListening() } }} onKeyUp={(event) => { if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); stopListening() } }} aria-label="Press and hold to record a voice command" disabled={state === 'transcribing'}><span className="mic-icon">{state === 'listening' ? '●' : '♩'}</span><span>{state === 'listening' ? 'Listening… release to finish' : state === 'transcribing' ? 'Transcribing…' : 'Press and hold to talk'}</span></button>
    <div className="voice-state" role="status" aria-live="polite">{state === 'idle' && <span>Ready · microphone stays off until you press the button.</span>}{state === 'listening' && <span className="state-listening">Listening · speak your short command now.</span>}{state === 'transcribing' && <span>Transcribing · sending audio only to the configured local backend.</span>}{state === 'confirmation' && <><strong>Confirm this command</strong><blockquote>{transcript}</blockquote><div className="voice-actions"><button className="voice-confirm" onClick={() => confirm(transcript)}>Confirm command</button><button className="voice-secondary" onClick={reset}>Try again</button></div></>}{state === 'success' && <><strong>Confirmed for sale review</strong><span>“{transcript}” · no sale was posted by voice.</span><button className="voice-secondary" onClick={reset}>Record another</button></>}{state === 'failure' && <><strong>Voice input unavailable</strong><span>{error}</span><label className="text-command"><span>Text fallback</span><textarea value={textCommand} onChange={(event) => setTextCommand(event.target.value)} placeholder="Type: 2 Coca-Cola for cash" rows={2} /></label><div className="voice-actions"><button className="voice-confirm" onClick={useTextFallback} disabled={!textCommand.trim()}>Review text command</button><button className="voice-secondary" onClick={reset}>Dismiss</button></div></>}</div>
    <small className="voice-privacy">Browser microphone → configured backend boundary. No provider key is stored in this app.</small>
  </section>
}
