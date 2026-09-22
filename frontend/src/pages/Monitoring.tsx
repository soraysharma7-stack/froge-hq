import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useHQ } from '../store'

interface Mon {
  cpu_percent: number; ram_percent: number; ram_used_mb: number; ram_total_mb: number
  active_employees: number; max_active_agents: number; queue_size: number
  running_missions: number; mode: string; stop_all_engaged: boolean
  model_gateway: { status: string; provider: string | null; model: string | null; requests_served: number }
  event_log_size: number
}

function Bar({ label, value, max = 100 }: { label: string; value: number; max?: number }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div className="holo-panel p-3">
      <div className="flex justify-between text-xs"><span className="text-slate-400">{label}</span><span>{value}{max === 100 ? '%' : ''}</span></div>
      <div className="mt-2 h-2 rounded bg-slate-800">
        <div className={`h-2 rounded ${pct > 85 ? 'bg-red-500' : pct > 60 ? 'bg-amber-400' : 'bg-cyan-400'}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function Monitoring() {
  const [mon, setMon] = useState<Mon | null>(null)
  const { wsConnected } = useHQ()
  useEffect(() => {
    const load = () => api.get('/monitoring').then(setMon)
    load(); const t = setInterval(load, 2000)
    return () => clearInterval(t)
  }, [])
  if (!mon) return <p className="text-slate-500">Loading…</p>
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Bar label="CPU" value={mon.cpu_percent} />
        <Bar label={`RAM (${mon.ram_used_mb}/${mon.ram_total_mb} MB)`} value={mon.ram_percent} />
        <Bar label="Active Employees" value={mon.active_employees} max={mon.max_active_agents} />
        <Bar label="Queue" value={mon.queue_size} max={50} />
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 text-xs">
        <div className="holo-panel p-3"><p className="holo-title">WebSocket</p><p className={`mt-1 ${wsConnected ? 'text-emerald-400' : 'text-red-400'}`}>{wsConnected ? 'CONNECTED' : 'DISCONNECTED'}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">System Mode</p><p className="mt-1">{mon.mode}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Model Gateway</p><p className="mt-1">{mon.model_gateway.status} · {mon.model_gateway.requests_served} req</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Running Missions</p><p className="mt-1">{mon.running_missions}</p></div>
      </div>
    </div>
  )
}
