export type Pronunciation = { apo: string; napo: string }
export const PRONUNCIATION_KEY = 'street-ceo-pronunciation-v1'
export const words = (value: string) => value.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').trim().replace(/\s+/g, ' ')
export function validAlias(value: string) { const clean = words(value); return /^[a-z]+(?: [a-z]+){0,2}$/.test(clean) && clean.length <= 30 }
export function conflictingAliases(value: Pronunciation) {
  const starts = ['apo', 'apple', value.apo].map(words), ends = ['napo', 'nabo', value.napo].map(words)
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
    const starts = [...new Set(['apo', pronunciation.apo])].map((s) => s.split(' '))
    const ends = [...new Set(['napo', 'nabo', pronunciation.napo])].map((s) => s.split(' '))
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

