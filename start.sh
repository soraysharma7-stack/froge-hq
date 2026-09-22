#!/usr/bin/env bash
# FROGÉ HQ — one command to run everything (backend + built frontend on one URL).
set -e
cd "$(dirname "$0")"

echo "==> Building frontend…"
(cd frontend && npm install && npm run build)

echo "==> Setting up backend…"
cd backend
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "==> FROGÉ HQ starting on http://localhost:8000"
echo "    (set FROGE_OWNER_EMAIL / FROGE_OWNER_PASSWORD to enable sign-in)"
echo ""
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
