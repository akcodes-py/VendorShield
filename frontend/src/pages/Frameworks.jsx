import React, { useEffect, useState } from 'react'
import { api } from '../services/api.js'

// WHY: coverage % = mapped controls / total; unmapped = gap to fix.
export default function Frameworks() {
  const [cov, setCov] = useState(null)
  useEffect(() => {
    api('/api/v1/frameworks/coverage?framework=ISO27001').then(setCov).catch(() => setCov({ error: 'no controls yet' }))
  }, [])
  return (
    <div>
      <h2 className="font-bold">Framework coverage</h2>
      <pre className="bg-white p-2 text-xs">{JSON.stringify(cov, null, 1)}</pre>
    </div>
  )
}
