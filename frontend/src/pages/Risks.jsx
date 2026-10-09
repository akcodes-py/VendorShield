import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'

// WHY: residual<=inherent enforced server-side; UI shows overdue flags.
export default function Risks() {
  const { can } = useAuth()
  const [rows, setRows] = useState([])
  const [vendors, setVendors] = useState([])
  const load = () => api('/api/v1/risks').then(setRows).catch(() => {})
  useEffect(() => { load(); api('/api/v1/vendors').then(setVendors).catch(() => {}) }, [])
  async function create(e) {
    e.preventDefault()
    const f = new FormData(e.target)
    await api('/api/v1/risks', {
      method: 'POST', body: JSON.stringify({
        vendor_id: +f.get('vendor_id'), description: f.get('description'),
        likelihood: +f.get('likelihood'), impact: +f.get('impact'),
      }),
    })
    e.target.reset(); load()
  }
  return (
    <div>
      <h2 className="font-bold">Risks (LxI, overdue flags, exceptions via API)</h2>
      {can('Admin', 'Reviewer') && (
        <form onSubmit={create} className="flex gap-2 my-2">
          <select name="vendor_id">{vendors.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}</select>
          <input name="description" placeholder="description" required />
          <select name="likelihood"><option value={3}>L3</option><option value={4}>L4</option><option value={5}>L5</option></select>
          <select name="impact"><option value={3}>I3</option><option value={4}>I4</option><option value={5}>I5</option></select>
          <button>Add</button>
        </form>
      )}
      <table><thead><tr><th>ID</th><th>Desc</th><th>LxI</th><th>Sev</th><th>Status</th><th>Overdue</th></tr></thead>
        <tbody>{rows.map(r => (
          <tr key={r.id}><td>{r.id}</td><td>{r.description.slice(0, 40)}</td>
            <td>{r.likelihood}x{r.impact}={r.inherent_score}</td><td>{r.severity}</td>
            <td>{r.status}</td><td>{r.overdue ? 'YES' : ''}</td></tr>
        ))}</tbody></table>
    </div>
  )
}
