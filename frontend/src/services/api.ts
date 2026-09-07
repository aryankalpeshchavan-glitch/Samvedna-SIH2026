import {
  IncidentCreatePayload,
  IncidentOut,
  IncidentStatusResponse,
  RiskZoneOut,
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

// --- Auth ---
export async function registerOrLoginDemo(): Promise<string> {
  const phone =
    (typeof localStorage !== 'undefined' && typeof localStorage.getItem === 'function' && localStorage.getItem('crisiscore_phone')) ||
    `+91${Math.floor(1000000000 + Math.random() * 9000000000)}`
  if (typeof localStorage !== 'undefined' && typeof localStorage.setItem === 'function') {
    localStorage.setItem('crisiscore_phone', phone)
  }
  try {
    await request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ phone, password: 'demoPass123', name: 'Citizen Demo', role: 'citizen' }),
    }).catch(() => {})
    const data = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ phone, password: 'demoPass123' }),
    })
    setAuthToken(data.access_token)
    return data.access_token
  } catch (e) {
    console.warn('[API] demo auth failed', e)
    return ''
  }
}

// --- Incidents ---
export async function createIncident(payload: IncidentCreatePayload): Promise<IncidentOut> {
  if (!authToken) await registerOrLoginDemo()
  return request('/incidents', { method: 'POST', body: JSON.stringify(payload) })
}

export async function createIncidentSMS(payload: { phone: string; text: string; lat?: number; lng?: number }) {
  return request('/incidents/sms', { method: 'POST', body: JSON.stringify(payload) })
}

// --- Status ---
export async function getStatus(incidentId: string): Promise<IncidentStatusResponse> {
  if (!authToken) await registerOrLoginDemo()
  return request(`/status/${incidentId}`)
}

// --- Health ---
export async function getHealth() {
  return request('/health')
}

// --- Risk ---
export async function getRisk(bbox?: string, horizon: string = '24h'): Promise<RiskZoneOut[]> {
  if (!authToken) await registerOrLoginDemo()
  const params = new URLSearchParams()
  if (bbox) params.set('bbox', bbox)
  if (horizon) params.set('horizon', horizon)
  const q = params.toString() ? `?${params.toString()}` : ''
  return request(`/risk${q}`)
}
