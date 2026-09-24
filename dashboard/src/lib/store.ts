/**
 * Global dashboard state — a plain useReducer store, no external library.
 * Backend event types (from app/events/bus.py EventType) are mapped onto
 * agent status transitions, chat messages, approvals and the log stream.
 */

import type {
  Agent,
  ApprovalItem,
  BackendEvent,
  ChatMessage,
  LogEntry,
  WsEnvelope,
} from "./types";

export interface DashboardState {
  agents: Agent[];
  chat: ChatMessage[];
  approvals: ApprovalItem[];
  log: LogEntry[];
  thinkingAgent: string | null;
  stopAll: boolean;
  seenEventIds: string[];
}

export const initialState: DashboardState = {
  agents: [
    {
      id: "maya",
      name: "Maya",
      role: "Chief AI Orchestrator",
      status: "IDLE",
      isMaya: true,
      lastEventAt: 0,
    },
  ],
  chat: [],
  approvals: [],
  log: [],
  thinkingAgent: null,
  stopAll: false,
  seenEventIds: [],
};

export type Action =
  | { type: "EVENT"; envelope: WsEnvelope }
  | { type: "USER_MESSAGE"; text: string }
  | { type: "CLEAR_THINKING" }
  | { type: "DISMISS_AGENT"; id: string }
  | { type: "APPROVALS_LOADED"; approvals: ApprovalItem[] }
  | { type: "EMPLOYEES_LOADED"; employees: { id: string; name: string; role: string }[] }
  | { type: "STOP_ALL" }
  | { type: "STOP_RELEASED" };

const MAX_CHAT = 200;
const MAX_LOG = 300;
const MAX_SEEN = 1000;

function severityOf(event: BackendEvent): LogEntry["severity"] {
  if (event.severity === "error") return "error";
  if (event.severity === "success") return "success";
  if (event.type.includes("FAILED") || event.type.includes("BLOCK") || event.type.includes("FAILURE"))
    return "error";
  if (event.type.includes("COMPLETED") || event.type.includes("SUCCESS")) return "success";
  return "info";
}

function upsertAgent(agents: Agent[], patch: Partial<Agent> & { id: string }): Agent[] {
  const idx = agents.findIndex((a) => a.id === patch.id);
  if (idx >= 0) {
    const next = [...agents];
    next[idx] = { ...next[idx], ...patch, lastEventAt: Date.now() };
    return next;
  }
  return [
    ...agents,
    {
      name: patch.id,
      role: "Agent",
      status: "IDLE",
      isMaya: false,
      lastEventAt: Date.now(),
      ...patch,
    } as Agent,
  ];
}

function mapEventToAgentStatus(eventType: string): Agent["status"] | null {
  if (
    eventType === "AGENT_ACTIVATED" ||
    eventType === "SKILL_STARTED" ||
    eventType === "TOOL_STARTED" ||
    eventType === "MODEL_REQUEST_STARTED"
  )
    return "PROCESSING";
  if (eventType === "SKILL_COMPLETED" || eventType === "MISSION_COMPLETED" || eventType === "TOOL_COMPLETED")
    return "SUCCESS";
  if (eventType === "MISSION_FAILED" || eventType === "QA_FAILURE" || eventType === "SECURITY_BLOCK")
    return "FAILED";
  return null;
}

function applyEvent(state: DashboardState, envelope: WsEnvelope): DashboardState {
  const ev = envelope.event;
  if (state.seenEventIds.includes(ev.id)) return state;

  const seenEventIds = [...state.seenEventIds, ev.id].slice(-MAX_SEEN);
  const logEntry: LogEntry = {
    id: ev.id,
    severity: severityOf(ev),
    message: `[${ev.source}] ${ev.message}`,
    at: ev.timestamp ? ev.timestamp * (ev.timestamp < 1e12 ? 1000 : 1) : Date.now(),
  };
  const log = [...state.log, logEntry].slice(-MAX_LOG);

  let agents = state.agents;
  let chat = state.chat;
  let approvals = state.approvals;
  let thinkingAgent = state.thinkingAgent;
  let stopAll = state.stopAll;

  const who = ev.employee_id || (ev.source !== "system" ? ev.source : null);
  const status = mapEventToAgentStatus(ev.type);
  if (who && status) {
    agents = upsertAgent(agents, { id: who, name: prettyName(who), status });
    if (status === "PROCESSING") thinkingAgent = prettyName(who);
    else if (thinkingAgent === prettyName(who)) thinkingAgent = null;
  }

  if (ev.type === "SPAWN_AGENT" && ev.metadata?.employee_id) {
    agents = upsertAgent(agents, {
      id: String(ev.metadata.employee_id),
      name: prettyName(String(ev.metadata.employee_id)),
      role: String(ev.metadata.role || "Agent"),
      status: "IDLE",
    });
  }

  if (ev.type === "APPROVAL_REQUIRED") {
    const meta = ev.metadata || {};
    const id = String(meta.approval_id || ev.id);
    if (!approvals.some((a) => a.id === id)) {
      approvals = [
        ...approvals,
        {
          id,
          action: String(meta.action || ev.message),
          reason: String(meta.reason || ""),
          risk: String(meta.risk || "MEDIUM"),
          requester: String(meta.requester || ev.source),
          missionId: ev.mission_id,
        },
      ];
    }
  }

  if (ev.type === "MISSION_PAUSED") stopAll = true;
  if (ev.type === "SYSTEM" && /stop all released/i.test(ev.message)) stopAll = false;

  // Decision summaries — Maya's structured reasoning, shown as agent chat lines
  if (envelope.kind === "live" && ev.type === "DECISION_SUMMARY") {
    const meta = ev.metadata || {};
    chat = [
      ...chat,
      {
        id: ev.id,
        from: "agent" as const,
        agentName: "Maya",
        text: `[${String(meta.stage || "decision")}] ${String(meta.decision || ev.message)} — ${String(meta.reason || "")}`,
        at: Date.now(),
      },
    ].slice(-MAX_CHAT);
  }

  if (
    envelope.kind === "live" &&
    who &&
    (ev.type === "MISSION_COMPLETED" || ev.type === "MISSION_FAILED" || ev.type === "QA_FAILURE" || ev.type === "BOARDROOM_STARTED")
  ) {
    chat = [
      ...chat,
      {
        id: ev.id,
        from: "agent" as const,
        agentName: prettyName(who),
        text: ev.message,
        at: Date.now(),
      },
    ].slice(-MAX_CHAT);
  }

  return { ...state, agents, chat, approvals, log, thinkingAgent, stopAll, seenEventIds };
}

export function prettyName(id: string): string {
  if (id === "maya") return "Maya";
  const clean = id.replace(/^(emp|agent)[-_]/i, "");
  return clean.charAt(0).toUpperCase() + clean.slice(1);
}

export function reducer(state: DashboardState, action: Action): DashboardState {
  switch (action.type) {
    case "EVENT":
      return applyEvent(state, action.envelope);
    case "USER_MESSAGE":
      return {
        ...state,
        chat: [
          ...state.chat,
          { id: `u-${Date.now()}`, from: "user" as const, text: action.text, at: Date.now() },
        ].slice(-MAX_CHAT),
        thinkingAgent: "Maya",
      };
    case "CLEAR_THINKING":
      return { ...state, thinkingAgent: null };
    case "DISMISS_AGENT":
      return {
        ...state,
        agents: state.agents.map((a) => (a.id === action.id ? { ...a, status: "IDLE" } : a)),
      };
    case "APPROVALS_LOADED":
      return { ...state, approvals: action.approvals };
    case "EMPLOYEES_LOADED": {
      let agents = state.agents;
      for (const e of action.employees) {
        agents = upsertAgent(agents, { id: e.id, name: e.name, role: e.role, status: "IDLE" });
      }
      return { ...state, agents };
    }
    case "STOP_ALL":
      return { ...state, stopAll: true };
    case "STOP_RELEASED":
      return { ...state, stopAll: false };
    default:
      return state;
  }
}
