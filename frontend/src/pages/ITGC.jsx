import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'

// WHY: Pass needs evidence (server 422 otherwise); change log is Admin-only.
export default function ITGC() {
  const [rows, setRows] = useState([])
  const [changes, setChanges] = useState([])
  useEffect(() => {
    api('/api/v1/itgc').then(setRows).catch(() => {})
    api('/api/v1/config-changes').then(setChanges).catch(() => {})
  }, [])
  return (
    <div>
      <h2 className="font-bold">ITGC checklist</h2>
      <table><thead><tr><th>Domain</th><th>Control</th><th>Status</th></tr></thead>
        <tbody>{rows.map(r => <tr key={r.id}><td>{r.domain}</td><td>{r.control.slice(0, 60)}</td><td>{r.status}</td></tr>)}</tbody></table>
      <h3 className="font-bold mt-2">Config changes</h3>
      <ul className="text-xs">{changes.map(c => <li key={c.id}>{c.change}</li>)}</ul>
    </div>
  )
}
