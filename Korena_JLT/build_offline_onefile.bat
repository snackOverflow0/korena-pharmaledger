@echo off
setlocal
cd /d "%~dp0"
title PharmaLedger - Offline One-File Build
if not exist ".venv\Scripts\python.exe" (
  py -m venv .venv
  if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel pyinstaller pyinstaller-hooks-contrib
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt -r requirements-desktop.txt
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name PharmaLedger ^
  --add-data "templates;templates" --add-data "static;static" ^
  --collect-submodules webview desktop_launcher.py
if errorlevel 1 goto :failed
echo.
echo SUCCESS: dist\PharmaLedger.exe
echo Send this EXE by itself. Each PC gets its own local database and admin login.
pause
exit /b 0
:failed
echo.
echo BUILD FAILED. See errors above.
pause
exit /b 1
