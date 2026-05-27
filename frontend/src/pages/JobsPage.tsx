import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../AuthContext'
import type { IngestionJob } from '../api'
import { listJobs } from '../api'

export function JobsPage() {
  const { orgSlug } = useAuth()
  const [jobs, setJobs] = useState<IngestionJob[]>([])
  const [error, setError] = useState<string | null>(null)

  function jobBadgeVariant(j: IngestionJob): 'success' | 'danger' | 'warn' | undefined {
    if (j.status === 'LOCKED') return 'success'
    if (j.failed_rows > 0) return 'danger'
    if (j.suspicious_rows > 0) return 'warn'
    return undefined
  }

  useEffect(() => {
    if (!orgSlug) return
    ;(async () => {
      try {
        setError(null)
        setJobs(await listJobs(orgSlug))
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load jobs')
      }
    })()
  }, [orgSlug])

  if (!orgSlug) {
    return (
      <div className="card">
        <h2>No organization selected</h2>
        <p className="muted">
          The backend seeds an org in dev. If you’re using your own user, create
          a membership in the Django admin.
        </p>
      </div>
    )
  }

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h2>Ingestion jobs</h2>
          <p className="muted page-subtitle">Review, approve, then lock for audit.</p>
        </div>
        <Link className="btn primary" to="/upload">
          Upload new
        </Link>
      </div>
      {error && <div className="error">{error}</div>}

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Source</th>
              <th>Status</th>
              <th className="num">Received</th>
              <th className="num">Failed</th>
              <th className="num">Suspicious</th>
              <th className="num">Approved</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td>
                  <Link to={`/jobs/${j.id}`}>#{j.id}</Link>
                </td>
                <td>
                  {j.source.source_type} — {j.source.name}
                </td>
                <td>
                  <span className="badge" data-variant={jobBadgeVariant(j)}>
                    {j.status}
                  </span>
                </td>
                <td className="num">{j.received_rows}</td>
                <td className={`num ${j.failed_rows ? 'warn' : ''}`}>{j.failed_rows}</td>
                <td className={`num ${j.suspicious_rows ? 'warn' : ''}`}>{j.suspicious_rows}</td>
                <td className="num">{j.approved_rows}</td>
                <td>{new Date(j.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {jobs.length === 0 && (
              <tr>
                <td colSpan={8} className="muted">
                  No jobs yet. Upload one.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
