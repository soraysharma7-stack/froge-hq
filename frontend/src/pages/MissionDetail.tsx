import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api'
import type { Mission } from '../types'

export default function MissionDetail() {
  const { id } = useParams()
  const [mission, setMission] = useState<Mission | null>(null)

  useEffect(() => {
    const load = () => api.get(`/missions/${id}`).then(setMission).catch(() => setMission(null))
    load()
    const t = setInterval(load, 2000)
    return () => clearInterval(t)
  }, [id])

  if (!mission) return <p className="text-slate-500">Loading mission…</p>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-cyan-200">{mission.title}</h2>
          <p className="text-xs text-slate-500">{mission.objective}</p>
        </div>
        <span className={`rounded-lg px-3 py-1 text-sm ${mission.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300' : mission.status === 'FAILED' ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'}`}>
          {mission.status}{mission.simulate ? ' (SIMULATION — no execution)' : ''}
        </span>
      </div>

      {mission.final_summary && (
        <div className="holo-panel p-4 text-sm text-slate-300">{mission.final_summary}</div>
      )}
      {mission.errors.length > 0 && (
        <div className="holo-panel border-red-500/30 p-4 text-sm text-red-400">
          {mission.errors.map((e, i) => <p key={i}>{e}</p>)}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="holo-panel p-4">
          <p className="holo-title mb-3">Plan</p>
          {mission.plan.map((s) => (
            <div key={s.step} className="mb-2 flex items-center gap-3 text-xs">
              <span className={`status-dot ${s.status === 'done' ? 'bg-emerald-500' : s.status === 'failed' ? 'bg-red-500' : 'bg-slate-600'}`} />
              <span className="text-slate-400">Step {s.step}</span>
              <span className="text-cyan-400">{s.owner}</span>
              <span className="text-slate-300">{s.action}</span>
              <span className="text-slate-600">{s.status}</span>
            </div>
          ))}
          <p className="mt-3 text-[10px] text-slate-600">
            confidence: {mission.confidence ?? '—'} · elapsed: {mission.elapsed_time}s · employees: {mission.active_employees.join(', ') || '—'}
          </p>
        </section>

        <section className="holo-panel p-4">
          <p className="holo-title mb-3">Mission Replay (read-only — tools never re-execute)</p>
          <div className="max-h-72 space-y-1 overflow-y-auto text-[11px]">
            {mission.timeline.map((t, i) => (
              <div key={i} className="flex gap-2">
                <span className="text-slate-600">{new Date(t.t * 1000).toLocaleTimeString()}</span>
                <span className="w-40 shrink-0 text-cyan-500/70">{t.step}</span>
                <span className="text-slate-400">{t.detail}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="holo-panel p-4">
        <p className="holo-title mb-2">Explainability</p>
        <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 md:grid-cols-4">
          <span>WHAT: {mission.plan.map((p) => p.action).join(' → ')}</span>
          <span>WHY: {mission.objective}</span>
          <span>TOOL: workspace_file_write / verify</span>
          <span>RESULT: {mission.status}</span>
        </div>
      </section>
    </div>
  )
}
