import {
  IncidentCreatePayload,
  IncidentOut,
  IncidentStatusResponse,
  RiskZoneOut,
  DecisionRequest,
  DecisionResponse,
  WhatIfRequest,
  WhatIfResponse,
} from '../types/api'

const API_BASE =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) || ''

export function apiUrl(path: string): string {
  if (!API_BASE) return path
  return `${API_BASE.replace(/\/$/, '')}${path}`
}

let authToken: string | null =
  typeof localStorage !== 'undefined' && typeof localStorage.getItem === 'function'
    ? localStorage.getItem('crisiscore_token')
    : null

export function setAuthToken(token: string | null) {
  authToken = token
  if (typeof localStorage !== 'undefined' && typeof localStorage.setItem === 'function') {
    if (token) localStorage.setItem('crisiscore_token', token)
    else localStorage.removeItem('crisiscore_token')
  }
}

export function getAuthToken(): string | null {
  return authToken
}

async function request(path: string, opts: RequestInit = {}) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string> || {}),
  }
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`
  const res = await fetch(apiUrl(path), { ...opts, headers })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`${res.status} ${txt}`)
  }
  return res.json().catch(() => ({}))
}

export function getUserRole(): string | null {
  if (typeof localStorage !== 'undefined' && typeof localStorage.getItem === 'function') {
    const cached = localStorage.getItem('crisiscore_user_role')
    if (cached) return cached
  }
  if (!authToken) return null
  try {
    const parts = authToken.split('.')
    if (parts.length === 3) {
      const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
      return payload.role || null
    }
  } catch {
    // ignore
  }
  return null
}

// --- Auth ---
export async function login(phone: string, password: string): Promise<{ access_token: string; role: string }> {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ phone, password }),
  })
  if (data?.access_token) {
    setAuthToken(data.access_token)
    if (typeof localStorage !== 'undefined' && typeof localStorage.setItem === 'function') {
      localStorage.setItem('crisiscore_user_role', data.role || '')
    }
  }
  return data
}

export function logout(): void {
  setAuthToken(null)
  if (typeof localStorage !== 'undefined' && typeof localStorage.removeItem === 'function') {
    localStorage.removeItem('crisiscore_user_role')
    localStorage.removeItem('crisiscore_token')
  }
}

// --- Incidents ---
export async function createIncident(payload: IncidentCreatePayload): Promise<IncidentOut> {
  return request('/incidents', { method: 'POST', body: JSON.stringify(payload) })
}

export async function createIncidentSMS(payload: { phone: string; text: string; lat?: number; lng?: number }) {
  return request('/incidents/sms', { method: 'POST', body: JSON.stringify(payload) })
}

// --- Status ---
export async function getStatus(incidentId: string): Promise<IncidentStatusResponse> {
  return request(`/status/${incidentId}`)
}

// --- Health ---
export async function getHealth() {
  return request('/health')
}

// --- Risk ---
export async function getRisk(bbox?: string, horizon: string = '24h'): Promise<RiskZoneOut[]> {
  const params = new URLSearchParams()
  if (bbox) params.set('bbox', bbox)
  if (horizon) params.set('horizon', horizon)
  const q = params.toString() ? `?${params.toString()}` : ''
  return request(`/risk${q}`)
}

// --- Intelligence ---
export async function getIntelligenceDecision(payload: DecisionRequest): Promise<DecisionResponse> {
  return request('/intelligence/decision', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function simulateWhatIf(payload: WhatIfRequest): Promise<WhatIfResponse> {
  return request('/intelligence/whatif', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
