const BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export type Priority = 'P1' | 'P2' | 'P3' | 'P4' | 'UNRATED'

export interface Incident {
  incident_id: string
  status: string
  priority: Priority
  severity: string
  confidence: number | null
  location: { lat: number | null; lon: number | null; confidence: number | null }
  victim_estimate: number | null
  vulnerability: Record<string, boolean>
  evidence_count: number
  independent_source_count: number
  zone_id: string | null
  created_at: string
  updated_at: string
  last_evidence_at: string | null
  resolved_at: string | null
}

export interface Zone {
  zone_id: string
  center: { lat: number; lon: number }
  radius_m: number
  priority: Priority
  confidence: number | null
  evidence_count: number
  independent_source_count: number
  incident_ids: string[]
  incidents: Array<{
    incident_id: string
    priority: Priority
    severity: string
    vulnerability: Record<string, boolean>
    victim_estimate: number | null
    evidence_count: number
    independent_source_count: number
    updated_at: string
  }>
}

export interface SystemStatus {
  connectivity_mode: string
  disaster_active: string | null
  events_by_source: Record<string, number>
  total_events: number
  total_incidents: number
  open_incidents: number
  llm_health: string
  llm_last_error: string | null
  llm_last_latency_ms: number | null
}

export interface MapData {
  heat_points: Array<{ lat: number; lon: number; weight: number; flagged?: string | null }>
  zones: Array<{
    zone_id: string
    lat: number
    lon: number
    radius_m: number
    priority: Priority
    confidence: number | null
    incident_count: number
    evidence_count: number
    source_count: number
  }>
  incidents: Array<{
    incident_id: string
    lat: number | null
    lon: number | null
    priority: Priority
    severity: string
    confidence: number | null
    vulnerability: Record<string, boolean>
    victim_estimate: number | null
    evidence_count: number
    source_count: number
    status: string
    updated_at: string
  }>
}

export interface PriorityDetail {
  score: number
  level: Priority
  components: Record<string, number>
  corroboration_boost: number
  reasons: Array<{ factor: string; weight?: number; value: number; evidence?: unknown[]; note?: string }>
  current_level?: Priority
  history?: Array<{ score: number; level: Priority; timestamp: string }>
}

export interface Recommendation {
  recommendation_id?: number
  resources: Array<{ resource: string; quantity: number; priority: string }>
  reasons: string[]
  status: string
}

export interface EvidenceEntry {
  event_id: string
  source_type: string
  source_identifier: string | null
  timestamp: string
  text: string
  flagged: string | null
  extraction: {
    severity?: string
    attributes?: Record<string, { value: boolean; confidence?: number; model?: string }>
    llm?: { result?: Record<string, unknown>; model_version?: string; status?: string } | null
  } | null
  confidence: number
  relationship: string
}

export interface SignalEntry {
  event_id: string
  source_type: string
  source_identifier: string | null
  timestamp: string
  text: string | null
  flagged: string | null
  incident_id: string | null
  status: string
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('netra_token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (res.status === 401) {
    localStorage.removeItem('netra_token')
    window.location.reload()
    throw new Error('unauthorized')
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail?.message || body.detail?.code || `${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  login: (username: string, password: string) =>
    request<{ access_token: string; user: { role: string; display_name: string } }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  me: () => request<{ role: string; display_name: string }>('/auth/me'),
  status: () => request<SystemStatus>('/system/status'),
  mapData: () => request<MapData>('/map-data'),
  incidents: () => request<Incident[]>('/incidents?limit=500'),
  recentEvents: (limit = 40) => request<SignalEntry[]>(`/events/recent?limit=${limit}`),
  zones: () => request<Zone[]>('/zones'),
  priority: (incidentId: string) => request<PriorityDetail>(`/incidents/${incidentId}/priority`),
  recommendation: (incidentId: string) => request<Recommendation>(`/incidents/${incidentId}/recommendation`),
  incidentEvidence: (incidentId: string) => request<EvidenceEntry[]>(`/incidents/${incidentId}/evidence`),
  fieldUpdate: (incidentId: string, updateType: string, values: Record<string, unknown> = {}, notes = '') =>
    request(`/incidents/${incidentId}/field-updates`, {
      method: 'POST',
      body: JSON.stringify({ update_type: updateType, values, notes }),
    }),
  submitEvent: (text: string, sourceType: string) =>
    request<{ event_id: string; status: string; incident_id: string | null }>('/events', {
      method: 'POST',
      body: JSON.stringify({
        source_type: sourceType,
        source_timestamp: new Date().toISOString(),
        text,
        source_identifier: 'console-operator',
        idempotency_key: `manual-${Date.now()}`,
      }),
    }),
  simStart: () =>
    request('/sim/scenario/start', { method: 'POST', body: JSON.stringify({ scenario_id: 'killer', seed: 42 }) }),
  simReset: () => request('/sim/reset', { method: 'POST', body: '{}' }),
  simStep: () => request('/sim/scenario/step', { method: 'POST', body: '{}' }),
  simInject: (kind: string) => request('/sim/inject', { method: 'POST', body: JSON.stringify({ kind, count: 5000 }) }),
  simNetwork: (mode: string) =>
    request('/sim/network', { method: 'POST', body: JSON.stringify({ mode }) }),
  simLlm: (enabled: boolean) => request('/sim/llm', { method: 'POST', body: JSON.stringify({ enabled }) }),
}