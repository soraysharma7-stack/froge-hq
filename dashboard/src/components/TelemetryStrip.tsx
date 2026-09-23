"use client";

import { Cpu, MemoryStick, Users, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Mon {
  cpu_percent?: number;
  ram_percent?: number;
  active_employees?: number;
  max_active_agents?: number;
  running_missions?: number;
  mode?: string;
  stop_all_engaged?: boolean;
}

/**
 * Telemetry strip — live resource + agent readout from /api/monitoring.
 * Polls every 5s. Renders nothing on failure (backend may be unreachable).
 */
export function TelemetryStrip() {
  const [m, setM] = useState<Mon | null>(null);

  useEffect(() => {
    let dead = false;
    const load = async () => {
      try {
        const data = await api.monitoring();
        if (!dead) setM(data);
      } catch {
        /* ignore — backend may be offline */
      }
    };
    load();
    const t = setInterval(load, 5000);
    return () => {
      dead = true;
      clearInterval(t);
    };
  }, []);

  if (!m) return null;

  const items = [
    { icon: Cpu, label: "CPU", value: `${Math.round(m.cpu_percent ?? 0)}%` },
    { icon: MemoryStick, label: "RAM", value: `${Math.round(m.ram_percent ?? 0)}%` },
    {
      icon: Users,
      label: "Agents",
      value: `${m.active_employees ?? 0}/${m.max_active_agents ?? 5}`,
    },
    { icon: Zap, label: "Mode", value: m.mode ?? "ONLINE" },
  ];

  return (
    <div className="flex items-center gap-4 rounded-[10px] border border-accent-dim bg-panel px-4 py-2 shadow-glow">
      <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-accent">
        Telemetry
      </span>
      <div className="flex flex-1 items-center justify-around gap-3">
        {items.map(({ icon: Icon, label, value }) => (
          <div key={label} className="flex items-center gap-1.5">
            <Icon className="h-3.5 w-3.5 text-accent" />
            <div className="flex flex-col leading-none">
              <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-600">
                {label}
              </span>
              <span className="font-mono text-xs text-zinc-200">{value}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
