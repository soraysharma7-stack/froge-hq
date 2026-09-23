"use client";

import { useState } from "react";
import { api, setToken } from "@/lib/api";
import { GlowButton, TextInput } from "./ui/panel";

export function LoginGate({ onAuthed }: { onAuthed: () => void }) {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const res =
        mode === "signin" ? await api.login(email, password) : await api.signup(email, password, name);
      setToken(res.access_token);
      onAuthed();
    } catch (e) {
      setError(e instanceof Error ? e.message : "authentication failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-base p-4">
      <div className="w-full max-w-sm rounded-[10px] border border-accent-dim bg-panel p-6 shadow-glow">
        <h1 className="mb-1 text-center font-mono text-lg font-bold tracking-[0.3em] text-zinc-100">
          FROGÉ <span className="text-accent">HQ</span>
        </h1>
        <p className="mb-5 text-center font-mono text-[10px] uppercase tracking-widest text-zinc-500">
          Virtual AI Organization
        </p>

        <div className="mb-4 grid grid-cols-2 gap-1 rounded-lg border border-zinc-800 p-1">
          {(["signin", "signup"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`rounded-md px-2 py-1.5 font-mono text-[11px] uppercase tracking-wider transition ${
                mode === m ? "bg-accent/10 text-accent" : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {m === "signin" ? "Sign In" : "Create Account"}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-3">
          {mode === "signup" && (
            <TextInput value={name} onChange={setName} placeholder="Name (optional)" />
          )}
          <TextInput value={email} onChange={setEmail} placeholder="Email" />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Password"
            className="w-full rounded-lg border border-accent-dim bg-black/40 px-3 py-2 font-mono text-sm text-zinc-200 placeholder:text-zinc-600 focus:shadow-glow-lg focus:outline-none"
          />
          {error && <p className="font-mono text-xs text-red-400">{error}</p>}
          <GlowButton onClick={submit} disabled={busy || !email || !password}>
            {busy ? "…" : mode === "signin" ? "Sign In" : "Create Account"}
          </GlowButton>
        </div>
      </div>
    </div>
  );
}
