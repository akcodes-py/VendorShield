import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'

// WHY: access review = list + confirm/revoke; role/delete need 2nd Admin via approvals.
export default function Users() {
  const { can } = useAuth()
  const [users, setUsers] = useState([])
  const [approvals, setApprovals] = useState([])
  const load = () => {
    api('/api/v1/users').then(setUsers).catch(() => {})
    if (can('Admin')) api('/api/v1/approvals').then(setApprovals).catch(() => {})
  }
  useEffect(load, [])
  async function decide(id, approve) {
    await api(`/api/v1/approvals/${id}/decide`, { method: 'POST', body: JSON.stringify({ approve }) }); load()
  }
  return (
    <div>
      <h2 className="font-bold">Access review (quarterly)</h2>
      <table><thead><tr><th>Email</th><th>Role</th><th>Status</th></tr></thead>
        <tbody>{users.map(u => <tr key={u.id}><td>{u.email}</td><td>{u.role}</td><td>{u.status}</td></tr>)}</tbody></table>
      {can('Admin') && (<>
        <h3 className="font-bold mt-2">Pending approvals (2nd Admin decides)</h3>
        <ul>{approvals.filter(a => a.decision === 'Pending').map(a => (
          <li key={a.id}>{a.entity} by {a.requested_by}
            <button onClick={() => decide(a.id, true)} className="ml-2">Approve</button>
            <button onClick={() => decide(a.id, false)} className="ml-1 danger">Reject</button></li>
        ))}</ul>
      </>)}
    </div>
  )
}
