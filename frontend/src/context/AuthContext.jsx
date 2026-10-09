import React, { createContext, useContext, useState } from 'react'
import { loginApi } from '../services/api.js'

const Ctx = createContext(null)
export const useAuth = () => useContext(Ctx)

// WHY: role stored from JWT payload client-side for UI hiding;
// backend re-checks every endpoint (never trust UI alone).
function roleFromToken(tok) {
  try { return JSON.parse(atob(tok.split('.')[1])).role || '' } catch { return '' }
}

export function AuthProvider({ children }) {
  const [access, setAccess] = useState(localStorage.getItem('access') || '')
  const [role, setRole] = useState(access ? roleFromToken(access) : '')
  const [mfaNeeded, setMfaNeeded] = useState(false)

  async function login(email, password, code) {
    const data = await loginApi(email, password, code)
    localStorage.setItem('access', data.access_token)
    localStorage.setItem('refresh', data.refresh_token)
    setAccess(data.access_token)
    setRole(roleFromToken(data.access_token))
    setMfaNeeded(!!data.mfa_required)
  }
  function logout() {
    localStorage.clear(); setAccess(''); setRole('')
  }
  // WHY: can() centralises UI hiding: Admin>Reviewer>Auditor(read)>Vendor(scoped).
  function can(...allowed) { return allowed.includes(role) }
  return <Ctx.Provider value={{ access, role, mfaNeeded, login, logout, can }}>{children}</Ctx.Provider>
}
