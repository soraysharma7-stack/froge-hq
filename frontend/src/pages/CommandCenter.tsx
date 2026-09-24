import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useHQ } from '../store'
import { startMission } from '../services/api'
import VoiceMic from '../components/VoiceMic'
import OfficeMap from '../components/OfficeMap'
import Telemetry from '../components/Telemetry'
import NeuralNet from '../components/NeuralNet'
import ChatBox from '../components/ChatBox'
import Globe3D from '../components/Globe3D'

const SEV: Record<string, string> = { info: 'text-slate-300', warning: 'text-amber-300', error: 'text-red-400' }

export default function CommandCenter() {
  const { events, missions, stopAll } = useHQ()
  const [objective, setObjective] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (simulate = false) => {
    if (!objective.trim() || busy) return
    setBusy(true)
    try {
      await startMission(objective.slice(0, 60), objective, simulate)
      setObjective('')
    } finally { setBusy(false) }
  }

  const stream = [...events].reverse().slice(0, 40)

  return (
    <div className="cc-grid">
      {/* Row 1: mission control + telemetry + neural */}
      <section className="cc-panel cc-maya">
        <p className="cc-title">Maya — Chief AI Orchestrator</p>
        <div className="flex gap-2">
          <input
            className="cc-input flex-1"
            placeholder='Objective दो — English, Hindi, या Hinglish ("website bana do")…'
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
            disabled={stopAll}
          />
          <VoiceMic onTranscript={(t) => setObjective(t)} />
          <button onClick={() => submit()} disabled={busy || stopAll} className="cc-send">{busy ? 'RUNNING…' : 'START'}</button>
          <button onClick={() => submit(true)} disabled={busy || stopAll} className="cc-ghost">SIM</button>
        </div>
        {stopAll && <p className="cc-sub cc-err mt-1">STOP ALL engaged — new missions blocked.</p>}
      </section>

      <Telemetry />
      <NeuralNet />
      <Globe3D />

      {/* Row 2: office floor + live stream + chat */}
      <OfficeMap />

      <section className="cc-panel cc-stream">
        <p className="cc-title">Live Data Stream</p>
        <div className="cc-stream-log">
          {stream.length === 0 && <p className="cc-dim">No events yet — start a mission.</p>}
          {stream.map((e) => (
            <div key={e.id} className="cc-stream-line">
              <span className="cc-dim">{new Date(e.timestamp * 1000).toLocaleTimeString()}</span>
              <span className="cc-stream-type">{e.type}</span>
              <span className={SEV[e.severity] ?? 'text-slate-300'}>{e.message}</span>
            </div>
          ))}
        </div>
      </section>

      <ChatBox />

      {/* Row 3: missions strip */}
      <section className="cc-panel cc-missions">
        <p className="cc-title">Missions</p>
        <div className="cc-mission-row">
          {missions.length === 0 && <p className="cc-dim">No missions yet.</p>}
          {missions.map((m) => (
            <Link key={m.id} to={`/mission/${m.id}`} className="cc-mission-card">
              <div className="flex justify-between gap-2">
                <span className="cc-mission-name">{m.title}</span>
                <span className={m.status === 'COMPLETED' ? 'cc-ok' : m.status === 'FAILED' ? 'cc-err' : 'cc-warn'}>
                  {m.status}
                </span>
              </div>
              <p className="cc-dim cc-mission-obj">{m.objective}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
