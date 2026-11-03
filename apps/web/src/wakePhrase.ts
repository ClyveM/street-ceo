export type Pronunciation = { apo: string; napo: string; apoAliases?: string[]; napoAliases?: string[] }
export type PronunciationWord = 'apo' | 'napo'
export const PRONUNCIATION_EVENT = 'street-ceo-pronunciation-changed'
export const PRONUNCIATION_SAMPLE_COUNT = 5
const MAX_SAVED_ALIASES = 10
export function apoAliases(value: Pronunciation): string[] {
  return [...new Set(['apo', 'apple', value.apo, ...(value.apoAliases ?? [])].filter(validAlias).map(words))]
}
export function napoAliases(value: Pronunciation): string[] {
  return [...new Set(['napo', 'nabo', 'napple', value.napo, ...(value.napoAliases ?? [])].filter(validAlias).map(words))]
}
export function addPronunciationSamples(value: Pronunciation, word: PronunciationWord, samples: string[]): Pronunciation {
  if (samples.length !== PRONUNCIATION_SAMPLE_COUNT || samples.some(sample => !validAlias(sample))) {
    throw new Error('Review five short pronunciation samples before saving.')
  }
  const key = word === 'apo' ? 'apoAliases' : 'napoAliases'
  const aliases = [...new Set([...(value[key] ?? []), ...samples.map(words)])]
  if (aliases.length > MAX_SAVED_ALIASES) throw new Error('Ten saved variations already. Reset pronunciation to replace them.')
  const next = { ...value, [key]: aliases }
  if (conflictingAliases(next)) throw new Error('Apo and Napo must be distinct: neither phrase can begin with the other.')
  return next
}
export function addNapoSamples(value: Pronunciation, samples: string[]): Pronunciation {
  return addPronunciationSamples(value, 'napo', samples)
}
export const PRONUNCIATION_KEY = 'street-ceo-pronunciation-v1'
export const words = (value: string) => value.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').trim().replace(/\s+/g, ' ')
export function validAlias(value: string) { const clean = words(value); return /^[a-z]+(?: [a-z]+){0,2}$/.test(clean) && clean.length <= 30 }
export function conflictingAliases(value: Pronunciation) {
  const starts = apoAliases(value), ends = napoAliases(value)
  return starts.some((start) => ends.some((end) => start === end || start.startsWith(`${end} `) || end.startsWith(`${start} `)))
}
export function readPronunciation(storage?: Pick<Storage, 'getItem'>): Pronunciation {
  try {
    const value = JSON.parse(storage?.getItem(PRONUNCIATION_KEY) ?? '{}')
    const result: Pronunciation = {
      apo: typeof value.apo === 'string' && validAlias(value.apo) ? words(value.apo) : 'apo',
      napo: typeof value.napo === 'string' && validAlias(value.napo) ? words(value.napo) : 'napo',
    }
    for (const key of ['apoAliases', 'napoAliases'] as const) {
      const raw = value[key]
      if (!Array.isArray(raw)) continue
      const aliases = raw.filter((item): item is string => typeof item === 'string' && validAlias(item)).map(words)
      if (aliases.length) result[key] = [...new Set(aliases)].slice(0, MAX_SAVED_ALIASES)
    }
    return conflictingAliases(result) ? { apo: 'apo', napo: 'napo' } : result
  } catch { return { apo: 'apo', napo: 'napo' } }
}
export const COMMAND_IDLE_MS = 20000
export const COMMAND_MAX_MS = 300000
export const COMMAND_MAX_CHARS = 15900
export class WakeCommand {
  body = ''
  awake = false
  startedAt = 0
  lastHeardAt = 0
  expired(now=Date.now()) { return this.awake && (now-this.lastHeardAt>COMMAND_IDLE_MS || now-this.startedAt>COMMAND_MAX_MS) }
  touch(now=Date.now()) { if(this.awake)this.lastHeardAt=now }
  reset() { this.body = ''; this.awake = false; this.startedAt = 0; this.lastHeardAt = 0 }
  accept(text: string, pronunciation: Pronunciation, now = Date.now()): string | null {
    return this.acceptEvent(text, pronunciation, now).command
  }
  acceptEvent(text: string, pronunciation: Pronunciation, now = Date.now()): { command: string | null; woke: boolean } {
    let woke = false
    if (this.expired(now)) this.reset()
    const tokens = text.toLowerCase().replace(/(\d)\.(?=\d)/g, '$1decimalmark').replace(/[^a-z0-9\s-]/g, ' ').replace(/decimalmark/g, '.').trim().split(/\s+/).filter(Boolean)
    const starts = apoAliases(pronunciation).map((s) => s.split(' ')).sort((a,b)=>b.length-a.length)
    const ends = napoAliases(pronunciation).map((s) => s.split(' ')).sort((a,b)=>b.length-a.length)
    const match = (at: number, choices: string[][]) => choices.find((part) => part.every((token, i) => tokens[at + i] === token))
    for (let i = 0; i < tokens.length; i++) {
      const end = match(i, ends)
      const start = i === 0 || tokens[i] === 'apo' ? match(i, starts) : undefined
      if (!this.awake) { if (start) { this.awake = true; this.startedAt = now; this.lastHeardAt=now; woke = true; i += start.length - 1 } continue }
      if (end && i + end.length === tokens.length) { const body = this.body.trim(); this.reset(); return { command: body ? `Apo ${body} Napo` : null, woke } }
      if (start?.length === 1 && start[0] === 'apo') { this.body = ''; this.startedAt = now; this.lastHeardAt=now; i += start.length - 1; continue }
      this.lastHeardAt=now
      this.body += `${tokens[i]} `
      if (this.body.length > COMMAND_MAX_CHARS) { this.reset(); return { command: null, woke } }
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
  if (machine.expired(now)) machine.reset()
  if (/^(cancel|cancel sale|cancel basket)$/.test(clean)) { machine.reset(); return { command: text, capturing: false } }
  const starts = apoAliases(pronunciation)
  const startsRetry = starts.some(start => clean === start || clean.startsWith(`${start} `))
  if (!machine.awake && !startsRetry) return { command: text.trim() || null, capturing: false }
  const result = machine.acceptEvent(text, pronunciation, now)
  return { command: result.command, capturing: machine.awake }
}
