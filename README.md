# FROGÉ HQ

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-froge--hq.onrender.com-blue)](https://froge-hq.onrender.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-yellow)](https://www.python.org)
[![React + TypeScript](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61dafb)](https://react.dev)

**Live web app: https://froge-hq.onrender.com**

**Best free AI agents platform & visual AI company — open source (MIT).** Maya is the Chief AI Orchestrator; a team of AI employees runs missions in a live visual office under a deterministic security policy, with you as final authority.

Keywords: best free AI agents · free AI agent platform · visual AI company · multi-agent orchestration · AI workforce

## Run it — pick your device

**Prerequisite (all devices):** install [Node.js 18+](https://nodejs.org) and [Python 3.10+](https://www.python.org/downloads/). On Windows, during Python install tick **"Add python.exe to PATH"**.

### Easiest — GitHub Codespaces (no install, runs in the browser; best for low-RAM machines)

1. Open the repo on GitHub → green **Code** button → **Codespaces** tab → **Create codespace on main**.
2. In the Codespaces terminal, run:
   ```bash
   bash start.sh
   ```
3. When the port popup appears, click **Open in Browser** (port **8000**). That's your FROGÉ HQ.

### macOS / Linux

```bash
bash start.sh
```
Open **http://localhost:8000**

### Windows (CMD or PowerShell)

```bat
start.bat
```
Open **http://localhost:8000**

### Windows (Git Bash / WSL)

```bash
bash start.sh
```

---

## Dev mode (optional, for editing the UI with hot reload)

Terminal 1 — backend (port 8000):
```bash
cd backend
python3 -m venv .venv        # Windows: py -m venv .venv
source .venv/bin/activate    # Windows CMD/PowerShell: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Terminal 2 — frontend (port 5173, proxies API to 8000):
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

---

## Sign-in (owner login)

Optional in dev, recommended in production. Set these before starting:

```bash
export FROGE_OWNER_EMAIL="you@example.com"      # Windows CMD: set FROGE_OWNER_EMAIL=you@example.com
export FROGE_OWNER_PASSWORD="a-strong-password"
export FROGE_AUTH_SECRET="any-long-random-string"
```
When unset, the app runs in open dev mode (no login). When set, every `/api` route requires the Bearer token from the login screen.

## Model configuration (ModelGateway)

No model is hard-coded anywhere. The gateway reads ONLY environment variables:

| Variable | Purpose |
|---|---|
| `FROGE_MODEL_PROVIDER` | `openai`, `openai-compatible`, `arena`, `local`, `ollama`, `openrouter` |
| `FROGE_MODEL_NAME` | the model to call |
| `FROGE_MODEL_API_BASE` | OpenAI-compatible endpoint (e.g. `http://localhost:11434/v1` for a local Ollama) |
| `FROGE_MODEL_API_KEY` | key, if the endpoint needs one |

Without these the gateway honestly reports **UNCONFIGURED** and missions degrade gracefully — nothing is faked. A failed provider call flips it to **DEGRADED** with the real error.

## Persistence

All state (missions, artifacts, memory vault, decisions, approvals, audit log, notifications, reputation, knowledge graph) is durable in SQLite (`FROGE_DATABASE_URL`, default `sqlite+aiosqlite:///./froge_hq.db`) and restored on startup. Structure is PostgreSQL-ready.

## Resource limits (low-spec friendly)

`FROGE_MAX_ACTIVE_AGENTS=5`, `FROGE_MAX_BROWSER_INSTANCES=1` — configurable. STOP ALL works independently of the AI model.

## Deploy (one live URL)

`render.yaml` is included. On [Render](https://render.com): **New → Blueprint** → connect this repo. It builds the frontend, installs the backend, and serves both from one URL.

## Tests

```bash
cd backend && .venv/bin/python -m pytest -q   # 18 passed
```
