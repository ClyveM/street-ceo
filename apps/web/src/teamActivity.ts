export type AgentStatus = 'Working' | 'Ready' | 'Review'

export type AgentActivity = {
  name: string
  role: string
  status: AgentStatus
  task: string
  files: string[]
  lastActivity: string
  accent: string
}

export type TeamStats = {
  completedTasks: number
  activeTasks: number
  commits: number
  totalUnitTests: number
  passingUnitTests: number
  warnings: string[]
}

export type TeamSnapshot = { agents: AgentActivity[]; stats: TeamStats }

export const fallbackTeamSnapshot: TeamSnapshot = {
  agents: [
    { name: 'Hwaro', role: 'Backend & Database', status: 'Working', task: 'Persistence adapter', files: ['services/api/persistence.py', 'services/api/app.py'], lastActivity: '2 min ago', accent: '#8a6de9' },
    { name: 'Verengai', role: 'Financial Systems', status: 'Review', task: 'MVP ledger and cash movements', files: ['services/finance/ledger.py'], lastActivity: '8 min ago', accent: '#e1843d' },
    { name: 'Dura', role: 'Inventory & Retail', status: 'Working', task: 'Weighted-average stock costs', files: ['services/inventory/movements.py', 'services/inventory/test_movements.py'], lastActivity: '4 min ago', accent: '#d05c8b' },
    { name: 'Runako', role: 'Frontend & UX', status: 'Working', task: 'Mobile-first web shell', files: ['apps/web/src/App.tsx', 'apps/web/src/styles.css', 'apps/web/src/api.ts'], lastActivity: 'Just now', accent: '#0b8f83' },
    { name: 'Fambai', role: 'Mobile & Offline', status: 'Ready', task: 'Offline queue and sync contract', files: ['apps/web/service-worker.js'], lastActivity: '12 min ago', accent: '#3d91c7' },
    { name: 'Inzwi', role: 'Voice AI', status: 'Working', task: 'Apo/Napo interaction adapter', files: ['services/voice/state_machine.py'], lastActivity: '6 min ago', accent: '#d49a29' },
  ],
  stats: { completedTasks: 7, activeTasks: 6, commits: 12, totalUnitTests: 40, passingUnitTests: 40, warnings: ['npm registry unavailable for frontend build', 'Fambai offline queue awaiting integration'] },
}

const ACTIVITY_URL = import.meta.env.VITE_TEAM_ACTIVITY_URL ?? ''

function isRecord(value: unknown): value is Record<string, unknown> { return typeof value === 'object' && value !== null }
function requiredString(value: unknown, field: string): string { if (typeof value !== 'string' || !value.trim()) throw new Error(`Invalid team activity field: ${field}`); return value }
function requiredNumber(value: unknown, field: string): number { if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error(`Invalid team activity field: ${field}`); return value }

const ROLE_LABELS: Record<string, string> = {
  mutungamiri: 'CTO & Orchestrator', runako: 'Frontend & UX', fambai: 'Mobile & Offline',
  hwaro: 'Backend & Database', inzwi: 'Voice AI', ungwaru: 'Meta AI', verengai: 'Financial Systems',
  dura: 'Inventory & Retail', chiono: 'Business Intelligence', chengetai: 'QA, Security & DevOps', ruzivo: 'CFO & Strategy',
}

function relativeTime(value: unknown): string {
  if (typeof value !== 'string') return 'Unknown'
  const age = Math.max(0, Date.now() - Date.parse(value))
  const minutes = Math.floor(age / 60000)
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  return `${hours} hr ago`
}

function parseRepositoryActivity(body: Record<string, unknown>): TeamSnapshot {
  const tasks = Array.isArray(body.tasks) ? body.tasks.filter(isRecord) : []
  const rawAgents = Array.isArray(body.agents) ? body.agents.filter(isRecord) : []
  const changedFiles = Array.isArray(body.changed_files) ? body.changed_files.filter(isRecord) : []
  const evidence = Array.isArray(body.test_evidence) ? body.test_evidence.filter(isRecord) : []
  const commits = isRecord(body.commits) ? body.commits : {}
  const agentActivities = rawAgents.map((agent, index) => {
    const name = requiredString(agent.agent, `agents[${index}].agent`)
    const slug = name.toLowerCase()
    const owned = tasks.find((task) => String(task.owner ?? '').toLowerCase().includes(slug))
    const files = changedFiles.slice(0, 3).map((file) => String(file.path ?? '')).filter(Boolean)
    const status: AgentStatus = owned?.status === 'done' ? 'Ready' : owned?.status === 'active' ? 'Working' : 'Review'
    return {
      name: name.charAt(0).toUpperCase() + name.slice(1), role: ROLE_LABELS[slug] ?? 'Project Team', status,
      task: typeof owned?.task === 'string' ? owned.task : 'Monitoring project activity', files,
      lastActivity: relativeTime(agent.last_activity_at), accent: fallbackTeamSnapshot.agents[index % fallbackTeamSnapshot.agents.length]?.accent ?? '#0b8f83',
    }
  })
  const passed = evidence.reduce((sum, item) => sum + (typeof item.passed === 'number' ? item.passed : 0), 0)
  return {
    agents: agentActivities,
    stats: {
      completedTasks: tasks.filter((task) => task.status === 'done').length,
      activeTasks: tasks.filter((task) => task.status === 'active').length,
      commits: typeof commits.count === 'number' ? commits.count : 0,
      totalUnitTests: passed, passingUnitTests: passed,
      warnings: Array.isArray(body.warnings) ? body.warnings.filter((warning): warning is string => typeof warning === 'string') : [],
    },
  }
}

export function parseTeamSnapshot(payload: unknown): TeamSnapshot {
  const body = isRecord(payload) && isRecord(payload.data) ? payload.data : payload
  if (isRecord(body) && Array.isArray(body.tasks) && isRecord(body.commits)) return parseRepositoryActivity(body)
  if (!isRecord(body) || !Array.isArray(body.agents) || !isRecord(body.stats)) throw new Error('Team activity response must contain agents and stats')
  const agents = body.agents.map((raw, index) => {
    if (!isRecord(raw)) throw new Error('Invalid team activity agent')
    const status = requiredString(raw.status, `agents[${index}].status`) as AgentStatus
    if (!['Working', 'Ready', 'Review'].includes(status)) throw new Error(`Unsupported team activity status: ${status}`)
    if (!Array.isArray(raw.files) || raw.files.some((file) => typeof file !== 'string')) throw new Error(`Invalid team activity files at agents[${index}]`)
    return { name: requiredString(raw.name, `agents[${index}].name`), role: requiredString(raw.role, `agents[${index}].role`), status, task: requiredString(raw.task, `agents[${index}].task`), files: raw.files as string[], lastActivity: requiredString(raw.lastActivity, `agents[${index}].lastActivity`), accent: typeof raw.accent === 'string' ? raw.accent : fallbackTeamSnapshot.agents[index]?.accent ?? '#0b8f83' }
  })
  const stats = body.stats
  if (!Array.isArray(stats.warnings) || stats.warnings.some((warning) => typeof warning !== 'string')) throw new Error('Invalid team activity warnings')
  return { agents, stats: { completedTasks: requiredNumber(stats.completedTasks, 'stats.completedTasks'), activeTasks: requiredNumber(stats.activeTasks, 'stats.activeTasks'), commits: requiredNumber(stats.commits, 'stats.commits'), totalUnitTests: requiredNumber(stats.totalUnitTests, 'stats.totalUnitTests'), passingUnitTests: requiredNumber(stats.passingUnitTests, 'stats.passingUnitTests'), warnings: stats.warnings as string[] } }
}

export async function fetchTeamSnapshot(signal?: AbortSignal): Promise<TeamSnapshot> {
  if (!ACTIVITY_URL) throw new Error('VITE_TEAM_ACTIVITY_URL is not configured')
  const response = await fetch(ACTIVITY_URL, { headers: { Accept: 'application/json' }, signal })
  if (!response.ok) throw new Error(`Team activity endpoint returned ${response.status}`)
  return parseTeamSnapshot(await response.json())
}

export function hasLiveActivityUrl(): boolean { return Boolean(ACTIVITY_URL) }
