export type VoiceTranscription = { transcript: string }

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
const SHOP_ID = import.meta.env.VITE_SHOP_ID ?? '00000000-0000-0000-0000-000000000001'
const VOICE_INPUT_URL = import.meta.env.VITE_VOICE_INPUT_URL ?? `${API_BASE_URL}/api/v1/shops/${SHOP_ID}/voice/audio`

function blobAsBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',', 2)[1] ?? '')
    reader.onerror = () => reject(reader.error ?? new Error('Could not read microphone recording'))
    reader.readAsDataURL(blob)
  })
}

/** Browser audio stops at this boundary; provider credentials stay server-side. */
export const voiceClient = {
  async transcribe(audio: Blob): Promise<VoiceTranscription> {
    if (!VOICE_INPUT_URL) throw new Error('Voice service is not configured. Use the text fallback.')
    const response = await fetch(VOICE_INPUT_URL, { method: 'POST', body: JSON.stringify({ audio_base64: await blobAsBase64(audio), media_type: audio.type || 'audio/webm' }), headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': `voice-${Date.now()}-${Math.random().toString(16).slice(2)}`, 'X-Shop-ID': SHOP_ID } })
    if (!response.ok) throw new Error(`Voice service returned ${response.status}`)
    const payload = await response.json() as unknown
    if (typeof payload !== 'object' || payload === null) throw new Error('Voice service returned no response')
    const typed = payload as { transcript?: unknown; status?: unknown; error?: unknown }
    if (typeof typed.transcript === 'string' && typed.transcript.trim()) return { transcript: typed.transcript.trim() }
    if (typed.status === 'unavailable') throw new Error('Audio was received, but speech-to-text is not configured yet. Use the text fallback.')
    throw new Error(typeof typed.error === 'string' ? typed.error : 'Voice service returned no transcript')
  },
}
