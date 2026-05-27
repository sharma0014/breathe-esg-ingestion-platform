import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../AuthContext'
import hero from '../assets/hero.png'

export function LoginPage() {
  const nav = useNavigate()
  const { login } = useAuth()

  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('demo1234')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await login(username, password)
      nav('/jobs')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="center">
      <div className="auth-shell">
        <section className="auth-hero">
          <h1>Breathe ESG</h1>
          <p className="muted">
            Ingest → normalize → review → approve → lock for audit.
          </p>
          <img src={hero} alt="Ingestion dashboard preview" />
        </section>

        <form className="card pad-lg" onSubmit={onSubmit}>
          <h2>Sign in</h2>
          <p className="muted">
            Demo users (created via backend seed): <code>admin</code> /{' '}
            <code>demo1234</code>
          </p>

          <div className="field">
            <label>Username</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div className="field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && <div className="error">{error}</div>}
          <button className="btn primary" disabled={busy} type="submit">
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
