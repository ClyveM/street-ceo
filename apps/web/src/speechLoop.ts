export type SpeechLoopState = 'starting' | 'listening' | 'waiting' | 'submitted' | 'background' | 'error' | 'stopped'
type Callbacks = { text(text: string, final: boolean): void; ready?(): void; error(message: string, fatal: boolean): void; end(): void; active?(value: boolean): void }
type Session = { start(): Promise<void>; stop(): Promise<void>; dispose(): Promise<void> }

/** One foreground recognition turn. A consumed final cannot dispatch twice.
 * The owner disposes this turn during TTS and creates a new one afterwards. */
export function startSpeechLoop(options: {
  open(callbacks: Callbacks): Promise<Session>
  text(text: string, final: boolean): boolean | Promise<boolean>
  state(state: SpeechLoopState): void
  error(message: string, fatal: boolean): void
  active?(value: boolean): void
  canStart?(): boolean
  schedule?(action: () => void): () => void
}) {
  let disposed = false, finished = false, foreground = true, starting = false
  let session: Session | undefined, cancelRestart: (() => void) | undefined
  const state = (value: SpeechLoopState) => { if (!disposed) options.state(value) }
  const schedule = options.schedule ?? ((action) => { const timer = setTimeout(action, 500); return () => clearTimeout(timer) })
  const restart = () => {
    cancelRestart?.()
    if (disposed || finished || !foreground || options.canStart?.() === false) return
    state('waiting')
    cancelRestart = schedule(() => { cancelRestart = undefined; void start() })
  }
  const fail = (message: string) => {
    if (disposed || finished) return
    finished = true; cancelRestart?.(); state('error'); options.error(message, true)
    void session?.stop().catch(() => {})
  }
  const start = async () => {
    if (disposed || finished || !foreground || options.canStart?.() === false || starting || !session) return
    starting = true; state('starting')
    try { await session.start() } catch (error) { fail(error instanceof Error ? error.message : 'Speech could not start.') }
    finally { starting = false }
  }
  const ready = options.open({
    ready() { if (!disposed && !finished && foreground && options.canStart?.() !== false) state('listening') },
    text(text, final) {
      if (disposed || finished || !foreground || options.canStart?.() === false) return
      let accepted: boolean | Promise<boolean>
      try { accepted = options.text(text, final) } catch (error) { options.error(error instanceof Error ? error.message : 'Answer handling failed.', false); restart(); return }
      if (accepted === true || typeof accepted === 'object') {
        finished = true; cancelRestart?.(); state('submitted'); void session?.stop().catch(() => {})
        if (typeof accepted === 'object') void accepted.catch((error) => { if (!disposed) options.error(error instanceof Error ? error.message : 'Answer handling failed.', false) }).finally(() => {
          // Busy/TTS normally replaces this loop. If React coalesces those
          // transitions, or the handler declines a request, do not stay deaf.
          if (!disposed) { finished = false; restart() }
        })
      }
    },
    error(message, fatal) { if (disposed || finished) return; if (fatal) fail(message); else { state('waiting'); options.error(message, false) } },
    end() { if (!disposed && !finished) restart() },
    active(value) { if (disposed) return; foreground = value; cancelRestart?.(); options.active?.(value); if (!value) state('background'); else if (!finished) restart() },
  }).then(async (value) => { session = value; if (disposed) await value.dispose(); else await start() }).catch((error) => fail(error instanceof Error ? error.message : 'Speech is unavailable.'))
  return {
    ready,
    fail,
    async dispose() { if (disposed) return; disposed = true; cancelRestart?.(); if (session) await session.dispose() },
  }
}
