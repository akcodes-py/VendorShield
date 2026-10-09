import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'

// WHY: tiny login form - shows MFA code box when Admin needs TOTP.
export default function Login() {
  const { login } = useAuth()
  const [email, setEmail] = useState('reviewer@example.com')
  const [password, setPassword] = useState('Password123!')
  const [code, setCode] = useState('')
  const [err, setErr] = useState('')
  async function go(e) {
    e.preventDefault(); setErr('')
    try { await login(email, password, code || undefined) }
    catch (ex) { setErr(String(ex.message)) }
  }
  return (
    <form onSubmit={go} className="max-w-sm mx-auto mt-20 p-4 bg-white rounded shadow">
      <h2 className="font-bold mb-2">VendorShield login (local demo)</h2>
      <input value={email} onChange={e => setEmail(e.target.value)} placeholder="email" />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="password" className="mt-2" />
      <input value={code} onChange={e => setCode(e.target.value)} placeholder="TOTP (Admin only)" className="mt-2" />
      {err && <p className="text-red-700 text-sm mt-2">{err}</p>}
      <button className="mt-3 w-full">Login</button>
      <p className="text-xs mt-2">SAMPLE users: admin / reviewer / auditor / vendor1 @example.com / Password123!</p>
    </form>
  )
}
