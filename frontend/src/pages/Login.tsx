import { useState } from 'react'
import { login } from '../services/api'
import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '../components/ui'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      const ok = await login(email.trim(), password)
      if (!ok) setError('Invalid email or password.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#050b12] p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>FROGÉ HQ — Sign in</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Input
              type="email"
              placeholder="Owner email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submit()}
            />
            {error && <p className="text-xs text-red-400">{error}</p>}
            <Button className="w-full" disabled={busy || !email || !password} onClick={submit}>
              {busy ? 'SIGNING IN…' : 'SIGN IN'}
            </Button>
            <p className="text-center text-[10px] text-slate-500">
              Owner credentials are set by the deployment environment — never stored in the repo.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
