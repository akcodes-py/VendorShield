import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'

// WHY: audit is append-only - UI has no edit/delete buttons by design.
export default function Audit() {
  const [rows, setRows] = useState([])
  useEffect(() => { api('/api/v1/audit-logs').then(setRows).catch(() => {}) }, [])
  return (
    <div>
      <h2 className="font-bold">Audit log (immutable, latest 200)</h2>
      <table><thead><tr><th>Actor</th><th>Action</th><th>Entity</th><th>IP</th></tr></thead>
        <tbody>{rows.map(r => <tr key={r.id}><td>{r.actor}</td><td>{r.action}</td><td>{r.entity}</td><td>{r.ip}</td></tr>)}</tbody></table>
    </div>
  )
}
