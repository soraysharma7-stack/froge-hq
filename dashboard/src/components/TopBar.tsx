"use client";

import { Activity, Command, OctagonX, Play, Users } from "lucide-react";
import { Badge, GlowButton } from "./ui/panel";
import type { ConnectionStatus } from "@/hooks/useFrogeSocket";

export function TopBar({
  status,
  stopAll,
  onOpenCommand,
  onCallMeeting,
  onStopAll,
  onRelease,
}: {
  status: ConnectionStatus;
  stopAll: boolean;
  onOpenCommand: () => void;
  onCallMeeting: () => void;
  onStopAll: () => void;
  onRelease: () => void;
}) {
  return (
    <header className="flex items-center justify-between gap-3 rounded-[10px] border border-accent-dim bg-panel px-4 py-2.5 shadow-glow">
      <div className="flex items-center gap-3">
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-60" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-accent" />
        </span>
        <h1 className="font-mono text-sm font-bold tracking-[0.3em] text-zinc-100">
          FROGÉ <span className="text-accent">HQ</span>
        </h1>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span
            className={
              status === "connected"
                ? "h-2 w-2 animate-pulse-dot rounded-full bg-emerald-400"
                : status === "connecting"
                  ? "h-2 w-2 animate-pulse-dot rounded-full bg-amber-400"
                  : "h-2 w-2 rounded-full bg-red-500"
            }
          />
          <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
            {status}
          </span>
        </div>

        {stopAll ? (
          <Badge tone="red" pulse>
            STOPPED
          </Badge>
        ) : (
          <Badge tone="cyan">
            <Activity className="h-3 w-3" /> LIVE
          </Badge>
        )}

        <GlowButton onClick={onCallMeeting}>
          <Users className="mr-1 inline h-3.5 w-3.5" /> Meeting
        </GlowButton>

        <GlowButton onClick={onOpenCommand}>
          <Command className="mr-1 inline h-3.5 w-3.5" /> Type Command
        </GlowButton>

        {stopAll ? (
          <GlowButton variant="success" onClick={onRelease}>
            <Play className="mr-1 inline h-3.5 w-3.5" /> Release
          </GlowButton>
        ) : (
          <GlowButton variant="danger" onClick={onStopAll}>
            <OctagonX className="mr-1 inline h-3.5 w-3.5" /> Stop All
          </GlowButton>
        )}
      </div>
    </header>
  );
}
