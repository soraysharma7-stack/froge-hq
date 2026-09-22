import { useEffect, useState } from 'react'
import { api } from '../services/api'

interface Position { participant: string; position: string; evidence: string; risk: string; confidence: number; recommendation: string }
interface Session { id: string; topic: string; called_by: string; status: string; positions: Position[]; synthesis: string | null; created_at: number }

export default function Boardroom() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [topic, setTopic] = useState('')

  const load = () => api.get('/boardroom').then(setSessions)
  useEffect(() => { load() }, [])

  const call = async () => {
    if (!topic.trim()) return
    await api.post('/boardroom', { topic })
    setTopic('')
    load()
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        <input value={topic} onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && call()}
          placeholder="Topic for deliberation…"
          className="flex-1 rounded-lg border border-cyan-500/30 bg-black/40 px-3 py-2 text-sm outline-none focus:border-cyan-400" />
        <button onClick={call} className="rounded-lg bg-purple-500/70 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-400">
          CALL BOARDROOM
        </button>
      </div>
      {sessions.map((s) => (
        <div key={s.id} className="holo-panel p-4 space-y-3">
          <div className="flex justify-between">
            <p className="font-semibold text-purple-200">{s.topic}</p>
            <span className="text-xs text-slate-500">{s.status} · by {s.called_by}</span>
          </div>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {s.positions.map((p) => (
              <div key={p.participant} className="rounded-lg border border-slate-700/50 bg-black/30 p-3 text-xs">
                <p className="font-semibold text-cyan-300">{p.participant} <span className="text-slate-500">(conf {p.confidence}, risk {p.risk})</span></p>
                <p className="mt-1 text-slate-300">{p.position}</p>
                <p className="mt-1 text-slate-500">{p.evidence}</p>
              </div>
            ))}
          </div>
          {s.synthesis && <p className="rounded-lg bg-purple-500/10 p-3 text-xs text-purple-200">{s.synthesis}</p>}
        </div>
      ))}
      {sessions.length === 0 && <p className="text-xs text-slate-600">No boardroom sessions yet.</p>}
    </div>
  )
}
