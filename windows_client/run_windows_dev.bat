@echo off
cd /d "%~dp0"
set "KORENA_SERVER_URL=http://localhost:8000"
".venv\Scripts\python.exe" korena_desktop.py
pause
