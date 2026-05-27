import { Link, useLocation } from 'react-router-dom'

import { useAuth } from '../AuthContext'

export function Layout({ children }: { children: React.ReactNode }) {
  const { logout, orgSlug } = useAuth()
  const loc = useLocation()

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-left">
          <div className="brand">Breathe ESG — Ingestion Prototype</div>
          <div className="org">Org: {orgSlug || '—'}</div>
        </div>
        <nav className="nav">
          <Link className={loc.pathname.startsWith('/jobs') ? 'active' : ''} to="/jobs">
            Jobs
          </Link>
          <Link className={loc.pathname === '/upload' ? 'active' : ''} to="/upload">
            Upload
          </Link>
          <button className="btn ghost small" onClick={logout}>
            Logout
          </button>
        </nav>
      </header>
      <main className="main">{children}</main>
    </div>
  )
}
