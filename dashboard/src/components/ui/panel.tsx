import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

export function Panel({
  title,
  right,
  children,
  className,
  bodyClassName,
}: {
  title: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section
      className={cn(
        "flex min-h-0 flex-col rounded-[10px] border border-accent-dim bg-panel shadow-glow",
        className,
      )}
    >
      <header className="flex items-center justify-between gap-2 border-b border-accent-dim px-3 py-2">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent">{title}</h2>
        {right}
      </header>
      <div className={cn("min-h-0 flex-1 overflow-auto p-3", bodyClassName)}>{children}</div>
    </section>
  );
}

export function Badge({
  children,
  tone = "gray",
  pulse = false,
  className,
}: {
  children: ReactNode;
  tone?: "gray" | "cyan" | "green" | "red" | "amber";
  pulse?: boolean;
  className?: string;
}) {
  const tones: Record<string, string> = {
    gray: "border-zinc-700 text-zinc-400",
    cyan: "border-accent-dim text-accent",
    green: "border-emerald-800 text-emerald-400",
    red: "border-red-900 text-red-400",
    amber: "border-amber-800 text-amber-400",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider",
        tones[tone],
        pulse && "animate-pulse-dot",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function GlowButton({
  children,
  onClick,
  variant = "accent",
  disabled,
  className,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "accent" | "ghost" | "danger" | "success";
  disabled?: boolean;
  className?: string;
  type?: "button" | "submit";
}) {
  const variants: Record<string, string> = {
    accent:
      "border-accent-dim text-accent hover:bg-accent/10 hover:shadow-glow-lg",
    ghost: "border-zinc-700 text-zinc-300 hover:border-accent-dim hover:text-accent",
    danger: "border-red-900 text-red-400 hover:bg-red-950/40",
    success: "border-emerald-800 text-emerald-400 hover:bg-emerald-950/40",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "rounded-lg border px-3 py-1.5 font-mono text-xs uppercase tracking-wider transition-all duration-200",
        "disabled:cursor-not-allowed disabled:opacity-40",
        variants[variant],
        className,
      )}
    >
      {children}
    </button>
  );
}

export function TextInput({
  value,
  onChange,
  onSubmit,
  placeholder,
  className,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit?: () => void;
  placeholder?: string;
  className?: string;
}) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter" && onSubmit) onSubmit();
      }}
      placeholder={placeholder}
      className={cn(
        "w-full rounded-lg border border-accent-dim bg-black/40 px-3 py-2 font-mono text-sm text-zinc-200",
        "placeholder:text-zinc-600 focus:outline-none focus:shadow-glow-lg",
        className,
      )}
    />
  );
}
