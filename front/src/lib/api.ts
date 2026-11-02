export interface Session {
  accessToken: string
  expiresAt: number
  username: string
}

const STORAGE_KEY = 'girassol-session'
const API_URL = (import.meta.env?.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
export const SESSION_EXPIRED = 'girassol-session-expired'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export function readSession(): Session | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || 'null')
    if (value && typeof value.accessToken === 'string' && value.accessToken &&
      typeof value.username === 'string' && typeof value.expiresAt === 'number' &&
      value.expiresAt > Date.now()) return value
    sessionStorage.removeItem(STORAGE_KEY)
  } catch { /* A sessão em memória continua disponível quando o storage está bloqueado. */ }
  return null
}

export function saveSession(session: Session | null) {
  try {
    if (session) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session))
    else sessionStorage.removeItem(STORAGE_KEY)
  } catch { /* Não impedir login em navegadores com storage bloqueado. */ }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options, headers,
      signal: options.signal ? AbortSignal.any([options.signal, AbortSignal.timeout(15000)]) : AbortSignal.timeout(15000),
    })
  } catch (error) {
    if (options.signal?.aborted) throw error
    throw new ApiError('Não foi possível conectar à API. Confira se o backend está em execução.', 0)
  }
  if (response.status === 401 && token) {
    saveSession(null)
    window.dispatchEvent(new Event(SESSION_EXPIRED))
  }
  if (!response.ok) {
    let message = 'Não foi possível concluir a operação.'
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') message = body.detail
      else if (Array.isArray(body.detail)) {
        message = body.detail.map((item: { loc?: string[]; msg?: string }) =>
          `${item.loc?.slice(1).join('.') || 'Dados'}: ${item.msg || 'valor inválido'}`
        ).join('; ')
      }
    } catch { /* Respostas não JSON recebem uma mensagem genérica. */ }
    throw new ApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function login(username: string, password: string): Promise<Session> {
  const result = await apiRequest<{ access_token: string; expires_in: number }>('/auth/login', {
    method: 'POST', body: JSON.stringify({ username: username.trim(), password }),
  })
  const session = { accessToken: result.access_token, expiresAt: Date.now() + result.expires_in * 1000, username: username.trim() }
  saveSession(session)
  return session
}
