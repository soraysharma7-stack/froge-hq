"use client";

import { useCallback, useEffect, useReducer, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useFrogeSocket } from "@/hooks/useFrogeSocket";
import { api, getToken, setToken } from "@/lib/api";
import { initialState, reducer } from "@/lib/store";
import type { ApprovalItem } from "@/lib/types";
import { ApprovalsPanel } from "@/components/ApprovalsPanel";
import { ChatPanel } from "@/components/ChatPanel";
import { DataStreamLog } from "@/components/DataStreamLog";
import { LoginGate } from "@/components/LoginGate";
import { StatsChart } from "@/components/StatsChart";
import { TopBar } from "@/components/TopBar";
import { VisualOffice } from "@/components/VisualOffice";
import { GlowButton, TextInput } from "@/components/ui/panel";

type AuthState = "loading" | "open" | "required" | "authed";

export default function DashboardPage() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [auth, setAuth] = useState<AuthState>("loading");
  const [commandOpen, setCommandOpen] = useState(false);
  const [commandText, setCommandText] = useState("");

  const { status } = useFrogeSocket({
    onEvent: useCallback((envelope) => dispatch({ type: "EVENT", envelope }), []),
  });

  // ---- auth bootstrap ----
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const cfg = await api.authConfig();
        if (cancelled) return;
        if (!cfg.auth_required) setAuth("open");
        else setAuth(getToken() ? "authed" : "required");
      } catch {
        if (!cancelled) setAuth(getToken() ? "authed" : "required");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // ---- initial data load once authed ----
  useEffect(() => {
    if (auth !== "authed" && auth !== "open") return;
    (async () => {
      try {
        const employees = await api.employees();
        dispatch({
          type: "EMPLOYEES_LOADED",
          employees: employees.map((e: any) => ({
            id: e.id || e.employee_id || e.name,
            name: e.name,
            role: e.role || e.title || "Agent",
          })),
        });
      } catch {
        /* backend may be unreachable; WS reconnect covers it */
      }
      try {
        const raw = await api.approvals("PENDING");
        const items: ApprovalItem[] = (Array.isArray(raw) ? raw : []).map((a: any) => ({
          id: a.id || a.approval_id,
          action: a.action,
          reason: a.reason || "",
          risk: a.risk || "MEDIUM",
          requester: a.requester || "maya",
          missionId: a.mission_id,
        }));
        dispatch({ type: "APPROVALS_LOADED", approvals: items });
      } catch {
        /* ignore */
      }
    })();
  }, [auth]);

  // 401 anywhere → drop back to login
  useEffect(() => {
    if (auth === "authed" && !getToken()) setAuth("required");
  }, [auth]);

  const sendCommand = useCallback(async (text: string) => {
    dispatch({ type: "USER_MESSAGE", text });
    try {
      await api.createMission(text);
    } catch (e) {
      dispatch({ type: "CLEAR_THINKING" });
      dispatch({
        type: "EVENT",
        envelope: {
          kind: "live",
          event: {
            id: `err-${Date.now()}`,
            type: "SYSTEM",
            message: `Mission rejected: ${e instanceof Error ? e.message : "unknown error"}`,
            source: "system",
            severity: "error",
            timestamp: Date.now(),
          },
        },
      });
    }
  }, []);

  const resolveApproval = useCallback(async (id: string, resolution: "APPROVED" | "DENIED") => {
    try {
      await api.resolveApproval(id, resolution);
    } catch {
      /* card still fades out; stream will re-report if it persists */
    }
    dispatch({
      type: "APPROVALS_LOADED",
      approvals: [],
    });
    // reload remaining approvals from the source of truth
    api
      .approvals("PENDING")
      .then((raw) => {
        const items: ApprovalItem[] = (Array.isArray(raw) ? raw : []).map((a: any) => ({
          id: a.id || a.approval_id,
          action: a.action,
          reason: a.reason || "",
          risk: a.risk || "MEDIUM",
          requester: a.requester || "maya",
          missionId: a.mission_id,
        }));
        dispatch({ type: "APPROVALS_LOADED", approvals: items });
      })
      .catch(() => {});
  }, []);

  const stopAll = useCallback(async () => {
    dispatch({ type: "STOP_ALL" });
    try {
      await fetch("/api/stop-all", {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken() || ""}` },
      });
    } catch {
      /* stream will reflect the true state */
    }
  }, []);

  const releaseStop = useCallback(async () => {
    dispatch({ type: "STOP_RELEASED" });
    try {
      await fetch("/api/stop-all/release", {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken() || ""}` },
      });
    } catch {
      /* ignore */
    }
  }, []);

  if (auth === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-base">
        <span className="font-mono text-xs uppercase tracking-widest text-accent animate-pulse-dot">
          Initializing HQ…
        </span>
      </div>
    );
  }

  if (auth === "required") {
    return <LoginGate onAuthed={() => setAuth("authed")} />;
  }

  const submitCommand = () => {
    const text = commandText.trim();
    if (!text) return;
    setCommandText("");
    setCommandOpen(false);
    sendCommand(text);
  };

  return (
    <div className="flex h-screen flex-col gap-3 overflow-hidden bg-base p-3">
      <TopBar
        status={status}
        stopAll={state.stopAll}
        onOpenCommand={() => setCommandOpen(true)}
        onStopAll={stopAll}
        onRelease={releaseStop}
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 lg:grid-cols-[1.6fr_1fr]">
        {/* Left column: visual office + approvals */}
        <div className="grid min-h-0 grid-rows-[1.5fr_1fr] gap-3">
          <VisualOffice
            agents={state.agents}
            onDismiss={(id) => dispatch({ type: "DISMISS_AGENT", id })}
          />
          <ApprovalsPanel approvals={state.approvals} onResolve={resolveApproval} />
        </div>

        {/* Right column: chat + data stream + chart */}
        <div className="grid min-h-0 grid-rows-[1.5fr_1fr_0.8fr] gap-3">
          <ChatPanel
            messages={state.chat}
            thinkingAgent={state.thinkingAgent}
            onSend={sendCommand}
          />
          <DataStreamLog entries={state.log} />
          <StatsChart entries={state.log} />
        </div>
      </div>

      {/* Command modal */}
      <AnimatePresence>
        {commandOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-start justify-center bg-black/70 p-4 pt-[15vh]"
            onClick={() => setCommandOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, y: -16, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -16, scale: 0.98 }}
              transition={{ duration: 0.2 }}
              className="w-full max-w-lg rounded-[10px] border border-accent-dim bg-panel p-4 shadow-glow-lg"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-3 flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-widest text-accent">
                  New Mission Command
                </span>
                <button
                  onClick={() => setCommandOpen(false)}
                  className="rounded-md border border-zinc-800 p-1 text-zinc-500 hover:text-zinc-200"
                  aria-label="Close"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <div className="flex gap-2">
                <TextInput
                  value={commandText}
                  onChange={setCommandText}
                  onSubmit={submitCommand}
                  placeholder="e.g. research AI trends and write a report"
                  className="flex-1"
                />
                <GlowButton onClick={submitCommand}>Launch</GlowButton>
              </div>
              <p className="mt-2 font-mono text-[10px] text-zinc-600">
                Sent to Maya → becomes a mission, planned and executed by the org.
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
