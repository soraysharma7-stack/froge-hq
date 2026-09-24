import { useEffect, useRef, useState } from 'react'
import { useHQ } from '../store'
import { sendChat, callBoardroom } from '../services/api'
import VoiceMic from './VoiceMic'

interface Msg { id: string; who: string; text: string; me?: boolean; model?: boolean }

/** Chat Box — real two-way chat with Maya + team leads. Mic at bottom. */
export default function ChatBox() {
  const { events, employees, stopAll } = useHQ()
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  // live agent activity also flows into the chat as context
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [msgs.length, events.length])

  const send = async () => {
    const text = draft.trim()
    if (!text || busy) return
    setDraft('')
    setMsgs((m) => [...m, { id: `u-${Date.now()}`, who: 'YOU', text, me: true }])
    setBusy(true)
    try {
      if (text.startsWith('/meet')) {
        await callBoardroom(text.replace(/^\/meet\s*/, '') || 'priorities')
        setMsgs((m) => [...m, { id: `s-${Date.now()}`, who: 'MAYA', text: 'Team leads ko bula liya — Boardroom kholo, sab apna position de rahe hain.' }])
      } else {
        const res = await sendChat(text)
        setMsgs((m) => [...m, {
          id: `a-${Date.now()}`, who: (res.from || 'maya').toUpperCase(),
          text: res.reply, model: res.model_used,
        }])
      }
    } catch {
      setMsgs((m) => [...m, { id: `e-${Date.now()}`, who: 'SYSTEM', text: 'Chat unreachable — backend offline hai kya?' }])
    } finally { setBusy(false) }
  }

  const stream = [...events].reverse().filter((e) =>
    ['DECISION_SUMMARY', 'AGENT_ACTIVATED', 'MISSION_COMPLETED', 'MISSION_FAILED'].includes(e.type),
  ).slice(0, 6)

  return (
    <div className="cc-panel cc-chat">
      <p className="cc-title">Chat Log — Team</p>
      <div ref={scrollRef} className="cc-chat-log">
        {msgs.length === 0 && stream.length === 0 && (
          <p className="cc-dim">Kuch bolo — Maya ya team lead jawab degi. Mission dene ke liye "build …" likho.</p>
        )}
        {msgs.map((m) => (
          <div key={m.id} className={`cc-chat-line ${m.me ? 'cc-chat-me' : ''}`}>
            <span className={`cc-chat-who ${m.me ? 'cc-me' : ''}`}>{m.who}</span>
            <span className={`cc-chat-text ${m.me ? 'cc-mine' : ''}`}>
              {m.text}{m.model ? ' · AI' : ''}
            </span>
          </div>
        ))}
        {busy && <p className="cc-chat-line"><span className="cc-chat-who">MAYA</span><span className="cc-chat-text cc-dim">typing…</span></p>}
        {stream.map((e) => (
          <div key={e.id} className="cc-chat-line cc-chat-sys">
            <span className="cc-chat-who cc-dim">{(e.employee_id || e.source || 'hq').toUpperCase()}</span>
            <span className={`cc-chat-text cc-dim ${e.severity === 'error' ? 'cc-err' : ''}`}>{e.message}</span>
          </div>
        ))}
      </div>
      <div className="cc-chat-input">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder={'Maya se bolo — "build a website" / "/meet"'}
          disabled={stopAll}
          className="cc-input"
        />
        <VoiceMic onTranscript={(t) => setDraft(t)} />
        <button onClick={send} disabled={busy || stopAll} className="cc-send">{busy ? '...' : 'SEND'}</button>
      </div>
      <p className="cc-sub">{employees.filter((x) => x.state === 'ACTIVE').length} agents active · {employees.length} total</p>
    </div>
  )
}
