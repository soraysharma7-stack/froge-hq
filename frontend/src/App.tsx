import { BrowserRouter, Route, Routes } from 'react-router-dom'
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
