export type TokenPair = { access: string; refresh: string }

export type Membership = {
  id: number
  role: 'ADMIN' | 'ANALYST'
  is_active: boolean
  created_at: string
  org: { id: number; name: string; slug: string; created_at: string }
}

export type IngestionJob = {
  id: number
  source: { id: number; source_type: 'SAP' | 'UTILITY' | 'TRAVEL'; name: string }
  status: 'CREATED' | 'PARSED' | 'PARTIAL' | 'FAILED' | 'LOCKED'
  received_rows: number
  parsed_rows: number
  failed_rows: number
  suspicious_rows: number
  approved_rows: number
  created_at: string
  processed_at: string | null
  locked_at: string | null
}

export type NormalizedRecord = {
  id: number
  category:
    | 'FUEL'
    | 'PROCUREMENT'
    | 'ELECTRICITY'
    | 'TRAVEL_FLIGHT'
    | 'TRAVEL_HOTEL'
    | 'TRAVEL_GROUND'
  scope: 'SCOPE_1' | 'SCOPE_2' | 'SCOPE_3'
  source_row_ref: string
  activity_date: string | null
  period_start: string | null
  period_end: string | null
  description: string
  quantity: string | null
  unit: string
  normalized_quantity: string | null
  normalized_unit: string
  supplier: string
  spend_amount: string | null
  spend_currency: string
  traveler: string
  origin: string
  destination: string
  distance_km: string | null
  review_status: 'PENDING' | 'APPROVED' | 'REJECTED'
  suspicious: boolean
  suspicious_reasons: string[]
  is_locked: boolean
  approved_at: string | null
}

export type RawErrorRow = {
  id: number
  row_number: number
  status: 'ERROR'
  error: string
  raw: Record<string, unknown>
  parsed: Record<string, unknown>
  created_at: string
}

const API_BASE = import.meta.env.VITE_API_BASE || ''

function getToken() {
  return localStorage.getItem('access_token')
}

function setTokens(tokens: TokenPair) {
  localStorage.setItem('access_token', tokens.access)
  localStorage.setItem('refresh_token', tokens.refresh)
}

export function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', headers.get('Content-Type') || 'application/json')

  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const resp = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (resp.status === 401) {
    throw new Error('unauthorized')
  }
  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(text || `HTTP ${resp.status}`)
  }
  return (await resp.json()) as T
}

export async function login(username: string, password: string) {
  const resp = await fetch(`${API_BASE}/api/auth/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!resp.ok) {
    throw new Error('Invalid credentials')
  }
  const tokens = (await resp.json()) as TokenPair
  setTokens(tokens)
}

export async function getMe() {
  return request<{ id: number; username: string; email: string | null }>(
    '/api/me/',
  )
}

export async function getMyOrgs() {
  return request<Membership[]>('/api/orgs/')
}

export async function ensureDemoOrg() {
  return request<{ detail: string }>(`/api/debug/ensure-demo-org/`, {
    method: 'POST',
  })
}

export async function listJobs(orgSlug: string) {
  return request<IngestionJob[]>(`/api/orgs/${orgSlug}/jobs/`)
}

export async function getJob(orgSlug: string, jobId: number) {
  return request<IngestionJob>(`/api/orgs/${orgSlug}/jobs/${jobId}/`)
}

export async function listRecords(
  orgSlug: string,
  jobId: number,
  opts?: { reviewStatus?: string; suspicious?: boolean },
) {
  const params = new URLSearchParams()
  if (opts?.reviewStatus) params.set('review_status', opts.reviewStatus)
  if (opts?.suspicious) params.set('suspicious', '1')
  const q = params.toString()
  return request<NormalizedRecord[]>(
    `/api/orgs/${orgSlug}/jobs/${jobId}/records/${q ? `?${q}` : ''}`,
  )
}

export async function listErrors(orgSlug: string, jobId: number) {
  return request<RawErrorRow[]>(`/api/orgs/${orgSlug}/jobs/${jobId}/errors/`)
}

export async function uploadIngest(
  orgSlug: string,
  sourceType: 'SAP' | 'UTILITY' | 'TRAVEL',
  file: File,
) {
  const token = getToken()
  const form = new FormData()
  form.append('source_type', sourceType)
  form.append('file', file)

  const resp = await fetch(`${API_BASE}/api/orgs/${orgSlug}/ingest/upload/`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: form,
  })
  if (!resp.ok) throw new Error(await resp.text())
  return (await resp.json()) as IngestionJob
}

export async function approveRecord(orgSlug: string, recordId: number) {
  return request<NormalizedRecord>(`/api/orgs/${orgSlug}/records/${recordId}/approve/`, {
    method: 'POST',
  })
}

export async function updateRecord(
  orgSlug: string,
  recordId: number,
  patch: Partial<NormalizedRecord> & { reason?: string },
) {
  return request<NormalizedRecord>(`/api/orgs/${orgSlug}/records/${recordId}/`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  })
}

export async function lockJob(orgSlug: string, jobId: number) {
  return request<IngestionJob>(`/api/orgs/${orgSlug}/jobs/${jobId}/lock/`, {
    method: 'POST',
  })
}
