import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'

// WHY: triage is Reviewer/Admin; Auditor read-only; Vendor blocked server-side.
export default function SOC() {
  const { can } = useAuth()
  const [alerts, setAlerts] = useState([])
  const load = () => api('/api/v1/alerts').then(setAlerts).catch(() => {})
  useEffect(load, [])
  async function run() { await api('/api/v1/detection/run', { method: 'POST' }); load() }
  async function triage(id, status) {
    await api(`/api/v1/alerts/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }); load()
  }
  return (
    <div>
      <h2 className="font-bold">SOC alerts (SAMPLE events labelled)</h2>
      {can('Admin', 'Reviewer') && <button onClick={run}>Run detection rules</button>}
      <table><thead><tr><th>Rule</th><th>Sev</th><th>Status</th><th>Detail</th><th>Act</th></tr></thead>
        <tbody>{alerts.map(a => (
          <tr key={a.id}><td>{a.rule}</td><td>{a.severity}</td><td>{a.status}</td><td>{a.detail.slice(0, 60)}</td>
            <td>{can('Admin', 'Reviewer') && (
              <select defaultValue="" onChange={e => e.target.value && triage(a.id, e.target.value)}>
                <option value="">…</option><option>Investigating</option><option>Resolved</option><option>FalsePositive</option>
              </select>)}</td></tr>
        ))}</tbody></table>
    </div>
  )
}
