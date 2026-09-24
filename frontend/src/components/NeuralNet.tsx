import { useEffect, useState } from 'react'
import { useHQ } from '../store'

/**
 * Neural Network — live model-gateway routing map.
 * Maya → configured model + fallbacks. Pulses when the gateway is active.
 */
export default function NeuralNet() {
  const { gateway, events } = useHQ()
  const [pulse, setPulse] = useState(false)
  const models: string[] = (gateway as any)?.candidate_models?.length
    ? (gateway as any).candidate_models
    : [(gateway as any)?.model || 'unconfigured']

  useEffect(() => {
    const last = events[events.length - 1]
    if (last && last.type.startsWith('MODEL_REQUEST')) {
      setPulse(true)
      const t = setTimeout(() => setPulse(false), 900)
      return () => clearTimeout(t)
    }
  }, [events])

  const active = (gateway as any)?.active_model || models[0]
  const status = (gateway as any)?.status || 'UNCONFIGURED'
  const on = status === 'ONLINE'

  return (
    <div className="cc-panel cc-neural">
      <p className="cc-title">Neural Network</p>
      <div className="cc-neural-map">
        <div className={`cc-node cc-node-maya ${pulse ? 'cc-pulse' : ''}`}>MAYA</div>
        <div className="cc-links">
          {models.map((m) => (
            <div key={m} className="cc-link-row">
              <span className={`cc-line ${on && m === active ? 'cc-line-on' : ''}`} />
              <div className={`cc-node ${m === active && on ? 'cc-node-on' : ''} ${pulse && m === active ? 'cc-pulse' : ''}`}>
                {m.split('/').pop()?.replace(':free', '') || m}
                {m === active && on && <span className="cc-badge-on">ACTIVE</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
      <p className="cc-sub">model gateway · <span className={on ? 'cc-ok' : 'cc-warn'}>{status}</span></p>
    </div>
  )
}
