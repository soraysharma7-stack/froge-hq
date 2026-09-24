import { useEffect, useState } from 'react'
import { api } from '../services/api'

interface Agent {
  id: string
  name: string
  role: string
  department: string
  specialty: string
}

interface RosterData {
  total: number
  agents: Agent[]
  leads: string[]
  departments: string[]
}

const DEPT_LABELS: Record<string, string> = {
  software_engineering: 'Software Engineering',
  marketing: 'Marketing & Growth',
  aerospace: 'Space & Aerospace',
  ai_research: 'AI Research & Intelligence',
  creative: 'Creative, 3D & Media',
  research: 'Research, Science & Knowledge',
  qa: 'QA, Security & Safety',
  security: 'Security & Safety',
  devops: 'DevOps & Infrastructure',
  orchestration: 'Business & Operations',
  operations: 'Business & Operations',
  client_services: 'Client & Web Services',
  ml_data: 'ML & Data Science',
}

export default function Agents() {
  const [data, setData] = useState<RosterData | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const [search, setSearch] = useState('')

  useEffect(() => {
    api.get('/roster').then((d) => { setData(d); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="cc-panel p-4"><p className="cc-dim">Loading 115 agents…</p></div>
  if (!data) return <div className="cc-panel p-4"><p className="cc-err">Could not load roster — backend offline?</p></div>

  const departments = data.departments
  const filtered = data.agents.filter((a) => {
    if (filter !== 'all' && a.department !== filter) return false
    if (search && !`${a.name} ${a.role} ${a.specialty}`.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div className="space-y-4">
      <div className="cc-panel p-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="cc-title">Full Agent Roster — {data.total} agents</p>
            <p className="cc-sub">11 departments · idle until Maya routes a task · one universal template + this data table</p>
          </div>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search agents…"
            className="cc-input w-48"
          />
        </div>
        <div className="mt-3 flex flex-wrap gap-1">
          <button onClick={() => setFilter('all')}
            className={`rounded px-2 py-1 text-[10px] font-mono ${filter === 'all' ? 'bg-cyan-500/30 text-cyan-200' : 'text-slate-500'}`}>
            ALL ({data.total})
          </button>
          {departments.map((d) => (
            <button key={d} onClick={() => setFilter(d)}
              className={`rounded px-2 py-1 text-[10px] font-mono ${filter === d ? 'bg-cyan-500/30 text-cyan-200' : 'text-slate-500'}`}>
              {DEPT_LABELS[d] || d}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((a) => (
          <div key={a.id} className={`cc-panel p-3 ${data.leads.includes(a.id) ? 'border-amber-500/40' : ''}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className={`flex h-7 w-7 items-center justify-center rounded border font-mono text-[10px] ${data.leads.includes(a.id) ? 'border-amber-500/60 text-amber-300' : 'border-cyan-500/40 text-cyan-300'}`}>
                  {a.name.slice(0, 1)}
                </div>
                <div>
                  <p className="font-mono text-xs font-bold text-slate-200">{a.name}</p>
                  <p className="font-mono text-[9px] text-slate-500">{a.role}</p>
                </div>
              </div>
              {data.leads.includes(a.id) && <span className="rounded bg-amber-500/20 px-1 font-mono text-[8px] text-amber-300">LEAD</span>}
            </div>
            <p className="mt-2 font-mono text-[9px] text-slate-500">{a.specialty}</p>
            <p className="mt-1 font-mono text-[8px] text-cyan-600">{DEPT_LABELS[a.department] || a.department}</p>
          </div>
        ))}
      </div>
      {filtered.length === 0 && <p className="cc-dim text-center">No agents match.</p>}
    </div>
  )
}
