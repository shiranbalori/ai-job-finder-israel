import { apiUrl, backendUnreachableHint } from './config'

const TOKEN_KEY = 'ajfi_access_token'

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setStoredToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* ignore */
  }
}

export interface AuthUser {
  id: number
  email: string
  full_name: string | null
  created_at: string
}

export interface AuthTokenResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

function formatNetworkError(err: unknown, fallback: string): string {
  if (err instanceof TypeError) {
    return backendUnreachableHint()
  }
  if (err instanceof Error && err.message) return err.message
  return fallback
}

function parseErrorDetail(data: unknown, fallback: string): string {
  if (!data || typeof data !== 'object') return fallback
  const d = data as { detail?: unknown; message?: string }
  if (typeof d.message === 'string') return d.message
  if (typeof d.detail === 'string') return d.detail
  if (Array.isArray(d.detail)) {
    return d.detail.map((item) => (typeof item === 'object' && item && 'msg' in item ? String((item as { msg: string }).msg) : String(item))).join('; ')
  }
  return fallback
}

export async function authRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken()
  const headers = new Headers(options.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  let res: Response
  try {
    res = await fetch(apiUrl(path), { ...options, headers })
  } catch (err) {
    throw new Error(formatNetworkError(err, 'Request failed'))
  }
  if (!res.ok) {
    const err = await res.json().catch(() => null)
    throw new Error(parseErrorDetail(err, res.statusText || 'Request failed'))
  }
  return res.json()
}

export async function registerUser(data: {
  email: string
  password: string
  full_name?: string
}): Promise<AuthTokenResponse> {
  return authRequest<AuthTokenResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      ...data,
      email: data.email.trim().toLowerCase(),
      full_name: data.full_name?.trim() || undefined,
    }),
  })
}

export async function loginUser(email: string, password: string): Promise<AuthTokenResponse> {
  const body = new URLSearchParams()
  body.set('username', email.trim().toLowerCase())
  body.set('password', password)
  let res: Response
  try {
    res = await fetch(apiUrl('/api/auth/login'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    })
  } catch (err) {
    throw new Error(formatNetworkError(err, 'Login failed'))
  }
  if (!res.ok) {
    const err = await res.json().catch(() => null)
    throw new Error(parseErrorDetail(err, 'Login failed'))
  }
  return res.json()
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  return authRequest<AuthUser>('/api/auth/me')
}

export async function logoutUser(): Promise<void> {
  try {
    await authRequest('/api/auth/logout', { method: 'POST' })
  } catch {
    /* stateless JWT — client discard is enough */
  }
}
