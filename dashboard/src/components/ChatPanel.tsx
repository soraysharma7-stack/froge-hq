"use client";

import { AnimatePresence, motion } from "framer-motion";
import { SendHorizonal } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "@/lib/types";
import { GlowButton, Panel, TextInput } from "./ui/panel";
import { VoiceMic } from "./VoiceMic";

function ThinkingDots() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex items-center gap-1.5 px-1 font-mono text-xs text-accent"
    >
      <span>thinking</span>
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          animate={{ opacity: [0.2, 1, 0.2] }}
          transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2 }}
        >
          .
        </motion.span>
      ))}
    </motion.div>
  );
}

export function ChatPanel({
  messages,
  thinkingAgent,
  onSend,
}: {
  messages: ChatMessage[];
  thinkingAgent: string | null;
  onSend: (text: string) => void;
}) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length, thinkingAgent]);

  const submit = () => {
    const text = draft.trim();
    if (!text) return;
    setDraft("");
    onSend(text);
  };

  return (
    <Panel title="Chat" className="min-h-0" bodyClassName="flex min-h-0 flex-col gap-0 p-0">
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto p-3">
        <div className="flex flex-col gap-2">
          <AnimatePresence initial={false}>
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 10, x: m.from === "user" ? 12 : -12 }}
                animate={{ opacity: 1, y: 0, x: 0 }}
                transition={{ duration: 0.3 }}
                className={m.from === "user" ? "self-end text-right" : "self-start"}
              >
                {m.from === "agent" && (
                  <div className="mb-0.5 font-mono text-[10px] uppercase tracking-wider text-accent">
                    {m.agentName || "agent"}
                  </div>
                )}
                <div
                  className={
                    m.from === "user"
                      ? "inline-block max-w-[85%] rounded-[10px] border border-accent-dim bg-accent/10 px-3 py-2 text-left text-sm text-zinc-100"
                      : "inline-block max-w-[85%] rounded-[10px] border border-zinc-800 bg-black/40 px-3 py-2 text-sm text-zinc-300"
                  }
                >
                  {m.text}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <AnimatePresence>
            {thinkingAgent && (
              <div className="self-start">
                <div className="mb-0.5 font-mono text-[10px] uppercase tracking-wider text-accent">
                  {thinkingAgent}
                </div>
                <ThinkingDots />
              </div>
            )}
          </AnimatePresence>
          {messages.length === 0 && !thinkingAgent && (
            <div className="py-8 text-center font-mono text-xs text-zinc-600">
              No messages yet. Give Maya a mission.
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 border-t border-accent-dim p-2">
        <TextInput
          value={draft}
          onChange={setDraft}
          onSubmit={submit}
          placeholder="Type a command for Maya…"
          className="flex-1"
        />
        <VoiceMic onTranscript={(text) => setDraft(text)} />
        <GlowButton onClick={submit} aria-label="Send message">
          <SendHorizonal className="h-4 w-4" />
        </GlowButton>
      </div>
    </Panel>
  );
}
