import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, stopAll } from '../services/api'
import { useHQ } from '../store'

interface Cmd { label: string; run: () => void | Promise<void>; hint?: string }

export default function CommandPalette({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<{ kind: string; label: string }[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const { missions, employees } = useHQ()

  useEffect(() => inputRef.current?.focus(), [])

  const commands: Cmd[] = [
    { label: 'Start mission', run: () => { navigate('/'); onClose() }, hint: 'new' },
    { label: 'Open Maya', run: () => { navigate('/employee/maya'); onClose() } },
    { label: 'Open department', run: () => { navigate('/department/software_engineering'); onClose() } },
    { label: 'Call Boardroom', run: async () => { await api.post('/boardroom', { topic: 'Manual boardroom call' }); navigate('/boardroom'); onClose() } },
    { label: 'Show running tasks', run: () => { navigate('/'); onClose() } },
    { label: 'Show errors', run: () => { navigate('/monitoring'); onClose() } },
    { label: 'Show approvals', run: () => { navigate('/security'); onClose() } },
    { label: 'Stop all', run: async () => { await stopAll(); onClose() } },
    { label: 'Open monitoring', run: () => { navigate('/monitoring'); onClose() } },
    { label: 'Open security', run: () => { navigate('/security'); onClose() } },
    { label: 'Open memory', run: () => { navigate('/memory'); onClose() } },
    ...missions.slice(0, 5).map((m) => ({ label: `Mission: ${m.title}`, run: () => { navigate(`/mission/${m.id}`); onClose() } })),
    ...employees.map((e) => ({ label: `Employee: ${e.name}`, run: () => { navigate(`/employee/${e.id}`); onClose() } })),
  ]

  useEffect(() => {
    if (query.length > 2) {
      api.get(`/search?q=${encodeURIComponent(query)}`).then((r) => setResults(r.slice(0, 6)))
    } else setResults([])
  }, [query])

  const filtered = commands.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()))

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-32" onClick={onClose}>
      <div className="holo-panel w-[520px] p-3" onClick={(e) => e.stopPropagation()}>
        <input ref={inputRef} value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a command or search… (e.g. website bana do)"
          className="w-full rounded-lg border border-cyan-500/30 bg-black/50 px-3 py-2 text-sm outline-none focus:border-cyan-400" />
        <div className="mt-2 max-h-72 overflow-y-auto">
          {filtered.map((c) => (
            <button key={c.label} onClick={() => void c.run()}
              className="block w-full rounded-md px-3 py-2 text-left text-xs text-slate-300 hover:bg-cyan-500/15">
              {c.label} {c.hint && <span className="text-slate-600">· {c.hint}</span>}
            </button>
          ))}
          {results.map((r, i) => (
            <div key={i} className="px-3 py-2 text-xs text-slate-500">[{r.kind}] {r.label}</div>
          ))}
        </div>
      </div>
    </div>
  )
}
