import { useHQ } from '../store'
import type { HQEvent } from '../types'

const TOKEN_KEY = 'froge_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t: string | null) =>
  t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY)

function headers(): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  const t = getToken()
  if (t) h.Authorization = `Bearer ${t}`
  return h
}

async function handle(r: Response) {
  if (r.status === 401) {
    setToken(null)
    useHQ.getState().setAuthed(false)
    throw new Error('unauthorized')
  }
  return r.json()
}

export const api = {
  get: (path: string) => fetch(`/api${path}`, { headers: headers() }).then(handle),
  post: (path: string, body?: unknown) =>
    fetch(`/api${path}`, {
      method: 'POST',
      headers: headers(),
      body: body === undefined ? undefined : JSON.stringify(body),
    }).then(handle),
}

export async function checkAuthConfig(): Promise<boolean> {
  const r = await fetch('/api/auth/config')
  const cfg = await r.json()
  return !!cfg.auth_required
}

export async function login(email: string, password: string): Promise<boolean> {
  const r = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!r.ok) return false
  const data = await r.json()
  setToken(data.access_token)
  useHQ.getState().setAuthed(true)
  return true
}

export async function signup(
  email: string,
  password: string,
  name: string,
): Promise<{ ok: boolean; error?: string }> {
  const r = await fetch('/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  })
  if (!r.ok) {
    const data = await r.json().catch(() => ({}))
    return { ok: false, error: data.detail || 'Signup failed.' }
  }
  const data = await r.json()
  setToken(data.access_token)
  useHQ.getState().setAuthed(true)
  return { ok: true }
}

export function logout() {
  setToken(null)
  useHQ.getState().setAuthed(false)
}

export async function refreshState() {
  const s = useHQ.getState()
  try {
    const [health, employees, missions, notifications] = await Promise.all([
      api.get('/health'), api.get('/employees'), api.get('/missions'), api.get('/notifications'),
    ])
    s.setGateway(health.model_gateway)
    s.setStopAll(health.stop_all_engaged)
    s.setMode(health.mode)
    s.setEmployees(employees)
    s.setMissions(missions)
    s.setNotifications(notifications)
  } catch {
    s.setMode('OFFLINE')
  }
}

export async function startMission(title: string, objective: string, simulate = false) {
  const r = await api.post('/missions', { title, objective, simulate })
  await refreshState()
  return r
}

export async function stopAll() {
  await api.post('/stop-all')
  useHQ.getState().setStopAll(true)
  await refreshState()
}

export async function releaseStopAll() {
  await api.post('/stop-all/release')
  useHQ.getState().setStopAll(false)
  await refreshState()
}

let socket: WebSocket | null = null

export function connectEvents() {
  if (socket) return
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  socket = new WebSocket(`${proto}://${location.host}/ws/events`)
  const s = useHQ.getState()
  socket.onopen = () => {
    s.setWsConnected(true)
    refreshState() // reconnect → recover state
  }
  socket.onclose = () => {
    s.setWsConnected(false)
    socket = null
    setTimeout(connectEvents, 2000) // connection recovery
  }
  socket.onmessage = (msg) => {
    const data = JSON.parse(msg.data)
    if (data.kind === 'live') {
      useHQ.getState().addEvent(data.event as HQEvent)
      if (data.event.type.startsWith('MISSION') || data.event.type === 'AGENT_ACTIVATED') {
        refreshState()
      }
      if (['APPROVAL_REQUIRED', 'SECURITY_BLOCK', 'QA_FAILURE', 'BOARDROOM_STARTED'].includes(data.event.type)) {
        refreshState()
      }
    }
  }
}
