import { useEffect, useState } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { useHQ } from './store'
import { checkAuthConfig, getToken } from './services/api'
import Login from './pages/Login'
import Layout from './components/Layout'
import CommandCenter from './pages/CommandCenter'
import Office from './pages/Office'
import MissionDetail from './pages/MissionDetail'
import { DepartmentPage, EmployeePage } from './pages/Generic'
import Boardroom from './pages/Boardroom'
import Security from './pages/Security'
import Monitoring from './pages/Monitoring'
import MemoryVault from './pages/Memory'
import { SkillsPage, QAPage, ModelGatewayPage, ArtifactsPage, DecisionsPage, SettingsPage } from './pages/Misc'

export default function App() {
  const authed = useHQ((s) => s.authed)
  const setAuthed = useHQ((s) => s.setAuthed)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    checkAuthConfig()
      .then((required) => {
        // If the deployment requires auth, a stored token must exist; otherwise show Login.
        setAuthed(!required || !!getToken())
      })
      .catch(() => setAuthed(true)) // backend unreachable → dev mode passthrough
      .finally(() => setChecking(false))
  }, [setAuthed])

  if (checking) return null
  if (!authed) return <Login />

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<CommandCenter />} />
          <Route path="/office" element={<Office />} />
          <Route path="/mission/:id" element={<MissionDetail />} />
          <Route path="/department/:id" element={<DepartmentPage />} />
          <Route path="/employee/:id" element={<EmployeePage />} />
          <Route path="/boardroom" element={<Boardroom />} />
          <Route path="/model-gateway" element={<ModelGatewayPage />} />
          <Route path="/memory" element={<MemoryVault />} />
          <Route path="/skills" element={<SkillsPage />} />
          <Route path="/security" element={<Security />} />
          <Route path="/qa" element={<QAPage />} />
          <Route path="/monitoring" element={<Monitoring />} />
          <Route path="/artifacts" element={<ArtifactsPage />} />
          <Route path="/decisions" element={<DecisionsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
