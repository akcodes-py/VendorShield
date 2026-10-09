import React from 'react'
import { useAuth } from '../context/AuthContext.jsx'

// WHY: nav hides what role cannot use; backend still enforces (defence in depth).
const ITEMS = [
  ['dashboard', 'Dashboard', ['Admin', 'Reviewer', 'Auditor', 'Vendor']],
  ['vendors', 'Vendors', ['Admin', 'Reviewer', 'Auditor', 'Vendor']],
  ['assess', 'Assessments', ['Admin', 'Reviewer', 'Auditor', 'Vendor']],
  ['docs', 'Documents', ['Admin', 'Reviewer', 'Auditor', 'Vendor']],
  ['risks', 'Risks', ['Admin', 'Reviewer', 'Auditor', 'Vendor']],
  ['policies', 'Policies', ['Admin', 'Reviewer', 'Auditor']],
  ['frameworks', 'Frameworks', ['Admin', 'Reviewer', 'Auditor']],
  ['continuity', 'Continuity', ['Admin', 'Reviewer', 'Auditor', 'Vendor']],
  ['itgc', 'ITGC', ['Admin', 'Reviewer', 'Auditor']],
  ['soc', 'SOC Alerts', ['Admin', 'Reviewer', 'Auditor']],
  ['incidents', 'Incidents', ['Admin', 'Reviewer', 'Auditor']],
  ['users', 'Users/Approvals', ['Admin', 'Auditor']],
  ['audit', 'Audit Log', ['Admin', 'Auditor']],
]

export default function Layout({ page, setPage, children }) {
  const { role, logout, mfaNeeded } = useAuth()
  return (
    <div className="p-4 max-w-6xl mx-auto">
      <header className="flex justify-between items-center mb-3">
        <h1 className="text-xl font-bold">VendorShield <span className="text-xs font-normal">(SAMPLE demo)</span></h1>
        <div className="text-sm">{role} <button onClick={logout} className="ml-2">Logout</button></div>
      </header>
      {mfaNeeded && <p className="bg-yellow-200 p-2 mb-2 text-sm">Admin: enable MFA via Users page or POST /mfa/setup (TOTP required).</p>}
      <nav className="flex flex-wrap gap-1 mb-4">
        {ITEMS.filter(([, , r]) => r.includes(role)).map(([k, label]) => (
          <button key={k} onClick={() => setPage(k)}
            className={page === k ? 'bg-blue-700' : ''}>{label}</button>
        ))}
      </nav>
      <main>{children}</main>
    </div>
  )
}
