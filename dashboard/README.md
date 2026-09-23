# FROGÉ HQ — Next.js Dashboard

A dark, teal-glow operations dashboard for FROGÉ HQ, built with Next.js 14 + TypeScript + Tailwind + shadcn-style primitives + Framer Motion + Recharts + lucide-react.

## Key design decision: no hardcoded backend URL

The WebSocket hook (`src/hooks/useFrogeSocket.ts`) derives its URL from the page origin:

- `https://your-site.com` → `wss://your-site.com/ws/events`
- `http://localhost:8000` → `ws://localhost:8000/ws/events`

Same for the REST client (`src/lib/api.ts`) — all paths are relative (`/api/...`). Serve this app from the same origin as the FastAPI backend (or reverse-proxy `/api` and `/ws` to it) and it just works, in dev and in production.

## Run

```bash
npm install
npm run dev        # http://localhost:3000 (backend must be proxied/served on same origin)
npm run build && npm start
```

## Structure

```
src/
  app/            layout.tsx, page.tsx (dashboard shell), globals.css
  hooks/          useFrogeSocket.ts  — reconnecting WebSocket hook (relative URL)
  lib/            api.ts, store.ts (useReducer global state), types.ts, cn.ts
  components/     TopBar, VisualOffice, ChatPanel, ApprovalsPanel, DataStreamLog, StatsChart, LoginGate
  components/ui/  panel.tsx — shadcn-style Panel / Badge / GlowButton / TextInput
```

## Backend contract

- WebSocket: `/ws/events` → frames `{ kind: "backlog" | "live", event: { id, type, message, source, severity, timestamp, ... } }`
- REST: `/api/auth/{config,login,signup}`, `/api/employees`, `/api/approvals`, `/api/missions`, `/api/stop-all`, `/api/stop-all/release`
