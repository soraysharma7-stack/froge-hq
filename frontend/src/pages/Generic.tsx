// Department / Employee detail pages + simple data pages
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../services/api'
import type { Department, Employee } from '../types'

export function DepartmentPage() {
  const { id } = useParams()
  const [dept, setDept] = useState<Department | null>(null)
  useEffect(() => { api.get(`/departments/${id}`).then(setDept).catch(() => {}) }, [id])
  if (!dept) return <p className="text-slate-500">Loading…</p>
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-200">{dept.name}</h2>
      <p className="text-xs text-slate-500">Lead: {dept.lead ?? '—'}</p>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {dept.employees.map((e) => (
          <Link key={e.id} to={`/employee/${e.id}`} className="holo-panel block p-4 hover:border-cyan-400/50">
            <p className="font-semibold">{e.name}</p>
            <p className="text-xs text-slate-500">{e.role}</p>
            <p className="mt-1 text-xs text-cyan-400">{e.state}</p>
          </Link>
        ))}
        {dept.employees.length === 0 && <p className="text-xs text-slate-600">No employees assigned yet.</p>}
      </div>
    </div>
  )
}

export function EmployeePage() {
  const { id } = useParams()
  const [emp, setEmp] = useState<Employee | null>(null)
  const [rep, setRep] = useState<{ score: number; missions_success: number; missions_failed: number } | null>(null)
  useEffect(() => {
    api.get(`/employees/${id}`).then(setEmp).catch(() => {})
    api.get('/reputation').then((all) => setRep(all.find((r: { employee_id: string }) => r.employee_id === id) ?? null))
  }, [id])
  if (!emp) return <p className="text-slate-500">Loading…</p>
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-200">{emp.name} <span className="text-sm text-slate-500">— {emp.role}</span></h2>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="holo-panel p-3"><p className="holo-title">State</p><p className="mt-1 text-sm">{emp.state}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Security Level</p><p className="mt-1 text-sm">{emp.security_level}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Reputation</p><p className="mt-1 text-sm">{rep ? `${rep.score} (${rep.missions_success}✓/${rep.missions_failed}✗)` : '—'}</p></div>
        <div className="holo-panel p-3"><p className="holo-title">Department</p><p className="mt-1 text-sm">{emp.department}</p></div>
      </div>
      <div className="holo-panel p-4 text-xs space-y-1">
        <p><span className="text-slate-500">Personality:</span> {emp.personality}</p>
        <p><span className="text-slate-500">Capabilities:</span> {emp.capabilities.join(', ')}</p>
        <p><span className="text-slate-500">Skills:</span> {emp.skills.join(', ') || '—'}</p>
      </div>
    </div>
  )
}
