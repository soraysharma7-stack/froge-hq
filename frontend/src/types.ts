export interface HQEvent {
  id: string
  timestamp: number
  type: string
  source: string
  severity: string
  message: string
  mission_id: string | null
  employee_id: string | null
  metadata: Record<string, unknown>
}

export interface Employee {
  id: string
  name: string
  department: string
  role: string
  state: string
  personality: string
  capabilities: string[]
  skills: string[]
  security_level: number
}

export interface Mission {
  id: string
  title: string
  objective: string
  status: string
  simulate: boolean
  plan: { step: number; owner: string; action: string; status: string }[]
  active_employees: string[]
  errors: string[]
  confidence: number | null
  elapsed_time: number
  final_summary: string | null
  timeline: { t: number; step: string; detail: string }[]
  outputs: Record<string, unknown>
}

export interface ModelGatewayInfo {
  provider: string | null
  model: string | null
  status: string
  requests_served: number
}

export interface Department {
  id: string
  name: string
  lead: string | null
  employees: Employee[]
  current_activity: string[]
}

export interface Approval {
  id: string
  action: string
  requester: string
  reason: string
  risk: string
  state: string
  created_at: number
}

export interface Notification {
  id: string
  timestamp: number
  kind: string
  message: string
  severity: string
  read: boolean
}
