import { useEffect, useRef, useState } from 'react'
import { useHQ } from '../store'

/**
 * Visual Office — isometric floor with WALKING agents.
 * Agents wander between desks (walking animation) and type when they stop.
 * Their desk glows with the live backend state (ACTIVE/SUCCESS/FAILED).
 */
const AGENTS = [
  { id: 'maya', color: '#f59e0b' },
  { id: 'alex', color: '#2dd4bf' },
  { id: 'nova', color: '#38bdf8' },
  { id: 'sam', color: '#34d399' },
  { id: 'rex', color: '#f43f5e' },
]

interface AgentPos {
  id: string
  x: number; y: number
  tx: number; ty: number
  state: 'walking' | 'typing'
  frame: number
  timer: number
}

export default function OfficeMap() {
  const { employees } = useHQ()
  const [agents, setAgents] = useState<AgentPos[]>(() =>
    AGENTS.map((a, i) => ({
      id: a.id,
      x: 20 + i * 12, y: 40 + (i % 2) * 20,
      tx: 20 + i * 12, ty: 40 + (i % 2) * 20,
      state: 'typing', frame: i * 2, timer: 80 + i * 30,
    })),
  )
  const rafRef = useRef<number>(0)
  const anyActive = employees.some((e) => e.state === 'ACTIVE')

  useEffect(() => {
    let last = performance.now()
    const step = (now: number) => {
      const dt = Math.min(50, now - last)
      last = now
      setAgents((prev) =>
        prev.map((a) => {
          const frame = a.frame + dt * 0.02
          if (a.state === 'walking') {
            const dx = a.tx - a.x, dy = a.ty - a.y
            const dist = Math.hypot(dx, dy)
            const speed = anyActive ? 0.06 : 0.025
            if (dist > 0.5) {
              return { ...a, frame, x: a.x + (dx / dist) * speed * dt, y: a.y + (dy / dist) * speed * dt }
            }
            return { ...a, frame, state: 'typing', timer: 120 + Math.random() * 160, x: a.tx, y: a.ty }
          }
          // typing — idle sway, then pick a new desk
          const timer = a.timer - 1
          if (timer <= 0) {
            return {
              ...a, frame, state: 'walking',
              tx: 12 + Math.random() * 76, ty: 30 + Math.random() * 55,
            }
          }
          return { ...a, frame, timer }
        }),
      )
      rafRef.current = requestAnimationFrame(step)
    }
    rafRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(rafRef.current)
  }, [anyActive])

  const get = (id: string) => employees.find((e) => e.id === id)
  const glow = (id: string) => {
    const st = get(id)?.state
    if (st === 'ACTIVE') return 'cc-agent-on'
    if (st === 'SUCCESS') return 'cc-agent-ok'
    if (st === 'FAILED') return 'cc-agent-err'
    return ''
  }

  return (
    <div className="cc-panel cc-office">
      <p className="cc-title">Visual Office — Live Floor</p>
      <div className="cc-room">
        <div className="cc-room-grid" />
        {/* desks */}
        {[{ x: 30, y: 48 }, { x: 55, y: 48 }, { x: 42, y: 68 }].map((d, i) => (
          <div key={i} className="cc-desk" style={{ left: `${d.x}%`, top: `${d.y}%` }}>
            <div className="cc-desk-top"><span className="cc-desk-screen" /></div>
          </div>
        ))}
        {/* walking agents */}
        {agents.map((a) => {
          const bounce = a.state === 'walking' ? Math.abs(Math.sin(a.frame * 2)) * 3 : Math.abs(Math.sin(a.frame * 0.5))
          const emp = get(a.id)
          return (
            <div key={a.id} className="cc-walker" style={{ left: `${a.x}%`, top: `${a.y}%`, transform: `translate(-50%,-${100 + bounce * 8}%)` }}>
              <div className={`cc-walker-body ${glow(a.id)} ${a.state === 'walking' ? 'cc-walking' : ''}`} style={{ borderColor: AGENTS.find((x) => x.id === a.id)?.color }}>
                <span className="cc-walker-head" style={{ background: AGENTS.find((x) => x.id === a.id)?.color }} />
              </div>
              <span className="cc-walker-name">{emp?.name || a.id}</span>
            </div>
          )
        })}
      </div>
      <p className="cc-sub">{employees.filter((e) => e.state === 'ACTIVE').length} working · {employees.length} on floor</p>
    </div>
  )
}
