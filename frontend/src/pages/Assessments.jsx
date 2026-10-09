import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'

// WHY: Vendor answers own, Reviewer submits (SoD visible in UI).
export default function Assessments() {
  const { can } = useAuth()
  const [qs, setQs] = useState([])
  const [vendors, setVendors] = useState([])
  const [result, setResult] = useState(null)
  useEffect(() => {
    api('/api/v1/questions').then(setQs).catch(() => {})
    api('/api/v1/vendors').then(setVendors).catch(() => {})
  }, [])
  async function mk(vid) {
    const a = await api(`/api/v1/vendors/${vid}/assessments`, { method: 'POST' })
    // answer all Yes as SAMPLE demo, then submit
    await api(`/api/v1/assessments/${a.id}/answers`, {
      method: 'PUT', body: JSON.stringify({
        answers: qs.map(q => ({ question_id: q.id, value: 'Yes', evidence: '' })),
      }),
    })
    const s = await api(`/api/v1/assessments/${a.id}/submit`, { method: 'POST' })
    setResult(s)
  }
  return (
    <div>
      <h2 className="font-bold">Assessments ({qs.length} questions SAMPLE)</h2>
      {can('Admin', 'Reviewer') && vendors.map(v => (
        <button key={v.id} onClick={() => mk(v.id)} className="mr-2 mb-2">Assess {v.name}</button>
      ))}
      {result && <pre className="bg-white p-2 text-xs">{JSON.stringify(result, null, 1)}</pre>}
      <ul className="text-xs">{qs.slice(0, 5).map(q => <li key={q.id}>[{q.domain}] {q.text}</li>)}</ul>
    </div>
  )
}
