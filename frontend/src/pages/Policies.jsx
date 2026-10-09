import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'

// WHY: version history proves what was approved when (governance).
export default function Policies() {
  const [rows, setRows] = useState([])
  const load = () => api('/api/v1/policies').then(setRows).catch(() => {})
  useEffect(load, [])
  return (
    <div>
      <h2 className="font-bold">Policies (SAMPLE templates marked)</h2>
      <table><thead><tr><th>Title</th><th>Ver</th><th>Status</th><th>Sample</th></tr></thead>
        <tbody>{rows.map(p => (
          <tr key={p.id}><td>{p.title}</td><td>{p.version}</td><td>{p.approval_status}</td><td>{p.is_sample ? 'YES' : ''}</td></tr>
        ))}</tbody></table>
    </div>
  )
}
