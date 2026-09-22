/**
 * FROGÉ HQ — UI primitives (shadcn/ui-style).
 *
 * Zero-dependency, Tailwind v4 compatible components following the shadcn/ui
 * composition pattern: small, composable, className-overridable. They adopt
 * the existing holo theme so every page upgrades without rewrites.
 */
import type { ReactNode } from 'react'

type Props = {
  children?: ReactNode
  className?: string
}

const cx = (...parts: Array<string | false | undefined>) => parts.filter(Boolean).join(' ')

/* ---------- Card (holo-panel compatible) ---------- */

export function Card({ children, className }: Props) {
  return <section className={cx('holo-panel p-4', className)}>{children}</section>
}

export function CardHeader({ children, className }: Props) {
  return <div className={cx('mb-3 flex items-center justify-between', className)}>{children}</div>
}

export function CardTitle({ children, className }: Props) {
  return <p className={cx('holo-title', className)}>{children}</p>
}

export function CardContent({ children, className }: Props) {
  return <div className={cx('space-y-2', className)}>{children}</div>
}

/* ---------- Badge ---------- */

const BADGE_TONES: Record<string, string> = {
  default: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300',
  success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  warning: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
  danger: 'border-red-500/30 bg-red-500/10 text-red-300',
  muted: 'border-slate-500/30 bg-slate-500/10 text-slate-400',
}

export function Badge({
  children,
  className,
  tone = 'default',
}: Props & { tone?: keyof typeof BADGE_TONES }) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wider',
        BADGE_TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}

/* ---------- StatusBadge — maps HQ states to tones honestly ---------- */

const STATE_TONES: Record<string, keyof typeof BADGE_TONES> = {
  ONLINE: 'success', COMPLETED: 'success', ACTIVE: 'success', APPROVED: 'success', FINAL: 'success',
  DEGRADED: 'warning', PAUSED: 'warning', PENDING: 'warning', WARNING: 'warning', MODIFIED: 'warning',
  OFFLINE: 'danger', FAILED: 'danger', BLOCKED: 'danger', DENIED: 'danger', STOP_ALL: 'danger',
  UNCONFIGURED: 'muted', DRAFT: 'muted', CANCELLED: 'muted',
}

export function StatusBadge({ state, className }: { state: string; className?: string }) {
  const tone = STATE_TONES[state?.toUpperCase?.() ?? ''] ?? 'muted'
  return <Badge tone={tone} className={className}>{state || 'UNKNOWN'}</Badge>
}

/* ---------- Button ---------- */

const BUTTON_VARIANTS: Record<string, string> = {
  default: 'border-cyan-500/40 bg-cyan-500/10 text-cyan-200 hover:bg-cyan-500/20',
  danger: 'border-red-500/40 bg-red-500/10 text-red-200 hover:bg-red-500/20',
  ghost: 'border-transparent bg-transparent text-slate-300 hover:bg-slate-500/10',
}

export function Button({
  children,
  className,
  variant = 'default',
  disabled,
  onClick,
  type = 'button',
}: Props & {
  variant?: keyof typeof BUTTON_VARIANTS
  disabled?: boolean
  onClick?: () => void
  type?: 'button' | 'submit'
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={cx(
        'rounded-md border px-3 py-1.5 text-xs transition-colors disabled:cursor-not-allowed disabled:opacity-40',
        BUTTON_VARIANTS[variant],
        className,
      )}
    >
      {children}
    </button>
  )
}

/* ---------- Input ---------- */

export function Input({
  className,
  ...rest
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...rest}
      className={cx(
        'w-full rounded-md border border-cyan-500/20 bg-black/30 px-3 py-1.5 text-sm text-slate-100',
        'placeholder:text-slate-500 focus:border-cyan-400/50 focus:outline-none',
        className,
      )}
    />
  )
}

/* ---------- Separator ---------- */

export function Separator({ className }: { className?: string }) {
  return <hr className={cx('border-cyan-500/10', className)} />
}

/* ---------- EmptyState — honest "nothing here yet" ---------- */

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-600/40 p-6 text-center">
      <p className="text-sm text-slate-400">{title}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  )
}
