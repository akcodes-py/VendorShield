// WHY: single API helper - injects JWT, handles 401/403/429 uniformly.
const BASE = 'http://localhost:8000'

export function authHeaders() {
  const t = localStorage.getItem('access')
  return { 'Content-Type': 'application/json', ...(t ? { Authorization: `Bearer ${t}` } : {}) }
}

export async function api(path, opts = {}) {
  const r = await fetch(BASE + path, { ...opts, headers: { ...authHeaders(), ...(opts.headers || {}) } })
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    throw new Error(`${r.status} ${body.detail || r.statusText}`)
  }
  return r.json().catch(() => ({}))
}

export async function loginApi(email, password, totp_code) {
  const r = await fetch(BASE + '/api/v1/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, ...(totp_code ? { totp_code } : {}) }),
  })
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || 'Login failed')
  return r.json()
}

export async function uploadDoc(formData) {
  // WHY: no Content-Type header - browser sets multipart boundary.
  const t = localStorage.getItem('access')
  const r = await fetch(BASE + '/api/v1/documents/upload', {
    method: 'POST', headers: { Authorization: `Bearer ${t}` }, body: formData,
  })
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || 'Upload failed')
  return r.json()
}
