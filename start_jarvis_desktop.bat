@echo off
title JARVIS AI Assistant Desktop Suite
cd /d %~dp0
echo ======================================================================
echo          LAUNCHING JARVIS DESKTOP SUITE (PHASE 9 ^& 10)
echo ======================================================================
echo.
echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo Starting JARVIS Desktop Supervisor, Tray App, and Global Hotkeys...
python start_jarvis_desktop.py
pause

