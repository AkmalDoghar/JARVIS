@echo off
echo ===================================================
echo     STARTING FULL JARVIS SYSTEM (BACKEND + FRONTEND)
echo ===================================================
echo.

echo Launching JARVIS FastAPI Backend on http://127.0.0.1:8000 ...
start "JARVIS Backend (FastAPI)" cmd /k "cd /d %~dp0 && .\.venv\Scripts\activate.bat && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 >nul

echo Launching JARVIS Next.js Desktop Dashboard on http://localhost:3000 ...
start "JARVIS Desktop UI (Next.js)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ===================================================
echo JARVIS is starting!
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:3000
echo ===================================================
echo.
pause
