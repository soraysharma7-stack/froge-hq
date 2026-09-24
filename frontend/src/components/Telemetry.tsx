import { useEffect, useState } from 'react'
import { api } from '../services/api'

/** Telemetry — live CPU / RAM / agents / mode readout, polls /api/monitoring. */
export default function Telemetry() {
  const [m, setM] = useState<any>(null)

  useEffect(() => {
    let dead = false
    const load = async () => {
      try { const d = await api.get('/monitoring'); if (!dead) setM(d) } catch { /* offline */ }
    }
    load()
    const t = setInterval(load, 5000)
    return () => { dead = true; clearInterval(t) }
  }, [])

  const rows = [
    { label: 'CPU', value: m ? `${Math.round(m.cpu_percent ?? 0)}%` : '—' },
    { label: 'RAM', value: m ? `${Math.round(m.ram_percent ?? 0)}%` : '—' },
    { label: 'AGENTS', value: m ? `${m.active_employees ?? 0}/${m.max_active_agents ?? 5}` : '—' },
    { label: 'MODE', value: m?.mode ?? '—' },
    { label: 'MISSIONS', value: m ? `${m.running_missions ?? 0} live` : '—' },
  ]

  return (
    <div className="cc-panel cc-telemetry">
      <p className="cc-title">Telemetry</p>
      <div className="cc-telemetry-grid">
        {rows.map((r) => (
          <div key={r.label} className="cc-tele-item">
            <span className="cc-tele-label">{r.label}</span>
            <span className="cc-tele-value">{r.value}</span>
          </div>
        ))}
      </div>
      <div className="cc-spark">
        {(m ? [m.cpu_percent ?? 0, m.ram_percent ?? 0, (m.active_employees ?? 0) * 20, 30, 55, 40, 65] : [10, 20, 15, 30, 25, 40, 35]).map((v, i) => (
          <span key={i} className="cc-bar" style={{ height: `${Math.min(100, Math.max(6, v))}%` }} />
        ))}
      </div>
    </div>
  )
}
