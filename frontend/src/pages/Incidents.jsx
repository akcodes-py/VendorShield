import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'

// WHY: stepwise lifecycle stops skipping containment; timeline notes = evidence.
export default function Incidents() {
  const { can } = useAuth()
  const [rows, setRows] = useState([])
  const load = () => api('/api/v1/incidents').then(setRows).catch(() => {})
  useEffect(load, [])
  const NEXT = { Detected: 'Triaged', Triaged: 'Contained', Contained: 'Eradicated', Eradicated: 'Recovered', Recovered: 'LessonsLearned' }
  async function step(i) {
    const to = NEXT[i.status]
    if (to) { await api(`/api/v1/incidents/${i.id}/transition`, { method: 'POST', body: JSON.stringify({ to }) }); load() }
  }
  return (
    <div>
      <h2 className="font-bold">Incidents</h2>
      <table><thead><tr><th>Title</th><th>Sev</th><th>Status</th><th>Act</th></tr></thead>
        <tbody>{rows.map(i => (
          <tr key={i.id}><td>{i.title}</td><td>{i.severity}</td><td>{i.status}</td>
            <td>{can('Admin', 'Reviewer') && NEXT[i.status] && <button onClick={() => step(i)}>→ {NEXT[i.status]}</button>}</td></tr>
        ))}</tbody></table>
    </div>
  )
}
