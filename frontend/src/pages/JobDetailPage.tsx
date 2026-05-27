import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '../AuthContext'
import type { IngestionJob, NormalizedRecord, RawErrorRow } from '../api'
import {
  approveRecord,
  getJob,
  listErrors,
  listRecords,
  lockJob,
  updateRecord,
} from '../api'

type Tab = 'pending' | 'suspicious' | 'errors' | 'approved'

export function JobDetailPage() {
  const { jobId } = useParams()
  const id = Number(jobId)

  const { orgSlug } = useAuth()
  const [job, setJob] = useState<IngestionJob | null>(null)
  const [tab, setTab] = useState<Tab>('pending')
  const [records, setRecords] = useState<NormalizedRecord[]>([])
  const [errors, setErrors] = useState<RawErrorRow[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canLock = useMemo(() => {
    if (!job) return false
    return job.status !== 'LOCKED'
  }, [job])

  async function reload() {
    if (!orgSlug) return
    setError(null)
    setJob(await getJob(orgSlug, id))
    if (tab === 'errors') {
      setErrors(await listErrors(orgSlug, id))
      setRecords([])
      return
    }

    if (tab === 'pending') {
      setRecords(await listRecords(orgSlug, id, { reviewStatus: 'PENDING' }))
    } else if (tab === 'approved') {
      setRecords(await listRecords(orgSlug, id, { reviewStatus: 'APPROVED' }))
    } else if (tab === 'suspicious') {
      setRecords(await listRecords(orgSlug, id, { suspicious: true }))
    }
    setErrors([])
  }

  useEffect(() => {
    if (!orgSlug || !id) return
    ;(async () => {
      try {
        await reload()
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load')
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgSlug, id, tab])

  async function doApprove(r: NormalizedRecord) {
    if (!orgSlug) return
    setBusy(true)
    try {
      await approveRecord(orgSlug, r.id)
      await reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Approve failed')
    } finally {
      setBusy(false)
    }
  }

  async function doQuickEdit(r: NormalizedRecord) {
    if (!orgSlug) return
    const newDesc = window.prompt('Edit description', r.description)
    if (newDesc === null) return
    setBusy(true)
    try {
      await updateRecord(orgSlug, r.id, { description: newDesc, reason: 'analyst_edit' })
      await reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Update failed')
    } finally {
      setBusy(false)
    }
  }

  async function doLock() {
    if (!orgSlug) return
    setBusy(true)
    try {
      await lockJob(orgSlug, id)
      await reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Lock failed')
    } finally {
      setBusy(false)
    }
  }

  if (!orgSlug) return <div className="card">No org selected</div>

  const statusVariant = job?.status === 'LOCKED' ? 'success' : undefined

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <Link className="btn ghost small" to="/jobs">
            ← Jobs
          </Link>
          <h2>Job #{id}</h2>
          {job && (
            <p className="muted page-subtitle">
              {job.source.source_type} — {job.source.name}{' '}
              <span className="badge" data-variant={statusVariant}>
                {job.status}
              </span>
            </p>
          )}
        </div>
        <button className="btn primary" disabled={busy || !canLock} onClick={doLock}>
          Lock for audit
        </button>
      </div>

      {job && (
        <div className="card pad-lg">
          <div className="grid4">
            <div>
              <div className="k">Received</div>
              <div className="v">{job.received_rows}</div>
            </div>
            <div>
              <div className="k">Failed</div>
              <div className="v">{job.failed_rows}</div>
            </div>
            <div>
              <div className="k">Suspicious</div>
              <div className="v">{job.suspicious_rows}</div>
            </div>
            <div>
              <div className="k">Approved</div>
              <div className="v">{job.approved_rows}</div>
            </div>
          </div>
        </div>
      )}

      <div className="tabs">
        <button className={tab === 'pending' ? 'active' : ''} onClick={() => setTab('pending')}>
          Pending
        </button>
        <button className={tab === 'suspicious' ? 'active' : ''} onClick={() => setTab('suspicious')}>
          Suspicious
        </button>
        <button className={tab === 'approved' ? 'active' : ''} onClick={() => setTab('approved')}>
          Approved
        </button>
        <button className={tab === 'errors' ? 'active' : ''} onClick={() => setTab('errors')}>
          Failed rows
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {tab === 'errors' ? (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Row</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {errors.map((e) => (
                <tr key={e.id}>
                  <td className="num">{e.row_number}</td>
                  <td className="warn">{e.error}</td>
                </tr>
              ))}
              {errors.length === 0 && (
                <tr>
                  <td colSpan={2} className="muted">
                    No errors.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Category</th>
                <th>Date/Period</th>
                <th>Description</th>
                <th>Normalized</th>
                <th className="num">Spend</th>
                <th>Flags</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id} className={r.suspicious ? 'row-warn' : ''}>
                  <td className="num">{r.id}</td>
                  <td>{r.category}</td>
                  <td>
                    {r.activity_date || ''}
                    {r.period_start && r.period_end
                      ? `${r.period_start} → ${r.period_end}`
                      : ''}
                  </td>
                  <td>{r.description}</td>
                  <td>
                    {r.normalized_quantity || ''} {r.normalized_unit}
                  </td>
                  <td className="num">
                    {r.spend_amount ? `${r.spend_amount} ${r.spend_currency}` : ''}
                  </td>
                  <td className="muted">
                    {r.suspicious_reasons?.length ? r.suspicious_reasons.join(', ') : ''}
                  </td>
                  <td className="right">
                    <button className="btn small" disabled={busy || r.is_locked} onClick={() => doQuickEdit(r)}>
                      Edit
                    </button>
                    {' '}
                    <button
                      className="btn small"
                      disabled={busy || r.is_locked || r.review_status === 'APPROVED'}
                      onClick={() => doApprove(r)}
                    >
                      Approve
                    </button>
                  </td>
                </tr>
              ))}
              {records.length === 0 && (
                <tr>
                  <td colSpan={8} className="muted">
                    No rows in this view.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
