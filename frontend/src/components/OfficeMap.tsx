import { useHQ } from '../store'

/**
 * Security Room / Visual Office — isometric-style room map with agent desks.
 * Each desk glows with the agent's live state. 2D (fast), not a heavy 3D render.
 */
const DESKS = [
  { id: 'maya', x: 50, y: 18 },
  { id: 'alex', x: 24, y: 46 },
  { id: 'nova', x: 50, y: 46 },
  { id: 'sam', x: 76, y: 46 },
  { id: 'rex', x: 37, y: 74 },
  { id: 'elena', x: 63, y: 74 },
]

export default function OfficeMap() {
  const { employees } = useHQ()
  const get = (id: string) => employees.find((e) => e.id === id)

  return (
    <div className="cc-panel cc-office">
      <p className="cc-title">Visual Office — Live Floor</p>
      <div className="cc-room">
        <div className="cc-room-grid" />
        {DESKS.map((d) => {
          const emp = get(d.id)
          const st = emp?.state || 'DORMANT'
          const active = st === 'ACTIVE'
          return (
            <div key={d.id} className="cc-desk" style={{ left: `${d.x}%`, top: `${d.y}%` }}>
              <div className={`cc-desk-top ${active ? 'cc-desk-on' : ''} ${st === 'SUCCESS' ? 'cc-desk-ok' : ''} ${st === 'FAILED' ? 'cc-desk-err' : ''}`}>
                <span className="cc-desk-screen" />
              </div>
              <span className={`cc-agent ${active ? 'cc-pulse' : ''}`} title={st}>
                {(emp?.name || d.id).slice(0, 1).toUpperCase()}
              </span>
              <span className="cc-desk-name">{emp?.name || d.id}</span>
            </div>
          )
        })}
      </div>
      <p className="cc-sub">{employees.filter((e) => e.state === 'ACTIVE').length} working · {employees.length} on floor</p>
    </div>
  )
}
