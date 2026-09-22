import { create } from 'zustand'
import type { HQEvent, Employee, Mission, ModelGatewayInfo, Notification } from './types'

interface HQState {
  events: HQEvent[]
  employees: Employee[]
  missions: Mission[]
  gateway: ModelGatewayInfo | null
  notifications: Notification[]
  wsConnected: boolean
  stopAll: boolean
  mode: string
  addEvent: (e: HQEvent) => void
  setBacklog: (e: HQEvent[]) => void
  setEmployees: (e: Employee[]) => void
  setMissions: (m: Mission[]) => void
  setGateway: (g: ModelGatewayInfo) => void
  setNotifications: (n: Notification[]) => void
  setWsConnected: (v: boolean) => void
  setStopAll: (v: boolean) => void
  setMode: (v: string) => void
}

export const useHQ = create<HQState>((set) => ({
  events: [],
  employees: [],
  missions: [],
  gateway: null,
  notifications: [],
  wsConnected: false,
  stopAll: false,
  mode: 'ONLINE',
  addEvent: (e) => set((s) => ({ events: [...s.events.slice(-299), e] })),
  setBacklog: (events) => set({ events }),
  setEmployees: (employees) => set({ employees }),
  setMissions: (missions) => set({ missions }),
  setGateway: (gateway) => set({ gateway }),
  setNotifications: (notifications) => set({ notifications }),
  setWsConnected: (wsConnected) => set({ wsConnected }),
  setStopAll: (stopAll) => set({ stopAll }),
  setMode: (mode) => set({ mode }),
}))
