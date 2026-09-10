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

export function decodeTokenPayload(token: string): { sub?: string; role?: string; exp?: number } | null {
  try {
    const parts = token.split('.')
    if (parts.length === 3) {
      return JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    }
  } catch {
    // ignore
  }
  return null
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeTokenPayload(token)
  if (!payload || !payload.exp) return false
  return payload.exp * 1000 < Date.now() + 10000
}

export function notifyAuthChange() {
  if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
    window.dispatchEvent(new CustomEvent('crisiscore-auth-change'))
  }
}

export function setAuthToken(token: string | null) {
  authToken = token
  if (typeof localStorage !== 'undefined' && typeof localStorage.setItem === 'function') {
    if (token) localStorage.setItem('crisiscore_token', token)
    else {
      localStorage.removeItem('crisiscore_token')
      localStorage.removeItem('crisiscore_user_role')
    }
  }
}

export function getAuthToken(): string | null {
  if (authToken && isTokenExpired(authToken)) {
    logout()
    return null
  }
  return authToken
}

async function request(path: string, opts: RequestInit = {}) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string> || {}),
  }
  const token = getAuthToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(apiUrl(path), { ...opts, headers })
  if (!res.ok) {
    if (res.status === 401) {
      // Clear expired / invalid token
      logout()
    }
    const txt = await res.text().catch(() => '')
    throw new Error(`${res.status} ${txt}`)
  }
  return res.json().catch(() => ({}))
}

export function getUserRole(): string | null {
  if (!authToken && typeof localStorage !== 'undefined') {
    authToken = localStorage.getItem('crisiscore_token')
  }
  if (!authToken) return null
  if (isTokenExpired(authToken)) {
    logout()
    return null
  }
  const payload = decodeTokenPayload(authToken)
  const role = payload?.role || null
  if (typeof localStorage !== 'undefined' && typeof localStorage.setItem === 'function') {
    if (role) localStorage.setItem('crisiscore_user_role', role)
    else localStorage.removeItem('crisiscore_user_role')
  }
  return role
}

export function isOperationsRole(role: string | null): boolean {
  return role === 'officer' || role === 'admin'
}

export function isOperationsUser(): boolean {
  return isOperationsRole(getUserRole())
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
    notifyAuthChange()
  }
  return data
}

export function logout(): void {
  setAuthToken(null)
  if (typeof localStorage !== 'undefined' && typeof localStorage.removeItem === 'function') {
    localStorage.removeItem('crisiscore_user_role')
    localStorage.removeItem('crisiscore_token')
  }
  notifyAuthChange()
}

// --- Incidents ---
export async function createIncident(payload: IncidentCreatePayload): Promise<IncidentOut> {
  return request('/incidents', { method: 'POST', body: JSON.stringify(payload) })
}

export async function createIncidentSMS(payload: { phone: string; text: string; lat?: number; lng?: number }) {
  return request('/incidents/sms', { method: 'POST', body: JSON.stringify(payload) })
}

export async function getIncidents(
  status?: string,
  bbox?: string,
  limit?: number
): Promise<IncidentOut[]> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (bbox) params.set('bbox', bbox)
  if (limit !== undefined) params.set('limit', String(limit))
  const q = params.toString() ? `?${params.toString()}` : ''
  return request(`/incidents${q}`)
}

export async function verifyIncident(
  id: string,
  dataLabel?: string
): Promise<IncidentOut> {
  return request(`/incidents/${id}/verify`, {
    method: 'POST',
    body: JSON.stringify({ data_label: dataLabel || 'live' }),
  })
}

export async function rejectIncident(id: string): Promise<IncidentOut> {
  return request(`/incidents/${id}/reject`, {
    method: 'PATCH',
  })
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
