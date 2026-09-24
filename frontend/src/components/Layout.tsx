import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useHQ } from '../store'
import { connectEvents, refreshState, stopAll as stopAllApi, releaseStopAll, callBoardroom } from '../services/api'
import CommandPalette from './CommandPalette'

const NAV = [
  ['/', 'Command Center'], ['/office', 'Office'], ['/boardroom', 'Boardroom'],
  ['/model-gateway', 'Model Gateway'], ['/memory', 'Memory'], ['/skills', 'Skills'],
  ['/security', 'Security'], ['/qa', 'QA'], ['/monitoring', 'Monitoring'],
  ['/artifacts', 'Artifacts'], ['/decisions', 'Decisions'], ['/settings', 'Settings'],
]

export default function Layout() {
  const { wsConnected, stopAll, mode, gateway, notifications } = useHQ()
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [meetingBusy, setMeetingBusy] = useState(false)
  const navigate = useNavigate()
  const unread = notifications.filter((n) => !n.read).length

  const meeting = async () => {
    const topic = window.prompt('Meeting topic — team leads kya discuss karein?', 'Current priorities & next steps')
    if (!topic || meetingBusy) return
    setMeetingBusy(true)
    try { await callBoardroom(topic) } finally { setMeetingBusy(false) }
    navigate('/boardroom')
  }

  useEffect(() => {
    refreshState()
    connectEvents()
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setPaletteOpen((v) => !v)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <div className="flex min-h-screen">
      <aside className="w-52 shrink-0 border-r border-cyan-500/15 bg-black/30 p-4 space-y-1">
        <h1 className="mb-4 text-lg font-bold tracking-widest text-cyan-300">FROGÉ HQ</h1>
        {NAV.map(([to, label]) => (
          <NavLink key={to} to={to} end={to === '/'}
            className={({ isActive }) =>
              `block rounded-md px-3 py-1.5 text-xs ${isActive ? 'bg-cyan-500/20 text-cyan-200' : 'text-slate-400 hover:text-slate-200'}`}>
            {label}
          </NavLink>
        ))}
        <button onClick={() => setPaletteOpen(true)}
          className="mt-4 w-full rounded-md border border-slate-700 px-3 py-1.5 text-[11px] text-slate-500">
          ⌘K Command Palette
        </button>
      </aside>

      <div className="flex-1 flex flex-col">
        <header className="flex items-center justify-between border-b border-cyan-500/15 px-6 py-3 text-xs">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-2">
              <span className={`status-dot ${wsConnected ? 'bg-emerald-400' : 'bg-red-500'}`} />
              {wsConnected ? 'LIVE' : 'DISCONNECTED'}
            </span>
            <span className={mode === 'ONLINE' ? 'text-emerald-400' : 'text-amber-400'}>{mode}</span>
            <span className="text-slate-500">
              Gateway: {gateway?.status ?? '…'}{gateway?.model ? ` (${gateway.model})` : ''}
            </span>
            {unread > 0 && (
              <button onClick={() => navigate('/')} className="text-amber-300">
                {unread} notification{unread > 1 ? 's' : ''}
              </button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={meeting} disabled={meetingBusy}
              className="rounded-lg border border-cyan-500/40 px-4 py-1.5 text-cyan-200 hover:bg-cyan-500/10 disabled:opacity-40">
              {meetingBusy ? 'MEETING…' : 'MEETING'}
            </button>
            <button
              onClick={() => (stopAll ? releaseStopAll() : stopAllApi())}
              className={`rounded-lg px-4 py-1.5 font-bold tracking-wider ${
                stopAll ? 'bg-red-700 text-white animate-pulse' : 'bg-red-600/80 text-white hover:bg-red-500'}`}>
              {stopAll ? 'STOP ALL ENGAGED — RELEASE' : 'STOP ALL'}
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
      {paletteOpen && <CommandPalette onClose={() => setPaletteOpen(false)} />}
    </div>
  )
}
