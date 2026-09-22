import { useHQ } from '../store'
import type { HQEvent } from '../types'

export const api = {
  get: (path: string) => fetch(`/api${path}`).then((r) => r.json()),
  post: (path: string, body?: unknown) =>
    fetch(`/api${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    }).then((r) => r.json()),
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
