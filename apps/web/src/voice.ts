import { getApiConfig } from './api'
import { shopConfigurationError } from './muse'
import { createQuickSaleClient } from './quickSale'

const client = createQuickSaleClient(() => {
  const config = getApiConfig(), error = shopConfigurationError(config)
  if (error) throw new Error(error)
  return config
})
function blobAsBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',', 2)[1] ?? '')
    reader.onerror = () => reject(new Error('Could not read microphone recording.'))
    reader.readAsDataURL(blob)
  })
}
export const voiceClient = {
  interpretTranscript: client.interpret,
  commit: client.commit,
  undo: client.undo,
  async transcribe(audio: Blob, key: string, signal?: AbortSignal) {
    if (!audio.size || audio.size > 5 * 1024 * 1024) throw new Error('Use a non-empty recording up to 5 MiB.')
    return client.audio(await blobAsBase64(audio), audio.type || 'audio/webm', key, signal)
  },
}
