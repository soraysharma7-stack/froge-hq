#!/usr/bin/env bash
# FROGÉ HQ — one command to run everything (backend + built frontend on one URL).
# Works on macOS, Linux, and Windows (Git Bash / WSL).
set -e
cd "$(dirname "$0")"

PY=python3
command -v python3 >/dev/null 2>&1 || PY=python
echo "==> Using $("$PY" --version 2>&1)"

echo "==> Building frontend…"
(cd frontend && npm install && npm run build)

echo "==> Setting up backend…"
cd backend
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
# venv layout: bin on macOS/Linux, Scripts on Windows venvs
if [ -f .venv/bin/python ]; then
  VENV_PY=.venv/bin/python
else
  VENV_PY=.venv/Scripts/python.exe
fi

"$VENV_PY" -m pip install -q --upgrade pip
"$VENV_PY" -m pip install -q -r requirements.txt

echo ""
echo "==> FROGÉ HQ starting on http://localhost:${PORT:-8000}"
echo "    (set FROGE_OWNER_EMAIL / FROGE_OWNER_PASSWORD / FROGE_AUTH_SECRET to enable sign-in)"
echo ""
exec "$VENV_PY" -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
