import React, { useState } from 'react'
import { useAuth } from './context/AuthContext.jsx'
import Layout from './components/Layout.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Vendors from './pages/Vendors.jsx'
import Assessments from './pages/Assessments.jsx'
import Documents from './pages/Documents.jsx'
import Risks from './pages/Risks.jsx'
import Policies from './pages/Policies.jsx'
import Frameworks from './pages/Frameworks.jsx'
import Continuity from './pages/Continuity.jsx'
import ITGC from './pages/ITGC.jsx'
import SOC from './pages/SOC.jsx'
import Incidents from './pages/Incidents.jsx'
import Users from './pages/Users.jsx'
import Audit from './pages/Audit.jsx'

// WHY: state-based nav (no router lib) keeps bundle small + readable for interview.
const PAGES = {
  dashboard: <Dashboard />, vendors: <Vendors />, assess: <Assessments />,
  docs: <Documents />, risks: <Risks />, policies: <Policies />,
  frameworks: <Frameworks />, continuity: <Continuity />, itgc: <ITGC />,
  soc: <SOC />, incidents: <Incidents />, users: <Users />, audit: <Audit />,
}

export default function App() {
  const { access } = useAuth()
  const [page, setPage] = useState('dashboard')
  if (!access) return <Login />
  return <Layout page={page} setPage={setPage}>{PAGES[page]}</Layout>
}
