import {
  IncidentCreatePayload,
  IncidentOut,
  IncidentStatusResponse,
  RiskZoneOut,
  DecisionRequest,
  DecisionResponse,
  WhatIfRequest,
  WhatIfResponse,
  AuthStatus,
  AuthInfo,
} from '../types/api'

export type { AuthStatus, AuthInfo }

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
      const decoded = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
      if (decoded && typeof decoded === 'object') {
        return decoded
      }
    }
  } catch {
    // ignore
  }
  return null
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeTokenPayload(token)
  if (!payload || typeof payload.exp !== 'number') return true
  return payload.exp * 1000 < Date.now() + 5000
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
  if (typeof localStorage !== 'undefined') {
    authToken = localStorage.getItem('crisiscore_token')
  }
  if (authToken && isTokenExpired(authToken)) {
    logout()
    return null
  }
  return authToken
}

export function getAuthInfo(): AuthInfo {
  if (typeof localStorage !== 'undefined') {
    authToken = localStorage.getItem('crisiscore_token')
  }
  if (!authToken) {
    return { status: 'unauthenticated', role: null, token: null }
  }
  if (isTokenExpired(authToken)) {
    logout()
    return { status: 'unauthenticated', role: null, token: null }
  }
  const payload = decodeTokenPayload(authToken)
  const role = payload?.role || null
  if (role === 'officer' || role === 'admin') {
    return { status: 'authenticated', role, token: authToken }
  }
  if (role === 'citizen') {
    return { status: 'access_required', role: 'citizen', token: authToken }
  }
  logout()
  return { status: 'unauthenticated', role: null, token: null }
}

export function getUserRole(): string | null {
  return getAuthInfo().role
}

export function isOperationsRole(role: string | null): boolean {
  return role === 'officer' || role === 'admin'
}

export function isOperationsUser(): boolean {
  return isOperationsRole(getUserRole())
}

export interface RequestOptions extends RequestInit {
  retries?: number
  retryDelayMs?: number
  skipAuth?: boolean
}

async function request(path: string, opts: RequestOptions = {}) {
  const { retries = 0, retryDelayMs = 800, skipAuth = false, ...fetchOpts } = opts
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOpts.headers as Record<string, string> || {}),
  }

  if (!skipAuth) {
    const token = getAuthToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  let attempt = 0
  while (true) {
    try {
      const res = await fetch(apiUrl(path), { ...fetchOpts, headers })
      if (!res.ok) {
        if (res.status === 401) {
          // Explicitly clear session on 401; never retry 401 indefinitely
          logout()
          const txt = await res.text().catch(() => '')
          const err = new Error(`401 Unauthorized: ${txt}`)
          ;(err as any).status = 401
          throw err
        }

        // Transient gateway/server startup codes (502, 503, 504)
        if ((res.status === 502 || res.status === 503 || res.status === 504) && attempt < retries) {
          attempt++
          await new Promise((resolve) => setTimeout(resolve, retryDelayMs * attempt))
          continue
        }

        const txt = await res.text().catch(() => '')
        const err = new Error(`${res.status} ${txt}`)
        ;(err as any).status = res.status
        throw err
      }
      return res.json().catch(() => ({}))
    } catch (err: any) {
      // Never retry 401
      if (err?.status === 401 || err?.message?.includes('401')) {
        throw err
      }

      // Retry transient network errors (Failed to fetch, backend startup delay)
      if (attempt < retries) {
        attempt++
        await new Promise((resolve) => setTimeout(resolve, retryDelayMs * attempt))
        continue
      }
      throw err
    }
  }
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
  limit?: number,
  retries = 2
): Promise<IncidentOut[]> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (bbox) params.set('bbox', bbox)
  if (limit !== undefined) params.set('limit', String(limit))
  const q = params.toString() ? `?${params.toString()}` : ''
  return request(`/incidents${q}`, { retries, retryDelayMs: 900 })
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
export async function getHealth(retries = 2) {
  return request('/health', { retries, retryDelayMs: 800, skipAuth: true })
}

// --- Risk ---
export async function getRisk(
  bbox?: string,
  horizon: string = '24h',
  retries = 2
): Promise<RiskZoneOut[]> {
  const params = new URLSearchParams()
  if (bbox) params.set('bbox', bbox)
  if (horizon) params.set('horizon', horizon)
  const q = params.toString() ? `?${params.toString()}` : ''
  return request(`/risk${q}`, { retries, retryDelayMs: 900 })
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
