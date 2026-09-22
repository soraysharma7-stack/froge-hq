import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { useHQ } from '../store'
import type { Department } from '../types'

export default function Office() {
  const [departments, setDepartments] = useState<Department[]>([])
  const { employees } = useHQ()

  useEffect(() => {
    const load = () => api.get('/departments').then(setDepartments)
    load()
    const t = setInterval(load, 3000)
    return () => clearInterval(t)
  }, [])

  return (
    <div>
      <p className="holo-title mb-4">Visual Office — live organization state</p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {departments.map((d) => {
          const anyActive = d.employees.some((e) => e.state === 'ACTIVE')
          return (
            <Link key={d.id} to={`/department/${d.id}`}
              className={`rounded-xl border p-4 transition-all ${
                anyActive
                  ? 'border-cyan-400/60 bg-cyan-500/10 shadow-[0_0_20px_rgba(34,211,238,0.25)]'
                  : 'border-slate-700/50 bg-black/20 hover:border-cyan-500/30'}`}>
              <p className="text-sm font-semibold text-slate-200">{d.name}</p>
              <p className="mt-1 text-[10px] text-slate-500">lead: {d.lead ?? '—'}</p>
              <div className="mt-2 space-y-1">
                {d.employees.map((e) => (
                  <p key={e.id} className="flex items-center gap-1.5 text-[11px] text-slate-400">
                    <span className={`status-dot ${e.state === 'ACTIVE' ? 'bg-cyan-400 animate-pulse' : e.state === 'SUCCESS' ? 'bg-emerald-500' : e.state === 'FAILED' ? 'bg-red-500' : 'bg-slate-600'}`} />
                    {e.name} · {e.state}
                  </p>
                ))}
                {d.employees.length === 0 && <p className="text-[10px] text-slate-600">no staff</p>}
              </div>
            </Link>
          )
        })}
      </div>
      <section className="holo-panel mt-6 p-4">
        <p className="holo-title mb-2">Agent Graph — live hierarchy</p>
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          <span className="rounded bg-cyan-500/20 px-2 py-1 text-cyan-200">USER</span><span>→</span>
          <span className={`rounded px-2 py-1 ${employees.find((e) => e.id === 'maya')?.state === 'ACTIVE' ? 'bg-cyan-400/40 text-cyan-100 animate-pulse' : 'bg-slate-700/40 text-slate-300'}`}>MAYA</span><span>→</span>
          <span className="rounded bg-slate-700/40 px-2 py-1 text-slate-300">DEPARTMENTS</span><span>→</span>
          {employees.filter((e) => e.id !== 'maya').map((e) => (
            <span key={e.id} className={`rounded px-2 py-1 ${e.state === 'ACTIVE' ? 'bg-cyan-400/40 text-cyan-100 animate-pulse' : e.state === 'SUCCESS' ? 'bg-emerald-500/30 text-emerald-200' : 'bg-slate-700/40 text-slate-400'}`}>
              {e.name.toUpperCase()}
            </span>
          ))}
          <span>→</span><span className="rounded bg-slate-700/40 px-2 py-1 text-slate-300">SKILLS → TOOLS → RESULT</span>
        </div>
        <p className="mt-2 text-[10px] text-slate-600">Graph driven by real backend events — active nodes pulse.</p>
      </section>
    </div>
  )
}
