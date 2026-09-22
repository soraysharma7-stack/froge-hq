import { useEffect, useState } from 'react'
import { api, refreshState } from '../services/api'

export default function Security() {
  const [overview, setOverview] = useState<{ rules: Record<string, unknown>; blocked: { timestamp: number; action: string; actor: string; reason: string }[] } | null>(null)
  const [approvals, setApprovals] = useState<{ id: string; action: string; requester: string; risk: string; reason: string; state: string }[]>([])

  const load = () => {
    api.get('/security').then(setOverview)
    api.get('/approvals').then(setApprovals)
  }
  useEffect(() => { load(); const t = setInterval(load, 3000); return () => clearInterval(t) }, [])

  const resolve = async (id: string, state: string) => {
    await api.post(`/approvals/${id}/resolve`, { state, resolver: 'user' })
    load(); refreshState()
  }

  return (
    <div className="space-y-6">
      <section className="holo-panel p-4">
        <p className="holo-title mb-3">Pending Approvals</p>
        {approvals.filter((a) => a.state === 'PENDING').map((a) => (
          <div key={a.id} className="mb-2 flex items-center justify-between rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-xs">
            <div>
              <p className="font-semibold text-amber-200">{a.action} <span className="text-slate-500">({a.risk})</span></p>
              <p className="text-slate-400">by {a.requester} — {a.reason || 'no reason given'}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => resolve(a.id, 'APPROVED')} className="rounded bg-emerald-500/70 px-3 py-1 text-black">APPROVE</button>
              <button onClick={() => resolve(a.id, 'DENIED')} className="rounded bg-red-500/70 px-3 py-1 text-white">DENY</button>
            </div>
          </div>
        ))}
        {approvals.filter((a) => a.state === 'PENDING').length === 0 && <p className="text-xs text-slate-600">No pending approvals.</p>}
      </section>

      <section className="holo-panel p-4">
        <p className="holo-title mb-3">Security Rules (deterministic, backend-enforced)</p>
        {overview && (
          <div className="grid grid-cols-1 gap-3 text-xs md:grid-cols-2">
            <div>
              <p className="text-red-400 mb-1">Hard-blocked actions</p>
              {(overview.rules.hard_blocked as string[]).map((a) => <p key={a} className="text-slate-400">✕ {a}</p>)}
            </div>
            <div>
              <p className="text-amber-400 mb-1">Approval required</p>
              {(overview.rules.approval_required as string[]).map((a) => <p key={a} className="text-slate-400">⚠ {a}</p>)}
              <p className="mt-2 text-slate-500">Sandbox: {overview.rules.sandbox as string}</p>
            </div>
          </div>
        )}
      </section>

      <section className="holo-panel p-4">
        <p className="holo-title mb-3">Blocked Actions Log</p>
        <div className="space-y-1 text-[11px]">
          {overview?.blocked.map((b, i) => (
            <p key={i} className="text-red-300/80">
              {new Date(b.timestamp * 1000).toLocaleTimeString()} — {b.actor} tried '{b.action}' — {b.reason || 'hard-blocked'}
            </p>
          ))}
          {(!overview || overview.blocked.length === 0) && <p className="text-slate-600">Nothing blocked yet.</p>}
        </div>
      </section>
    </div>
  )
}
