/**
 * CrisisCore Backend API Client
 * Connects Pawani frontend to AJ backend (Samvedna Merge)
 * Handles JWT auth + offline fallback
 */
const API_BASE = import.meta.env.VITE_API_URL || ''

function apiUrl(path: string): string {
  if (!API_BASE) return path
  return `${API_BASE.replace(/\/$/, '')}${path}`
}

let authToken: string | null = localStorage.getItem('crisiscore_token')

export function setAuthToken(token: string | null) {
  authToken = token
  if (token) localStorage.setItem('crisiscore_token', token)
  else localStorage.removeItem('crisiscore_token')
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
  const phone = localStorage.getItem('crisiscore_phone') || `+91${Math.floor(1000000000 + Math.random()*9000000000)}`
  localStorage.setItem('crisiscore_phone', phone)
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
export async function createIncident(payload: { type: string; description: string; lat: number; lng: number; severity: number }) {
  if (!authToken) await registerOrLoginDemo()
  return request('/incidents', { method: 'POST', body: JSON.stringify(payload) })
}

export async function createIncidentSMS(payload: { phone: string; text: string; lat?: number; lng?: number }) {
  return request('/incidents/sms', { method: 'POST', body: JSON.stringify(payload) })
}

// --- Status ---
export async function getStatus(incidentId: string) {
  return request(`/status/${incidentId}`)
}

// --- Health ---
export async function getHealth() {
  return request('/health')
}

// --- Risk ---
export async function getRisk(bbox?: string) {
  const q = bbox ? `?bbox=${bbox}` : ''
  return request(`/risk${q}`)
}
