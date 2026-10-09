import React, { useEffect, useState } from 'react'
import { api, uploadDoc } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'

// WHY: upload uses FormData; expiry_flag shown from API (Valid/Expiring/Expired).
export default function Documents() {
  const { can } = useAuth()
  const [rows, setRows] = useState([])
  const [vendors, setVendors] = useState([])
  const load = () => api('/api/v1/documents').then(setRows).catch(() => {})
  useEffect(() => { load(); api('/api/v1/vendors').then(setVendors).catch(() => {}) }, [])
  async function go(e) {
    e.preventDefault()
    const fd = new FormData(e.target)
    await uploadDoc(fd); e.target.reset(); load()
  }
  return (
    <div>
      <h2 className="font-bold">Documents</h2>
      {can('Admin', 'Reviewer', 'Vendor') && (
        <form onSubmit={go} className="flex gap-2 my-2">
          <select name="vendor_id">{vendors.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}</select>
          <select name="doc_type"><option>ISO27001</option><option>SOC2</option><option>Policy</option><option>Pentest</option></select>
          <input type="file" name="file" required />
          <button>Upload</button>
        </form>
      )}
      <p className="text-xs">AI summaries are drafts - reviewer must confirm. Risks: hallucination + data privacy.</p>
      <table><thead><tr><th>ID</th><th>Type</th><th>Expiry</th><th>Flag</th><th>Review</th></tr></thead>
        <tbody>{rows.map(d => (
          <tr key={d.id}><td>{d.id}</td><td>{d.doc_type}</td><td>{d.expiry_date}</td>
            <td><span className="badge" style={{ background: d.expiry_flag === 'Expired' ? 'red' : d.expiry_flag === 'Expiring' ? 'orange' : 'green' }}>{d.expiry_flag}</span></td>
            <td>{d.review_status}</td></tr>
        ))}</tbody></table>
    </div>
  )
}
