/** Client request/layout reference, never an authentication credential. Works on HTTP LAN. */
export function clientId(source: { randomUUID?: () => string; getRandomValues?: (bytes: Uint8Array<ArrayBuffer>) => Uint8Array<ArrayBuffer> } | undefined = globalThis.crypto): string {
  if (typeof source?.randomUUID === 'function') return source.randomUUID()
  const bytes = new Uint8Array(16)
  if (typeof source?.getRandomValues === 'function') source.getRandomValues(bytes)
  else for (let index = 0; index < bytes.length; index++) bytes[index] = Math.floor(Math.random() * 256)
  bytes[6] = bytes[6] & 15 | 64; bytes[8] = bytes[8] & 63 | 128
  const hex = [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}
