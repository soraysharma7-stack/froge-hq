import { useEffect, useState } from 'react'
import { api } from '../services/api'

interface Memory { id: string; content: string; category: string; source: string; confidence: number; created_at: number }

export default function MemoryVault() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [cat, setCat] = useState('')
  const [q, setQ] = useState('')
  const [content, setContent] = useState('')
  const [newCat, setNewCat] = useState('LESSONS')

  const load = () => api.get(`/memory?q=${encodeURIComponent(q)}${cat ? `&category=${cat}` : ''}`).then(setMemories)
  useEffect(() => { api.get('/memory/categories').then(setCategories) }, [])
  useEffect(() => { load() }, [cat, q])

  const store = async () => {
    if (!content.trim()) return
    await api.post('/memory', { content, category: newCat, source: 'user' })
    setContent(''); load()
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <button onClick={() => setCat('')} className={`rounded px-2 py-1 text-[11px] ${!cat ? 'bg-cyan-500/30 text-cyan-200' : 'text-slate-500'}`}>ALL</button>
        {categories.map((c) => (
          <button key={c} onClick={() => setCat(c)} className={`rounded px-2 py-1 text-[11px] ${cat === c ? 'bg-cyan-500/30 text-cyan-200' : 'text-slate-500'}`}>{c}</button>
        ))}
      </div>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search memories…"
        className="w-full rounded-lg border border-cyan-500/30 bg-black/40 px-3 py-2 text-sm outline-none" />
      <div className="holo-panel p-3 flex gap-2">
        <input value={content} onChange={(e) => setContent(e.target.value)} placeholder="Store a useful memory…"
          className="flex-1 rounded-lg border border-cyan-500/30 bg-black/40 px-3 py-2 text-xs outline-none" />
        <select value={newCat} onChange={(e) => setNewCat(e.target.value)} className="rounded-lg bg-black/40 border border-cyan-500/30 px-2 text-xs">
          {categories.map((c) => <option key={c}>{c}</option>)}
        </select>
        <button onClick={store} className="rounded-lg bg-cyan-500/80 px-3 py-1 text-xs font-semibold text-black">STORE</button>
      </div>
      <div className="space-y-2">
        {memories.map((m) => (
          <div key={m.id} className="holo-panel p-3 text-xs">
            <div className="flex justify-between">
              <span className="text-cyan-400">{m.category}</span>
              <span className="text-slate-600">conf {m.confidence} · {m.source} · {new Date(m.created_at * 1000).toLocaleString()}</span>
            </div>
            <p className="mt-1 text-slate-300">{m.content}</p>
          </div>
        ))}
        {memories.length === 0 && <p className="text-xs text-slate-600">No memories — only useful information is stored.</p>}
      </div>
    </div>
  )
}
