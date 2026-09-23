"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef } from "react";
import type { LogEntry } from "@/lib/types";
import { Panel } from "./ui/panel";

const dotColor: Record<LogEntry["severity"], string> = {
  info: "bg-accent",
  success: "bg-emerald-400",
  error: "bg-red-500",
};

function formatTime(at: number): string {
  const d = new Date(at);
  return d.toLocaleTimeString("en-GB", { hour12: false });
}

export function DataStreamLog({ entries }: { entries: LogEntry[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [entries.length]);

  return (
    <Panel title="Data Stream" className="min-h-0" bodyClassName="p-0">
      <div ref={scrollRef} className="h-full overflow-y-auto overflow-x-auto p-3">
        <div className="flex min-w-max flex-col gap-1">
          <AnimatePresence initial={false}>
            {entries.map((e) => (
              <motion.div
                key={e.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className="flex items-center gap-2 whitespace-nowrap font-mono text-[11px]"
              >
                <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dotColor[e.severity]}`} />
                <span className="text-zinc-600">{formatTime(e.at)}</span>
                <span className={e.severity === "error" ? "text-red-400" : "text-zinc-400"}>
                  {e.message}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
          {entries.length === 0 && (
            <div className="py-6 text-center font-mono text-xs text-zinc-600">
              Waiting for backend events…
            </div>
          )}
        </div>
      </div>
    </Panel>
  );
}
