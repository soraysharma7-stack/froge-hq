import { useEffect, useRef } from 'react'
import { useHQ } from '../store'

/**
 * Earth 3D — wireframe globe with lat/long lines, orbiting satellite,
 * and pulsing hot-spots for active missions. Spins faster when agents work.
 */
export default function Globe3D() {
  const { employees } = useHQ()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const anyActive = employees.some((e) => e.state === 'ACTIVE')

  useEffect(() => {
    const cv = canvasRef.current
    if (!cv) return
    const ctx = cv.getContext('2d')
    if (!ctx) return
    let raf = 0
    let rot = 0

    const draw = () => {
      const w = (cv.width = cv.parentElement?.clientWidth || 300)
      const h = (cv.height = cv.parentElement?.clientHeight || 200)
      ctx.clearRect(0, 0, w, h)
      const cx = w / 2, cy = h / 2
      const R = Math.min(cx, cy) * 0.62
      rot += anyActive ? 0.02 : 0.005

      // atmosphere ring
      ctx.strokeStyle = 'rgba(45,212,191,0.12)'
      ctx.lineWidth = 1
      ctx.beginPath(); ctx.arc(cx, cy, R + 12, 0, Math.PI * 2); ctx.stroke()

      // sphere
      ctx.strokeStyle = 'rgba(45,212,191,0.5)'
      ctx.lineWidth = 1.2
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.stroke()

      // latitudes
      for (let i = 1; i < 8; i++) {
        const lat = (i / 8) * Math.PI
        const r = R * Math.sin(lat)
        const y = cy + R * Math.cos(lat)
        ctx.strokeStyle = 'rgba(45,212,191,0.15)'
        ctx.beginPath(); ctx.ellipse(cx, y, r, r * 0.2, 0, 0, Math.PI * 2); ctx.stroke()
      }
      // longitudes (front-facing only)
      for (let i = 0; i < 10; i++) {
        const a = (i / 10) * Math.PI * 2 + rot
        const f = Math.sin(a)
        if (Math.cos(a) > -0.15) {
          ctx.strokeStyle = 'rgba(45,212,191,0.3)'
          ctx.beginPath(); ctx.ellipse(cx, cy, R * Math.abs(f), R, 0, 0, Math.PI * 2); ctx.stroke()
        }
      }

      // hot-spots for active missions
      if (anyActive) {
        for (let i = 0; i < 3; i++) {
          const a = rot * 1.3 + i * 2.1
          const hx = cx + Math.cos(a) * R * 0.6
          const hy = cy + Math.sin(a) * R * 0.5
          const p = Math.sin(Date.now() * 0.006 + i) * 0.5 + 0.5
          ctx.beginPath(); ctx.arc(hx, hy, 3 + p * 3, 0, Math.PI * 2)
          ctx.strokeStyle = `rgba(94,234,212,${0.3 + p * 0.6})`; ctx.stroke()
        }
      }

      // orbiting satellite
      const sa = rot * 1.6
      const sx = cx + Math.cos(sa) * (R + 20)
      const sy = cy + Math.sin(sa) * (R * 0.42)
      ctx.fillStyle = '#5eead4'
      ctx.beginPath(); ctx.arc(sx, sy, 2.5, 0, Math.PI * 2); ctx.fill()
      ctx.strokeStyle = 'rgba(94,234,212,0.3)'
      ctx.setLineDash([2, 3])
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(sx, sy); ctx.stroke()
      ctx.setLineDash([])

      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(raf)
  }, [anyActive])

  return (
    <div className="cc-panel cc-globe">
      <p className="cc-title">Earth 3D — Operations Globe</p>
      <div className="cc-globe-canvas"><canvas ref={canvasRef} /></div>
      <p className="cc-sub">{anyActive ? 'missions live — tracking' : 'standby'}</p>
    </div>
  )
}
