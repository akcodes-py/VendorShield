import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'

// WHY: gaps report = critical vendors with missing/untested/exit-less plans.
export default function Continuity() {
  const [gaps, setGaps] = useState([])
  const [all, setAll] = useState([])
  useEffect(() => {
    api('/api/v1/continuity/report/gaps').then(setGaps).catch(() => {})
    api('/api/v1/continuity').then(setAll).catch(() => {})
  }, [])
  return (
    <div>
      <h2 className="font-bold">Continuity gaps (critical vendors)</h2>
      <ul>{gaps.map(g => <li key={g.vendor_id}>{g.name}: {g.reasons.join(', ')}</li>)}</ul>
      <h3 className="font-bold mt-2">All</h3>
      <table><thead><tr><th>Vendor</th><th>RTO/RPO</th><th>Plan</th><th>Test</th><th>Exit</th></tr></thead>
        <tbody>{all.map(c => (
          <tr key={c.vendor_id}><td>{c.name}</td><td>{c.rto_hours}/{c.rpo_hours}</td>
            <td>{c.plan_available ? 'Y' : 'N'}</td><td>{c.last_test_date}</td><td>{c.exit_plan ? 'Y' : 'N'}</td></tr>
        ))}</tbody></table>
    </div>
  )
}
