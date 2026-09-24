import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useHQ } from '../store'
import { startMission } from '../services/api'
import { Badge, StatusBadge } from '../components/ui'
import VoiceMic from '../components/VoiceMic'


const SEV: Record<string, string> = { info: 'text-slate-300', warning: 'text-amber-300', error: 'text-red-400' }
const FILTERS = ['ALL', 'MISSIONS', 'AGENTS', 'AI', 'SECURITY', 'QA', 'SYSTEM', 'COST']

export default function CommandCenter() {
  const { events, employees, missions, gateway, stopAll } = useHQ()
  const [objective, setObjective] = useState('')
  const [busy, setBusy] = useState(false)
  const [filter, setFilter] = useState('ALL')

  const submit = async (simulate = false) => {
    if (!objective.trim() || busy) return
    setBusy(true)
    try {
      await startMission(objective.slice(0, 60), objective, simulate)
      setObjective('')
    } finally { setBusy(false) }
  }

  const active = employees.filter((e) => e.state === 'ACTIVE')
  const filteredEvents = [...events].reverse().filter((e) => {
    if (filter === 'ALL') return true
    const map: Record<string, string[]> = {
      MISSIONS: ['MISSION'], AGENTS: ['AGENT', 'SKILL', 'TOOL'], AI: ['MODEL'],
      SECURITY: ['SECURITY', 'APPROVAL'], QA: ['QA'], SYSTEM: ['SYSTEM', 'RESOURCE', 'STOP'],
      COST: ['COST'],
    }
    return (map[filter] ?? []).some((p) => e.type.startsWith(p))
  })

  return (
    <div className="space-y-6">
      {/* Maya */}
      <section className="holo-panel p-4">
        <p className="holo-title mb-2">Maya — Chief AI Orchestrator</p>
        <div className="flex gap-2">
          <input
            className="flex-1 rounded-lg border border-cyan-500/30 bg-black/40 px-3 py-2 text-sm outline-none focus:border-cyan-400"
            placeholder='Objective दो — English, Hindi, या Hinglish ("website bana do")…'
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
            disabled={stopAll}
          />
          <VoiceMic onTranscript={(t) => setObjective(t)} />
          <button onClick={() => submit()} disabled={busy || stopAll}
            className="rounded-lg bg-cyan-500/80 px-4 py-2 text-sm font-semibold text-black hover:bg-cyan-400 disabled:opacity-40">
            {busy ? 'RUNNING…' : 'START MISSION'}
          </button>
          <button onClick={() => submit(true)} disabled={busy || stopAll}
            className="rounded-lg border border-cyan-500/40 px-4 py-2 text-sm text-cyan-300 hover:bg-cyan-500/10 disabled:opacity-40">
            SIMULATE
          </button>
        </div>
        {stopAll && <p className="mt-2 text-xs text-red-400">STOP ALL engaged — new missions blocked.</p>}
      </section>

      {/* Status strip */}
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="holo-panel p-3"><p className="holo-title">Maya</p>
          <p className="mt-1 text-sm">{employees.find((e) => e.id === 'maya')?.state ?? '—'}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Active Employees</p>
          <p className="mt-1 text-sm">{active.length} / {employees.length}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Missions</p>
          <p className="mt-1 text-sm">{missions.filter((m) => m.status === 'RUNNING').length} running · {missions.length} total</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Model Gateway</p>
          <div className="mt-1">{gateway?.status ? <StatusBadge state={gateway.status} /> : <Badge tone="muted">…</Badge>}</div></div>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Live stream */}
        <section className="holo-panel p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="holo-title">Live Data Stream</p>
            <div className="flex gap-1">
              {FILTERS.map((f) => (
                <button key={f} onClick={() => setFilter(f)}
                  className={`rounded px-2 py-0.5 text-[10px] ${filter === f ? 'bg-cyan-500/30 text-cyan-200' : 'text-slate-500'}`}>
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div className="h-96 space-y-1 overflow-y-auto text-[11px]">
            {filteredEvents.map((e) => (
              <div key={e.id} className="flex gap-2">
                <span className="text-slate-600">{new Date(e.timestamp * 1000).toLocaleTimeString()}</span>
                <span className="w-36 shrink-0 truncate text-cyan-500/70">{e.type}</span>
                <span className={SEV[e.severity] ?? 'text-slate-300'}>{e.message}</span>
              </div>
            ))}
            {filteredEvents.length === 0 && <p className="text-slate-600">No events yet — start a mission.</p>}
          </div>
        </section>

        {/* Missions */}
        <section className="holo-panel p-4">
          <p className="holo-title mb-3">Missions</p>
          <div className="h-96 space-y-2 overflow-y-auto text-xs">
            {missions.map((m) => (
              <Link key={m.id} to={`/mission/${m.id}`}
                className="block rounded-lg border border-slate-700/50 bg-black/20 p-3 hover:border-cyan-500/40">
                <div className="flex justify-between">
                  <span className="font-semibold">{m.title}</span>
                  <span className={
                    m.status === 'COMPLETED' ? 'text-emerald-400'
                    : m.status === 'FAILED' ? 'text-red-400'
                    : m.status === 'BLOCKED' ? 'text-red-500' : 'text-amber-300'}>
                    {m.status}{m.simulate ? ' (SIM)' : ''}
                  </span>
                </div>
                <p className="mt-1 text-slate-400">{m.objective}</p>
                <div className="mt-1 flex gap-3 text-slate-600">
                  <span>{m.elapsed_time}s</span>
                  {m.confidence != null && <span>conf {m.confidence}</span>}
                  <span>{m.plan.length} steps</span>
                </div>
              </Link>
            ))}
            {missions.length === 0 && <p className="text-slate-600">No missions yet.</p>}
          </div>
        </section>
      </div>
    </div>
  )
}
