"use client";

import { useMemo } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { LogEntry } from "@/lib/types";
import { Panel } from "./ui/panel";

export function StatsChart({ entries }: { entries: LogEntry[] }) {
  const data = useMemo(() => {
    const buckets = new Map<string, number>();
    const now = Date.now();
    for (let i = 11; i >= 0; i--) {
      const t = new Date(now - i * 60_000);
      const key = `${String(t.getHours()).padStart(2, "0")}:${String(t.getMinutes()).padStart(2, "0")}`;
      buckets.set(key, 0);
    }
    for (const e of entries) {
      const t = new Date(e.at);
      const key = `${String(t.getHours()).padStart(2, "0")}:${String(t.getMinutes()).padStart(2, "0")}`;
      if (buckets.has(key)) buckets.set(key, (buckets.get(key) || 0) + 1);
    }
    return Array.from(buckets, ([time, count]) => ({ time, count }));
  }, [entries]);

  return (
    <Panel title="Activity (events/min)" className="min-h-0" bodyClassName="p-2">
      <div className="h-full min-h-[120px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -22 }}>
            <defs>
              <linearGradient id="accentFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              tick={{ fill: "#52525b", fontSize: 9, fontFamily: "JetBrains Mono, monospace" }}
              tickLine={false}
              axisLine={{ stroke: "#27272a" }}
              interval={3}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: "#52525b", fontSize: 9, fontFamily: "JetBrains Mono, monospace" }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "#0e0e14",
                border: "1px solid rgba(45,212,191,0.35)",
                borderRadius: 8,
                fontFamily: "JetBrains Mono, monospace",
                fontSize: 11,
              }}
              labelStyle={{ color: "#2dd4bf" }}
              itemStyle={{ color: "#d4d4d8" }}
            />
            <Area
              type="monotone"
              dataKey="count"
              stroke="#2dd4bf"
              strokeWidth={1.5}
              fill="url(#accentFill)"
              isAnimationActive
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  );
}
