"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Bot, Crown, X } from "lucide-react";
import type { Agent } from "@/lib/types";
import { Badge, Panel } from "./ui/panel";

const statusTone: Record<Agent["status"], "gray" | "cyan" | "green" | "red"> = {
  IDLE: "gray",
  PROCESSING: "cyan",
  SUCCESS: "green",
  FAILED: "red",
};

function AgentCard({ agent, onDismiss }: { agent: Agent; onDismiss: (id: string) => void }) {
  const processing = agent.status === "PROCESSING";
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{
        opacity: 1,
        y: 0,
        scale: processing ? [1, 1.015, 1] : 1,
        boxShadow: processing
          ? "0 0 24px rgba(45,212,191,0.4)"
          : agent.status === "SUCCESS"
            ? "0 0 18px rgba(52,211,153,0.35)"
            : agent.status === "FAILED"
              ? "0 0 18px rgba(248,113,113,0.3)"
              : "0 0 0px rgba(0,0,0,0)",
      }}
      exit={{ opacity: 0, y: -8 }}
      transition={{
        duration: 0.35,
        scale: processing ? { repeat: Infinity, duration: 1.4 } : { duration: 0.2 },
      }}
      className={
        agent.isMaya
          ? "rounded-[10px] border border-amber-700/60 bg-black/40 p-4"
          : "rounded-[10px] border border-accent-dim bg-black/40 p-3"
      }
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3">
          <div
            className={
              agent.isMaya
                ? "flex h-10 w-10 items-center justify-center rounded-lg border border-amber-700/60 text-amber-400"
                : "flex h-8 w-8 items-center justify-center rounded-lg border border-accent-dim text-accent"
            }
          >
            {agent.isMaya ? <Crown className="h-5 w-5" /> : <Bot className="h-4 w-4" />}
          </div>
          <div>
            <div
              className={
                agent.isMaya
                  ? "font-mono text-sm font-bold text-amber-300"
                  : "font-mono text-sm text-zinc-100"
              }
            >
              {agent.name}
            </div>
            <div className="text-xs text-zinc-500">{agent.role}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={statusTone[agent.status]} pulse={processing}>
            {agent.status}
          </Badge>
          {agent.status === "FAILED" && (
            <button
              onClick={() => onDismiss(agent.id)}
              aria-label={`Dismiss ${agent.name} failure`}
              className="rounded-md border border-red-900 p-1 text-red-400 transition hover:bg-red-950/40"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export function VisualOffice({
  agents,
  onDismiss,
}: {
  agents: Agent[];
  onDismiss: (id: string) => void;
}) {
  const maya = agents.find((a) => a.isMaya);
  const others = agents.filter((a) => !a.isMaya);
  const active = others.filter((a) => a.status !== "IDLE");
  const idle = others.filter((a) => a.status === "IDLE");
  const showIdleCards = others.length <= 8;

  return (
    <Panel
      title="Visual Office"
      className="min-h-0"
      right={
        <span className="font-mono text-[10px] text-zinc-500">
          {agents.length} agent{agents.length === 1 ? "" : "s"}
        </span>
      }
    >
      <div className="flex flex-col gap-3">
        {maya && <AgentCard agent={maya} onDismiss={onDismiss} />}
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <AnimatePresence>
            {(showIdleCards ? others : active).map((a) => (
              <AgentCard key={a.id} agent={a} onDismiss={onDismiss} />
            ))}
          </AnimatePresence>
        </div>
        {!showIdleCards && idle.length > 0 && (
          <div className="rounded-lg border border-zinc-800 px-3 py-2 text-center font-mono text-xs text-zinc-500">
            {idle.length} idle
          </div>
        )}
      </div>
    </Panel>
  );
}
