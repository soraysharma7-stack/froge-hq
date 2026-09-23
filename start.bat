@echo off
REM FROGE HQ - one command to run everything on Windows (CMD / PowerShell).
cd /d "%~dp0"

echo ==^> Building frontend...
pushd frontend
call npm install
if errorlevel 1 goto :fail
call npm run build
if errorlevel 1 goto :fail
popd

echo ==^> Setting up backend...
cd backend
if not exist .venv (
  py -m venv .venv 2>nul || python -m venv .venv
)
set VENV_PY=.venv\Scripts\python.exe

"%VENV_PY%" -m pip install -q --upgrade pip
"%VENV_PY%" -m pip install -q -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo ==^> FROGE HQ starting on http://localhost:8000
echo     (set FROGE_OWNER_EMAIL / FROGE_OWNER_PASSWORD / FROGE_AUTH_SECRET to enable sign-in)
echo.
"%VENV_PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
goto :eof

:fail
echo.
echo FAILED. Make sure Node.js ^(https://nodejs.org^) and Python 3.10+ ^(https://python.org^) are installed.
pause
exit /b 1
