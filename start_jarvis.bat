@echo off
echo ===================================================
echo          STARTING JARVIS AI ASSISTANT BACKEND
echo ===================================================
echo.
echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo Starting FastAPI Server on http://127.0.0.1:8000 ...
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

pause
