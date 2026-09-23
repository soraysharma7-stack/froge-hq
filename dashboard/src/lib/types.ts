/**
 * Shared types matching the FROGÉ HQ backend event bus contract.
 */

export interface BackendEvent {
  id: string;
  type: string;
  message: string;
  source: string;
  severity: "info" | "success" | "error" | string;
  timestamp: number;
  mission_id?: string | null;
  employee_id?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface WsEnvelope {
  kind: "backlog" | "live";
  event: BackendEvent;
}

export type AgentStatus = "IDLE" | "PROCESSING" | "SUCCESS" | "FAILED";

export interface Agent {
  id: string;
  name: string;
  role: string;
  status: AgentStatus;
  isMaya: boolean;
  lastEventAt: number;
}

export interface ChatMessage {
  id: string;
  from: "user" | "agent";
  agentName?: string;
  text: string;
  at: number;
}

export interface ApprovalItem {
  id: string;
  action: string;
  reason: string;
  risk: string;
  requester: string;
  missionId?: string | null;
}

export interface LogEntry {
  id: string;
  severity: "info" | "success" | "error";
  message: string;
  at: number;
}
