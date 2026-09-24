import { useEffect, useRef, useState } from 'react'
import { useHQ } from '../store'
import { startMission, callBoardroom } from '../services/api'
import VoiceMic from './VoiceMic'

/** Chat Box — talk to Maya + team leads. Mic at bottom, like the reference. */
export default function ChatBox() {
  const { events, employees, stopAll } = useHQ()
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const chatEvents = [...events].reverse().filter((e) =>
    ['DECISION_SUMMARY', 'BOARDROOM_STARTED', 'MISSION_COMPLETED', 'MISSION_FAILED', 'AGENT_ACTIVATED'].includes(e.type),
  ).slice(0, 40)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [chatEvents.length])

  const send = async () => {
    const text = draft.trim()
    if (!text || busy) return
    setBusy(true)
    try {
      if (text.startsWith('/meet')) await callBoardroom(text.replace(/^\/meet\s*/, '') || 'priorities')
      else await startMission(text.slice(0, 60), text, false)
      setDraft('')
    } finally { setBusy(false) }
  }

  return (
    <div className="cc-panel cc-chat">
      <p className="cc-title">Chat Log — Team</p>
      <div ref={scrollRef} className="cc-chat-log">
        {chatEvents.length === 0 && <p className="cc-dim">No messages yet — give Maya a mission or start a meeting.</p>}
        {chatEvents.map((e) => (
          <div key={e.id} className="cc-chat-line">
            <span className="cc-chat-who">{(e.employee_id || e.source || 'hq').toUpperCase()}</span>
            <span className={`cc-chat-text ${e.severity === 'error' ? 'cc-err' : ''}`}>{e.message}</span>
          </div>
        ))}
      </div>
      <div className="cc-chat-input">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Type or speak a command…  (/meet to call the leads)"
          disabled={stopAll}
          className="cc-input"
        />
        <VoiceMic onTranscript={(t) => setDraft(t)} />
        <button onClick={send} disabled={busy || stopAll} className="cc-send">{busy ? '…' : 'SEND'}</button>
      </div>
      <p className="cc-sub">{employees.filter((x) => x.state === 'ACTIVE').length} agents active · {employees.length} total</p>
    </div>
  )
}
