import React, { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts'
import { api } from '../services/api.js'

// WHY: single /reports/dashboard call (Phase 9) + PDF exports for exec pack.
export default function Dashboard() {
  const [d, setD] = useState(null)
  useEffect(() => { api('/api/v1/reports/dashboard').then(setD).catch(() => {}) }, [])
  const bars = d ? Object.entries(d.open_risks_by_severity).map(([k, v]) => ({ sev: k, n: v })) : []
  function pdf(url, name) {
    // WHY: fetch with JWT then blob - plain <a> would miss Authorization.
    fetch(url, { headers: { Authorization: `Bearer ${localStorage.getItem('access')}` } })
      .then(r => r.blob()).then(b => {
        const a = document.createElement('a')
        a.href = URL.createObjectURL(b); a.download = name; a.click()
      })
  }
  if (!d) return <p>Loading dashboard…</p>
  return (
    <div>
      <h2 className="font-bold">Dashboard (live API, SAMPLE data)</h2>
      <div className="grid grid-cols-4 gap-2 my-2">
        <div className="bg-white p-2">Completion: <b>{d.assessment_completion_rate}%</b></div>
        <div className="bg-white p-2">Expiring docs: <b>{d.expiring_documents.length}</b></div>
        <div className="bg-white p-2">Overdue fixes: <b>{d.overdue_remediations.length}</b></div>
        <div className="bg-white p-2">Top risky: <b>{d.top_5_riskiest[0]?.name || '—'}</b></div>
      </div>
      <BarChart width={400} height={200} data={bars}>
        <XAxis dataKey="sev" /><YAxis /><Tooltip /><Bar dataKey="n" />
      </BarChart>
      <div className="mt-2 flex gap-2">
        <button onClick={() => pdf('http://localhost:8000/api/v1/reports/executive.pdf', 'executive.pdf')}>
          Download executive PDF</button>
      </div>
      <pre className="text-xs bg-white p-2 mt-2">{JSON.stringify({ by_level: d.vendors_by_risk_level, top5: d.top_5_riskiest }, null, 1)}</pre>
    </div>
  )
}
