import { useState } from 'react'
import { login, signup } from '../services/api'
import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '../components/ui'

export default function Login() {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      if (mode === 'signin') {
        const ok = await login(email.trim(), password)
        if (!ok) setError('Invalid email or password.')
      } else {
        const r = await signup(email.trim(), password, name.trim())
        if (!r.ok) setError(r.error || 'Signup failed.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#050b12] p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>FROGÉ HQ</CardTitle>
          <div className="mt-2 flex gap-2">
            <button
              className={`flex-1 rounded px-2 py-1 text-xs ${
                mode === 'signin'
                  ? 'bg-cyan-500/20 text-cyan-300'
                  : 'bg-white/5 text-slate-400 hover:text-slate-200'
              }`}
              onClick={() => { setMode('signin'); setError('') }}
            >
              SIGN IN
            </button>
            <button
              className={`flex-1 rounded px-2 py-1 text-xs ${
                mode === 'signup'
                  ? 'bg-cyan-500/20 text-cyan-300'
                  : 'bg-white/5 text-slate-400 hover:text-slate-200'
              }`}
              onClick={() => { setMode('signup'); setError('') }}
            >
              CREATE ACCOUNT
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {mode === 'signup' && (
              <Input
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            )}
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus={mode === 'signin'}
            />
            <Input
              type="password"
              placeholder={mode === 'signup' ? 'Password (min 8 characters)' : 'Password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submit()}
            />
            {error && <p className="text-xs text-red-400">{error}</p>}
            <Button className="w-full" disabled={busy || !email || !password} onClick={submit}>
              {busy ? 'PLEASE WAIT…' : mode === 'signin' ? 'SIGN IN' : 'CREATE ACCOUNT'}
            </Button>
            <p className="text-center text-[10px] text-slate-500">
              Passwords are stored salted and hashed — never in plaintext.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
