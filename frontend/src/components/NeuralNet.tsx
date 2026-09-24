import { useEffect, useRef } from 'react'
import { useHQ } from '../store'

/**
 * Neural Network — live model-gateway routing map with PULSING synapses.
 * Signals travel through connections when a model request fires.
 */
export default function NeuralNet() {
  const { gateway, events } = useHQ()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const activeRef = useRef(false)

  const models: string[] = (gateway as any)?.candidate_models?.length
    ? (gateway as any).candidate_models
    : [(gateway as any)?.model || 'unconfigured']
  const active = (gateway as any)?.active_model || models[0]
  const online = (gateway as any)?.status === 'ONLINE'

  // pulse when a model request fires
  useEffect(() => {
    const last = events[events.length - 1]
    if (last && last.type.startsWith('MODEL_REQUEST')) {
      activeRef.current = true
      const t = setTimeout(() => { activeRef.current = false }, 1200)
      return () => clearTimeout(t)
    }
  }, [events])

  useEffect(() => {
    const cv = canvasRef.current
    if (!cv) return
    const ctx = cv.getContext('2d')
    if (!ctx) return

    let raf = 0
    const draw = () => {
      const w = (cv.width = cv.parentElement?.clientWidth || 300)
      const h = (cv.height = cv.parentElement?.clientHeight || 180)
      ctx.clearRect(0, 0, w, h)
      const t = Date.now() * 0.003
      const cx = w * 0.22
      const cy = h / 2

      // Maya node (left)
      const mayaPulse = activeRef.current ? Math.sin(t * 4) * 0.5 + 0.5 : 0
      ctx.beginPath()
      ctx.arc(cx, cy, 12 + mayaPulse * 3, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(245,158,11,0.15)'
      ctx.fill()
      ctx.strokeStyle = '#f59e0b'
      ctx.lineWidth = 1.5
      ctx.stroke()
      ctx.fillStyle = '#fcd34d'
      ctx.font = '8px monospace'
      ctx.textAlign = 'center'
      ctx.fillText('MAYA', cx, cy + 3)

      // model nodes (right)
      const mx = w * 0.75
      models.forEach((m, i) => {
        const my = h * 0.25 + i * (h * 0.5 / Math.max(1, models.length - 1 || 1))
        const isActive = online && m === active
        const flow = (Math.sin(t * 3 - i) * 0.5 + 0.5)

        // synapse line
        ctx.beginPath()
        ctx.moveTo(cx + 12, cy)
        ctx.lineTo(mx - 10, my)
        ctx.strokeStyle = isActive
          ? `rgba(45,212,191,${0.3 + flow * 0.6})`
          : 'rgba(45,212,191,0.12)'
        ctx.lineWidth = isActive ? 1.5 : 1
        ctx.stroke()

        // traveling signal packet on active synapse
        if (isActive && activeRef.current) {
          const p = (t * 0.8) % 1
          const px = cx + 12 + (mx - 10 - (cx + 12)) * p
          const py = cy + (my - cy) * p
          ctx.beginPath()
          ctx.arc(px, py, 2.5, 0, Math.PI * 2)
          ctx.fillStyle = '#5eead4'
          ctx.fill()
        }

        // node
        ctx.beginPath()
        ctx.arc(mx, my, isActive ? 8 + flow * 2 : 6, 0, Math.PI * 2)
        ctx.fillStyle = isActive ? 'rgba(45,212,191,0.2)' : 'rgba(0,0,0,0.5)'
        ctx.fill()
        ctx.strokeStyle = isActive ? '#2dd4bf' : 'rgba(45,212,191,0.3)'
        ctx.lineWidth = isActive ? 1.5 : 1
        ctx.stroke()
        ctx.fillStyle = isActive ? '#5eead4' : '#64748b'
        ctx.font = '7px monospace'
        ctx.fillText(m.split('/').pop()?.replace(':free', '') || m, mx, my + 16)
      })

      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(raf)
  }, [models.join(','), active, online])

  return (
    <div className="cc-panel cc-neural">
      <p className="cc-title">Neural Network</p>
      <div className="cc-neural-canvas"><canvas ref={canvasRef} /></div>
      <p className="cc-sub">model gateway · <span className={online ? 'cc-ok' : 'cc-warn'}>{(gateway as any)?.status || 'UNCONFIGURED'}</span></p>
    </div>
  )
}
