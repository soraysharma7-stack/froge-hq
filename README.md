# FROGÉ HQ

Virtual AI organization HQ. Maya is the Chief AI Orchestrator; a team of AI employees runs missions under a deterministic security policy, with the user as final authority.

## Run it

Backend (port 8000):

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend (port 5173, proxies API to 8000):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Model configuration (ModelGateway)

No model is hard-coded anywhere. The gateway reads ONLY environment variables:

| Variable | Purpose |
|---|---|
| `FROGE_MODEL_PROVIDER` | `openai`, `openai-compatible`, `arena`, `local`, `ollama`, `openrouter` |
| `FROGE_MODEL_NAME` | the model to call, from config |
| `FROGE_MODEL_API_BASE` | OpenAI-compatible endpoint (e.g. `http://localhost:11434/v1` for a local Ollama, or your hosted endpoint) |
| `FROGE_MODEL_API_KEY` | key, if the endpoint needs one |

Without these the gateway honestly reports **UNCONFIGURED** and missions degrade gracefully — nothing is faked. A failed provider call flips it to **DEGRADED** with the real error.

## Persistence

All state (missions, artifacts, memory vault, decisions, approvals, audit log, notifications, reputation, knowledge graph) is durable in SQLite (`FROGE_DATABASE_URL`, default `sqlite+aiosqlite:///./froge_hq.db`) and restored on startup. Structure is PostgreSQL-ready. If a save fails, the app keeps running in-memory instead of crashing.

## Resource limits (low-spec friendly)

`FROGE_MAX_ACTIVE_AGENTS=5`, `FROGE_MAX_BROWSER_INSTANCES=1` — configurable. STOP ALL works independently of the AI model.

## Tests

```bash
cd backend && .venv/bin/python -m pytest app/tests -q   # 18 passed
```
