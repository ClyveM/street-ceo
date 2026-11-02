type Handle = { remove(): Promise<void> }
type Plugin = { start(options: { language: string }): Promise<void>; stop(): Promise<void>; speak(options: { text: string }): Promise<void>; stopSpeaking(): Promise<void>; addListener(name: string, callback: (event: { text?: string; final?: boolean; message?: string; code?: number }) => void): Promise<Handle> }
type Recognition = { lang: string; continuous: boolean; interimResults: boolean; onresult: ((event: { resultIndex: number; results: { length: number; [index: number]: { isFinal: boolean; 0: { transcript: string } } } }) => void) | null; onerror: ((event: { error: string }) => void) | null; onend: (() => void) | null; start(): void; abort(): void }
type SpeechWindow = Window & { Capacitor?: { getPlatform?(): string; registerPlugin?(name: string): Plugin; Plugins?: { ApoSpeech?: Plugin } }; SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition }
let nativeOwner: symbol | null = null, nativeRunning = false
let nativeQueue: Promise<unknown> = Promise.resolve()
function queueNative(action: () => Promise<void>) {
  const next = nativeQueue.then(action, action)
  nativeQueue = next.catch(() => {})
  return next
}
export function isNativeAndroid() { return (window as SpeechWindow).Capacitor?.getPlatform?.() === 'android' }
export function nativeSpeech() {
  const cap = (window as SpeechWindow).Capacitor
  return cap?.getPlatform?.() === 'android' ? cap.registerPlugin?.('ApoSpeech') ?? cap.Plugins?.ApoSpeech : undefined
}
export async function stopSpokenPrompt() {
  if (isNativeAndroid()) await nativeSpeech()?.stopSpeaking()
  else window.speechSynthesis?.cancel()
}

/** Resolves only when output ends so recognition cannot capture its own prompt. */
export async function speakPrompt(text: string): Promise<void> {
  if (isNativeAndroid()) {
    const plugin = nativeSpeech()
    if (!plugin) throw new Error('Spoken responses are unavailable in this APK.')
    await queueNative(async () => { nativeRunning = false; await plugin.speak({ text }) })
    return
  }
  if (!window.speechSynthesis || typeof SpeechSynthesisUtterance === 'undefined') throw new Error('Spoken responses are unavailable here.')
  await new Promise<void>((resolve, reject) => {
    window.speechSynthesis.cancel()
    const spoken = new SpeechSynthesisUtterance(text)
    spoken.onend = () => resolve()
    spoken.onerror = () => reject(new Error('The spoken response could not play.'))
    window.speechSynthesis.speak(spoken)
  })
}
export async function openSpeech(callbacks: { text(text: string, final: boolean): void; error(message: string, fatal: boolean): void; end(): void; active?(value: boolean): void }) {
  const win = window as SpeechWindow, cap = win.Capacitor
  if (cap?.getPlatform?.() === 'android') {
    const plugin = nativeSpeech()
    if (!plugin) throw new Error('Speech recognition is unavailable in this APK. Install the latest build.')
    const handles: Handle[] = [], owner = Symbol('speech session')
    let disposed = false
    const owned = () => !disposed && nativeOwner === owner
    const stop = () => queueNative(async () => { if (nativeOwner === owner) { nativeOwner = null; nativeRunning = false; await plugin.stop() } })
    try {
      handles.push(await plugin.addListener('speech', (event) => { if (owned()) callbacks.text(event.text ?? '', !!event.final) }))
      handles.push(await plugin.addListener('speechError', (event) => { if (owned()) { nativeRunning = false; callbacks.error(event.message ?? 'Speech recognition failed.', ![6, 7, 8].includes(event.code ?? -1)) } }))
      handles.push(await plugin.addListener('speechEnd', () => { if (owned()) { nativeRunning = false; callbacks.end() } }))
      handles.push(await plugin.addListener('speechPaused', () => { if (owned()) { nativeRunning = false; callbacks.active?.(false) } }))
      handles.push(await plugin.addListener('speechResumed', () => { if (owned()) callbacks.active?.(true) }))
      return {
        start: () => queueNative(async () => {
          if (disposed || nativeOwner === owner && nativeRunning) return
          if (nativeOwner !== null && nativeOwner !== owner) { nativeOwner = null; nativeRunning = false; await plugin.stop() }
          nativeOwner = owner
          try { await plugin.start({ language: 'en-ZA' }); nativeRunning = true }
          catch (error) { if (nativeOwner === owner) { nativeOwner = null; nativeRunning = false }; throw error }
        }),
        stop,
        dispose: async () => { disposed = true; await stop(); await Promise.all(handles.map((h) => h.remove())) },
      }
    } catch (error) { await Promise.all(handles.map((h) => h.remove())); throw error }
  }
  const Constructor = win.SpeechRecognition ?? win.webkitSpeechRecognition
  if (!Constructor) throw new Error('Hands-free recognition is unavailable here. Use the Android APK or the recording fallback.')
  const recognition = new Constructor()
  recognition.lang = 'en-ZA'; recognition.continuous = false; recognition.interimResults = true
  recognition.onresult = (event) => { for (let i = event.resultIndex; i < event.results.length; i++) callbacks.text(event.results[i][0].transcript, event.results[i].isFinal) }
  recognition.onerror = (event) => callbacks.error(`Speech recognition: ${event.error}`, !['no-speech', 'aborted'].includes(event.error))
  recognition.onend = callbacks.end
  return { start: async () => { recognition.start() }, stop: async () => { recognition.abort() }, dispose: async () => { recognition.onresult = null; recognition.onerror = null; recognition.onend = null; recognition.abort() } }
}
