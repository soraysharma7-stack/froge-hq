"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ShieldQuestion } from "lucide-react";
import type { ApprovalItem } from "@/lib/types";
import { Badge, GlowButton, Panel } from "./ui/panel";

export function ApprovalsPanel({
  approvals,
  onResolve,
}: {
  approvals: ApprovalItem[];
  onResolve: (id: string, state: "APPROVED" | "DENIED") => void;
}) {
  return (
    <Panel
      title="Pending Approvals"
      className="min-h-0"
      right={
        <Badge tone={approvals.length > 0 ? "amber" : "gray"}>{approvals.length}</Badge>
      }
    >
      <div className="flex flex-col gap-2">
        <AnimatePresence initial={false}>
          {approvals.map((a) => (
            <motion.div
              key={a.id}
              layout
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10, transition: { duration: 0.25 } }}
              transition={{ duration: 0.3 }}
              className="rounded-[10px] border border-accent-dim bg-black/40 p-3"
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 font-mono text-xs text-zinc-200">
                  <ShieldQuestion className="h-3.5 w-3.5 text-amber-400" />
                  <span className="truncate">{a.action}</span>
                </div>
                <Badge tone={a.risk === "HIGH" ? "red" : "amber"}>
                  Tier {a.risk === "HIGH" ? "2" : "1"}
                </Badge>
              </div>
              {a.reason && <p className="mb-2 text-xs text-zinc-500">{a.reason}</p>}
              <div className="flex gap-2">
                <GlowButton
                  variant="success"
                  className="flex-1"
                  onClick={() => onResolve(a.id, "APPROVED")}
                >
                  Approve
                </GlowButton>
                <GlowButton
                  variant="danger"
                  className="flex-1"
                  onClick={() => onResolve(a.id, "DENIED")}
                >
                  Deny
                </GlowButton>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {approvals.length === 0 && (
          <div className="py-6 text-center font-mono text-xs text-zinc-600">
            Nothing waiting for you.
          </div>
        )}
      </div>
    </Panel>
  );
}
