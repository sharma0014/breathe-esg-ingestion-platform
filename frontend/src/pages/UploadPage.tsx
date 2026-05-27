import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../AuthContext'
import { uploadIngest } from '../api'

export function UploadPage() {
  const { orgSlug } = useAuth()
  const nav = useNavigate()

  const [sourceType, setSourceType] = useState<'SAP' | 'UTILITY' | 'TRAVEL'>('SAP')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function onFile(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] || null
    setFile(f)
  }

  async function submit() {
    if (!orgSlug) return
    if (!file) {
      setError('Pick a file')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const job = await uploadIngest(orgSlug, sourceType, file)
      nav(`/jobs/${job.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h2>Upload + ingest</h2>
          <p className="muted page-subtitle">Create a job and generate review rows.</p>
        </div>
      </div>

      <div className="card pad-lg">
        <div className="field">
          <label>Source type</label>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value as any)}
          >
            <option value="SAP">SAP (fuel + procurement)</option>
            <option value="UTILITY">Utility electricity export</option>
            <option value="TRAVEL">Corporate travel export</option>
          </select>
        </div>
        <div className="field">
          <label>File</label>
          <input type="file" onChange={onFile} />
          {file && (
            <div className="muted">
              Selected: <code>{file.name}</code>
            </div>
          )}
        </div>
        {error && <div className="error">{error}</div>}
        <button className="btn primary" disabled={busy || !orgSlug} onClick={submit}>
          {busy ? 'Ingesting…' : 'Upload'}
        </button>
      </div>

      <div className="card">
        <h3>Sample files</h3>
        <p className="muted">
          Use the CSVs in <code>sample_data/</code> at repo root.
        </p>
      </div>
    </div>
  )
}
