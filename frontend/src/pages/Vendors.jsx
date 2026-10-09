import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'

// WHY: Vendor sees own only (server filters); Reviewer creates, Admin approves.
export default function Vendors() {
  const { can } = useAuth()
  const [rows, setRows] = useState([])
  const [form, setForm] = useState({ name: '', service_type: '', tier: 2 })
  const load = () => api('/api/v1/vendors').then(setRows).catch(() => {})
  useEffect(load, [])
  async function create(e) {
    e.preventDefault()
    await api('/api/v1/vendors', { method: 'POST', body: JSON.stringify({ ...form, tier: +form.tier, data_access: 'Low' }) })
    setForm({ name: '', service_type: '', tier: 2 }); load()
  }
  async function trans(id, to) {
    await api(`/api/v1/vendors/${id}/transition`, { method: 'POST', body: JSON.stringify({ to }) }); load()
  }
  return (
    <div>
      <h2 className="font-bold">Vendors</h2>
      {can('Admin', 'Reviewer') && (
        <form onSubmit={create} className="flex gap-2 my-2">
          <input placeholder="name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
          <input placeholder="service" value={form.service_type} onChange={e => setForm({ ...form, service_type: e.target.value })} />
          <select value={form.tier} onChange={e => setForm({ ...form, tier: e.target.value })}>
            <option value={1}>T1</option><option value={2}>T2</option><option value={3}>T3</option>
          </select>
          <button>Create</button>
        </form>
      )}
      <table><thead><tr><th>Name</th><th>Tier</th><th>Lifecycle</th><th>Next review</th><th>Action</th></tr></thead>
        <tbody>{rows.map(v => (
          <tr key={v.id}><td>{v.name}</td><td>{v.tier}</td><td>{v.lifecycle}</td><td>{v.next_review_date}</td>
            <td>{can('Admin', 'Reviewer') && (
              <select defaultValue="" onChange={e => e.target.value && trans(v.id, e.target.value)}>
                <option value="">move…</option>
                {['Assessment', 'Approved', 'Rejected', 'Review', 'Offboarded'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>)}</td></tr>
        ))}</tbody></table>
    </div>
  )
}
