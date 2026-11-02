export type Pronunciation = { apo: string; napo: string }
export const PRONUNCIATION_KEY = 'street-ceo-pronunciation-v1'
export const words = (value: string) => value.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').trim().replace(/\s+/g, ' ')
export function validAlias(value: string) { const clean = words(value); return /^[a-z]+(?: [a-z]+){0,2}$/.test(clean) && clean.length <= 30 }
export function conflictingAliases(value: Pronunciation) {
  const starts = ['apo', 'apple', value.apo].map(words), ends = ['napo', 'nabo', 'napple', value.napo].map(words)
  return starts.some((start) => ends.some((end) => start === end || start.startsWith(`${end} `) || end.startsWith(`${start} `)))
}
export function readPronunciation(storage?: Pick<Storage, 'getItem'>): Pronunciation {
  try { const value = JSON.parse(storage?.getItem(PRONUNCIATION_KEY) ?? '{}'); const result = { apo: validAlias(value.apo ?? '') ? words(value.apo) : 'apo', napo: validAlias(value.napo ?? '') ? words(value.napo) : 'napo' }; return conflictingAliases(result) ? { apo: 'apo', napo: 'napo' } : result } catch { return { apo: 'apo', napo: 'napo' } }
}
export class WakeCommand {
  body = ''
  awake = false
  startedAt = 0
  reset() { this.body = ''; this.awake = false; this.startedAt = 0 }
  accept(text: string, pronunciation: Pronunciation, now = Date.now()): string | null {
    return this.acceptEvent(text, pronunciation, now).command
  }
  acceptEvent(text: string, pronunciation: Pronunciation, now = Date.now()): { command: string | null; woke: boolean } {
    let woke = false
    if (this.awake && now - this.startedAt > 20000) this.reset()
    const tokens = text.toLowerCase().replace(/(\d)\.(?=\d)/g, '$1decimalmark').replace(/[^a-z0-9\s-]/g, ' ').replace(/decimalmark/g, '.').trim().split(/\s+/).filter(Boolean)
    const starts = [...new Set(['apo', pronunciation.apo])].map((s) => s.split(' ')).sort((a,b)=>b.length-a.length)
    const ends = [...new Set(['napo', 'nabo', 'napple', pronunciation.napo])].map((s) => s.split(' ')).sort((a,b)=>b.length-a.length)
    const match = (at: number, choices: string[][]) => choices.find((part) => part.every((token, i) => tokens[at + i] === token))
    for (let i = 0; i < tokens.length; i++) {
      const end = match(i, ends), start = match(i, starts)
      if (!this.awake) { if (start || i === 0 && tokens[i] === 'apple') { this.awake = true; this.startedAt = now; woke = true; i += start ? start.length - 1 : 0 } continue }
      if (end && i + end.length === tokens.length) { const body = this.body.trim(); this.reset(); return { command: body ? `Apo ${body} Napo` : null, woke } }
      if (start && start[0] !== 'apple') { this.body = ''; this.startedAt = now; i += start.length - 1; continue }
      this.body += `${tokens[i]} `
      if (this.body.length > 900) { this.reset(); return { command: null, woke } }
    }
    return { command: null, woke }
  }
}


/** Catalogue questions accept plain answers, or a deliberately framed retry.
 * A leading wake phrase starts a retry; ordinary/internal apple stays a product
 * word. Incomplete retries remain in this machine across final ASR segments. */
export function catalogueReplyEvent(machine: WakeCommand, text: string, pronunciation: Pronunciation, now = Date.now()): { command: string | null; capturing: boolean } {
  const clean = words(text)
  const legacy = /^apo\b([\s\S]+?)\bapo[.!?]*$/i.exec(text.trim())
  if (legacy && legacy[1].trim()) { machine.reset(); return { command: `Apo ${legacy[1].trim()} Napo`, capturing: false } }
  if (machine.awake && now-machine.startedAt>20000) machine.reset()
  if (/^(cancel|cancel sale|cancel basket)$/.test(clean)) { machine.reset(); return { command: text, capturing: false } }
  const starts = ['apo', 'apple', pronunciation.apo].map(words)
  const startsRetry = starts.some(start => clean === start || clean.startsWith(`${start} `))
  if (!machine.awake && !startsRetry) return { command: text.trim() || null, capturing: false }
  const result = machine.acceptEvent(text, pronunciation, now)
  return { command: result.command, capturing: machine.awake }
}
