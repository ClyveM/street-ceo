/** Contract verified against services/api/app.py: MuseAskRequest/MuseAskResponse. */
// Confirmed in InMemoryStore.seed_demo_shop() and Hwaro's W3-MUSE-SHOP-001 handoff.
export const DEMO_SHOP_ID = '00000000-0000-0000-0000-000000000001'
export const SAMPLE_SHOP_ID = '00000000-0000-0000-0000-000000000120'
export type ShopConnection = { baseUrl: string; shopId: string }

/** Upgrade only the retired, known APK demo connection. Custom shops and browsers stay unchanged. */
export function migrateKnownDemoConnection(storage: Pick<Storage, 'getItem' | 'setItem'>, bundled: Partial<ShopConnection>, nativeAndroid: boolean): string | null {
  if (!nativeAndroid || bundled.baseUrl?.trim().replace(/\/$/, '') !== 'http://192.168.10.213:8001' || (bundled.shopId ?? DEMO_SHOP_ID).trim() !== DEMO_SHOP_ID) return null
  let saved: unknown
  try { saved = JSON.parse(storage.getItem('street-ceo-api-config') ?? 'null') } catch { return null }
  if (!saved || typeof saved !== 'object' || Array.isArray(saved)) return null
  const config = saved as Record<string, unknown>
  if (typeof config.baseUrl !== 'string' || config.baseUrl.trim().replace(/\/$/, '') !== 'http://192.168.10.213:8000' || typeof config.shopId !== 'string' || config.shopId.trim() !== DEMO_SHOP_ID) return null
  try { storage.setItem('street-ceo-api-config', JSON.stringify({ ...config, baseUrl: 'http://192.168.10.213:8001' })) }
  catch { return 'The saved demo connection could not be updated. Open Profile → Shop Connection and use port 8001.' }
  return 'Demo connection updated to the current local server on port 8001. Your shop and other saved settings were preserved.'
}

export function resolveShopConnection(stored: unknown, environment: Partial<ShopConnection> = {}): ShopConnection {
  const saved = stored && typeof stored === 'object' && !Array.isArray(stored) ? stored as Record<string, unknown> : {}
  return {
    baseUrl: (typeof saved.baseUrl === 'string' ? saved.baseUrl : environment.baseUrl ?? '').trim(),
    shopId: (typeof saved.shopId === 'string' ? saved.shopId : environment.shopId ?? DEMO_SHOP_ID).trim(),
  }
}

export function shopConfigurationError(config: ShopConnection): string | null {
  if (!config.baseUrl.trim()) return 'Backend address is missing. Open Shop Connection to connect your shop.'
  if (!config.shopId.trim()) return 'Shop ID is missing. Enter your shop’s ID in Shop Connection.'
  if (!/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(config.shopId.trim()) || /^0{8}(?:-0{4}){3}-0{12}$/.test(config.shopId.trim())) {
    return 'Shop ID is invalid. Enter a non-zero shop UUID in Shop Connection.'
  }
  try {
    const url = new URL(config.baseUrl.trim())
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) throw new Error()
  } catch { return 'Backend address is invalid. Enter the HTTP or HTTPS backend root in Shop Connection.' }
  return null
}

export type MuseSection = { title: string; body: string; evidence_ids?: string[] }
export type MuseDocument = { title: string; sections: MuseSection[] }

export type MuseResponse = {
  status: 'answered' | 'needs_data' | 'unavailable'
  title: string
  answer: string
  evidence_ids: string[]
  missing_data: string[]
  source: string
  confidence: number
  document?: MuseDocument | null
  sections?: MuseSection[]
  partial?: boolean
}

export function parseMuseResponse(value: unknown): MuseResponse {
  if (!value || typeof value !== 'object') throw new Error('Muse returned an unreadable response. Please try again.')
  const data = value as Record<string, unknown>
  const strings = (v: unknown): v is string[] => Array.isArray(v) && v.every((item) => typeof item === 'string')
  if (!['answered', 'needs_data', 'unavailable'].includes(String(data.status)) ||
    typeof data.title !== 'string' || !data.title.trim() ||
    typeof data.answer !== 'string' || !data.answer.trim() ||
    typeof data.source !== 'string' || !data.source.trim() ||
    !strings(data.evidence_ids) || !strings(data.missing_data) ||
    typeof data.confidence !== 'number' || !Number.isFinite(data.confidence) || data.confidence < 0 || data.confidence > 1) {
    throw new Error('Muse returned an unreadable response. Please try again.')
  }
  if (data.sections != null && !validMuseSections(data.sections)) {
    throw new Error('Muse returned unreadable investigation sections.')
  }
  if (data.document != null && !validMuseDocument(data.document)) {
    throw new Error('Muse returned an unreadable business plan.')
  }
  return data as MuseResponse
}

const boundedMuseText = (field: unknown, limit: number): field is string =>
  typeof field === 'string' && !!field.trim() && field.length <= limit

function validMuseSections(value: unknown): value is MuseSection[] {
  return Array.isArray(value) && value.length <= 20 && value.every(section =>
    section && boundedMuseText(section.title, 250) && boundedMuseText(section.body, 12000) &&
    (section.evidence_ids == null || Array.isArray(section.evidence_ids) && section.evidence_ids.length <= 24 &&
      section.evidence_ids.every((id: unknown) => boundedMuseText(id, 64))))
}

function validMuseDocument(value: unknown): value is MuseDocument {
  if (!value || typeof value !== 'object') return false
  const { title, sections } = value as Record<string, unknown>
  return boundedMuseText(title, 250) && validMuseSections(sections) && sections.length > 0
}

/** Period comes from returned evidence, never from a guess about the question. */
export function museSourcePeriod(ids: string[]): string {
  const periods = [...new Set(ids.map((id) => /^(?:sales|transactions)-(.+)$/.exec(id)?.[1]).filter(Boolean))]
  if (!periods.length) return 'Not supplied by the service'
  return periods.map((period) => {
    if (period === 'today') return 'Today (UTC)'
    if (period === 'this_month') return 'This month (service label)'
    if (period === 'available') return 'All available records'
    const days = /^last_(\d+)_days$/.exec(period!)
    return days ? `Last ${days[1]} days (UTC)` : period
  }).join('; ')
}

export async function requestMuse(
  config: { baseUrl: string; shopId: string }, question: string,
  signal?: AbortSignal, fetcher: typeof fetch = fetch,
): Promise<MuseResponse> {
  const configurationError = shopConfigurationError(config)
  if (configurationError) throw new Error(configurationError)
  const shopId = config.shopId.trim()
  const trimmed = question.trim()
  if (!trimmed || trimmed.length > 1000) throw new Error('Enter a question of 1–1,000 characters.')
  const timeout = AbortSignal.timeout(65000)
  try {
    const response = await fetcher(`${config.baseUrl.trim().replace(/\/$/, '')}/api/v1/shops/${encodeURIComponent(shopId)}/muse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'X-Shop-ID': shopId },
      body: JSON.stringify({ question: trimmed }),
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    })
    if (!response.ok) {
      const message = response.status === 404 ? 'Ask Muse is unavailable on this backend, or the shop was not found.'
        : response.status === 403 ? 'The shop connection was rejected. Check your Shop ID.'
          : response.status === 422 ? 'Muse could not accept this question. Check it and try again.'
            : 'Muse could not answer right now. Please try again.'
      throw new Error(`${message} (${response.status})`)
    }
    return parseMuseResponse(await response.json())
  } catch (error) {
    if (timeout.aborted) throw new Error('Muse took too long to respond. Please try again.')
    if (signal?.aborted) throw error
    if (error instanceof TypeError) throw new Error('Could not reach Muse. Check your connection and try again.')
    if (error instanceof SyntaxError) throw new Error('Muse returned an unreadable response. Please try again.')
    throw error
  }
}

export type MuseJobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'expired'
const museProgressLabels = {
  discovering: 'Muse is checking which business records are available…',
  investigating: 'Muse is reviewing the evidence…',
  retrieving: 'Muse is reading the records it selected…',
  drafting: 'Muse is preparing your answer…',
}
type MuseProgressStage = keyof typeof museProgressLabels

export type MuseJob = { job_id: string; status: MuseJobStatus; result: MuseResponse | null; progress?: MuseProgressStage }

function parseMuseProgress(progress: unknown): MuseProgressStage | undefined {
  if (!progress || typeof progress !== 'object') return
  const { stage } = progress as Record<string, unknown>
  if (typeof stage === 'string' && Object.prototype.hasOwnProperty.call(museProgressLabels, stage)) return stage as MuseProgressStage
}

export function museJobProgressLabel(job: MuseJob): string {
  if (job.status === 'queued') return 'Muse has queued your question…'
  return job.progress ? museProgressLabels[job.progress] : 'Muse is working on your answer…'
}
export type PendingMuseJob = {
  requestId: string
  jobId?: string
  priorJobId?: string
  startedAt: number
  chatId: string
  message: string
  question: string
}

export class MuseJobError extends Error {
  readonly retryable: boolean
  constructor(message: string, retryable: boolean) {
    super(message)
    this.retryable = retryable
  }
}

const jobIdPattern = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i

export async function requestMuseJob(
  config: ShopConnection, pending: PendingMuseJob, signal: AbortSignal, fetcher: typeof fetch = fetch,
): Promise<MuseJob> {
  const configError = shopConfigurationError(config)
  if (configError) throw new MuseJobError(configError, false)
  const question = pending.question.trim()
  if (!question || question.length > 1000 || !jobIdPattern.test(pending.requestId) ||
      (pending.jobId && !jobIdPattern.test(pending.jobId)) ||
      (pending.priorJobId && !jobIdPattern.test(pending.priorJobId))) {
    throw new MuseJobError('Muse could not accept this question. Check it and try again.', false)
  }
  const shopId = config.shopId.trim()
  const headers: Record<string, string> = { Accept: 'application/json', 'X-Shop-ID': shopId }
  const timeout = AbortSignal.timeout(8000)
  const url = `${config.baseUrl.trim().replace(/\/$/, '')}/api/v1/shops/${encodeURIComponent(shopId)}/muse/jobs`
  try {
    if (!pending.jobId) {
      headers['Content-Type'] = 'application/json'
      headers['Idempotency-Key'] = pending.requestId
    }
    const response = await fetcher(pending.jobId ? `${url}/${pending.jobId}` : url, {
      method: pending.jobId ? 'GET' : 'POST',
      headers,
      body: pending.jobId ? undefined : JSON.stringify({ question, prior_job_id: pending.priorJobId }),
      signal: AbortSignal.any([signal, timeout]),
      cache: 'no-store',
    })
    if (!response.ok) {
      const message = response.status === 404
        ? pending.jobId ? 'Muse could not find the saved request.' : 'Ask Muse jobs are unavailable on this backend, or the shop was not found.'
        : response.status === 403 ? 'The shop connection was rejected. Check your Shop ID.'
        : response.status === 422 ? 'Muse could not accept this question. Check it and try again.'
        : response.status === 409 ? 'Muse could not match the saved request.'
        : 'Muse is temporarily unavailable.'
      throw new MuseJobError(message, response.status >= 500 || [408, 425, 429].includes(response.status))
    }
    const data = await response.json()
    if (typeof data?.job_id !== 'string' || !jobIdPattern.test(data.job_id) ||
      (pending.jobId && pending.jobId !== data.job_id) ||
      !['queued', 'running', 'succeeded', 'failed', 'expired'].includes(data.status)) {
      throw new Error('Invalid Muse job')
    }
    const progress = parseMuseProgress(data.progress)
    return {
      job_id: data.job_id, status: data.status,
      result: data.status === 'succeeded' ? parseMuseResponse(data.result) : null,
      ...(progress ? { progress } : {}),
    }
  } catch (error) {
    if (signal.aborted || error instanceof MuseJobError) throw error
    const message = timeout.aborted || error instanceof TypeError
      ? 'Could not reach Muse. Check your connection.'
      : 'Muse returned an unreadable response.'
    throw new MuseJobError(message, true)
  }
}
