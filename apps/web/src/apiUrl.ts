/** Settings accept the backend root; remove an accidentally pasted API suffix. */
export function normalizeApiBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '').replace(/\/api\/v1$/i, '')
}

export function validateApiBaseUrl(value: string): string {
  const base = normalizeApiBaseUrl(value)
  if (!base && !value.trim()) return base
  try {
    const url = new URL(base)
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) throw new Error()
    return base
  } catch { throw new Error('Enter the backend root URL, such as http://localhost:8000, without credentials, a query, or a fragment.') }
}

