import { useEffect, useState } from 'react'
import { api } from '../services/api'

export function SkillsPage() {
  const [skills, setSkills] = useState<{ id: string; name: string; description: string; permissions: string[] }[]>([])
  useEffect(() => { api.get('/skills').then(setSkills) }, [])
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      {skills.map((s) => (
        <div key={s.id} className="holo-panel p-4 text-xs">
          <p className="font-semibold text-cyan-200">{s.name}</p>
          <p className="mt-1 text-slate-400">{s.description}</p>
          <p className="mt-2 text-slate-500">permissions: {s.permissions.join(', ')}</p>
        </div>
      ))}
    </div>
  )
}

export function QAPage() {
  const [qa, setQa] = useState<{ summary: { total: number; passed: number; failed: number; pass_rate: number | null }; checks: { id: string; kind: string; target: string; status: string; timestamp: number }[]; unresolved_failures: unknown[] } | null>(null)
  useEffect(() => { const l = () => api.get('/qa').then(setQa); l(); const t = setInterval(l, 3000); return () => clearInterval(t) }, [])
  if (!qa) return <p className="text-slate-500">Loading…</p>
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3 text-xs">
        <div className="holo-panel p-3"><p className="holo-title">Total Checks</p><p className="mt-1 text-lg">{qa.summary.total}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Passed</p><p className="mt-1 text-lg text-emerald-400">{qa.summary.passed}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Failed</p><p className="mt-1 text-lg text-red-400">{qa.summary.failed}</p></div>
      </div>
      <p className="text-[11px] text-slate-500">Rule: never declare success without evidence.</p>
      <div className="space-y-1 text-[11px]">
        {qa.checks.map((c) => (
          <div key={c.id} className="flex gap-3 holo-panel p-2">
            <span className={c.status === 'PASSED' ? 'text-emerald-400' : 'text-red-400'}>{c.status}</span>
            <span className="text-slate-400">{c.kind}</span>
            <span className="truncate text-slate-500">{c.target}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ModelGatewayPage() {
  const [gw, setGw] = useState<{ provider: string | null; model: string | null; status: string; requests_served: number } | null>(null)
  useEffect(() => { const l = () => api.get('/model-gateway').then(setGw); l(); const t = setInterval(l, 3000); return () => clearInterval(t) }, [])
  if (!gw) return <p className="text-slate-500">Loading…</p>
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 text-xs">
        <div className="holo-panel p-3"><p className="holo-title">Status</p><p className={`mt-1 text-sm ${gw.status === 'ONLINE' ? 'text-emerald-400' : 'text-amber-400'}`}>{gw.status}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Provider</p><p className="mt-1 text-sm">{gw.provider ?? 'not configured'}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Model</p><p className="mt-1 text-sm">{gw.model ?? 'not configured'}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Requests Served</p><p className="mt-1 text-sm">{gw.requests_served}</p></div>
      </div>
      <div className="holo-panel p-4 text-xs text-slate-400 space-y-1">
        <p>No model is hard-coded. Configure via environment:</p>
        <p className="font-mono text-cyan-300">FROGE_MODEL_PROVIDER=arena FROGE_MODEL_NAME=&lt;your-arena-model&gt; FROGE_MODEL_API_BASE=&lt;endpoint&gt;</p>
        {gw.status !== 'ONLINE' && <p className="text-amber-400">Degraded state shown instead of silently switching models.</p>}
      </div>
    </div>
  )
}

export function ArtifactsPage() {
  const [arts, setArts] = useState<{ id: string; type: string; title: string; creator: string; version: number; location: string; status: string; created_at: number }[]>([])
  useEffect(() => { const l = () => api.get('/artifacts').then(setArts); l(); const t = setInterval(l, 3000); return () => clearInterval(t) }, [])
  return (
    <div className="space-y-2">
      {arts.map((a) => (
        <div key={a.id} className="holo-panel p-3 text-xs flex justify-between">
          <div><p className="font-semibold text-slate-200">{a.title}</p>
            <p className="text-slate-500">{a.type} · by {a.creator} · v{a.version} · {a.location}</p></div>
          <span className="text-emerald-400">{a.status}</span>
        </div>
      ))}
      {arts.length === 0 && <p className="text-xs text-slate-600">No artifacts yet — complete a mission.</p>}
    </div>
  )
}

export function DecisionsPage() {
  const [decs, setDecs] = useState<{ id: string; decision: string; context: string; status: string; owner: string; version: number; risks: string[] }[]>([])
  const [decision, setDecision] = useState('')
  const [ctx, setCtx] = useState('')
  const load = () => api.get('/decisions').then(setDecs)
  useEffect(() => { load() }, [])
  const add = async () => {
    if (!decision.trim()) return
    await api.post('/decisions', { decision, context: ctx, owner: 'user', reasoning_summary: 'Recorded by user' })
    setDecision(''); setCtx(''); load()
  }
  return (
    <div className="space-y-4">
      <div className="holo-panel p-3 flex gap-2">
        <input value={decision} onChange={(e) => setDecision(e.target.value)} placeholder="Decision…"
          className="flex-1 rounded-lg border border-cyan-500/30 bg-black/40 px-3 py-2 text-xs outline-none" />
        <input value={ctx} onChange={(e) => setCtx(e.target.value)} placeholder="Context…"
          className="flex-1 rounded-lg border border-cyan-500/30 bg-black/40 px-3 py-2 text-xs outline-none" />
        <button onClick={add} className="rounded-lg bg-cyan-500/80 px-3 text-xs font-semibold text-black">RECORD ADR</button>
      </div>
      {decs.map((d) => (
        <div key={d.id} className="holo-panel p-3 text-xs">
          <div className="flex justify-between"><p className="font-semibold text-slate-200">{d.decision}</p>
            <span className="text-slate-500">v{d.version} · {d.status} · {d.owner}</span></div>
          <p className="mt-1 text-slate-400">{d.context}</p>
        </div>
      ))}
    </div>
  )
}

export function SettingsPage() {
  const [cfg, setCfg] = useState<Record<string, unknown> | null>(null)
  useEffect(() => { api.get('/config').then(setCfg) }, [])
  if (!cfg) return <p className="text-slate-500">Loading…</p>
  return (
    <div className="holo-panel p-4 text-xs space-y-2">
      <p className="holo-title">Configuration (from environment — FROGE_ prefix)</p>
      {Object.entries(cfg).map(([k, v]) => (
        <div key={k} className="flex justify-between border-b border-slate-800 py-1">
          <span className="text-slate-500">{k}</span>
          <span className="text-slate-200 font-mono">{JSON.stringify(v)}</span>
        </div>
      ))}
    </div>
  )
}
