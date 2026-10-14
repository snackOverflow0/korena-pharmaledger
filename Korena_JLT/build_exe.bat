@echo off
setlocal
cd /d "%~dp0"
title Building PharmaLedger for Windows
where py >nul 2>&1
if errorlevel 1 (set "PYTHON=python") else (set "PYTHON=py")
if not exist ".venv\Scripts\python.exe" (
    %PYTHON% -m venv .venv
    if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt -r requirements-desktop.txt
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --windowed --name PharmaLedger ^
 --add-data "templates;templates" --add-data "static;static" ^
 --collect-submodules "webview" desktop_launcher.py
if errorlevel 1 goto :failed
copy /Y ".env.example" "dist\PharmaLedger\.env.example" >nul
copy /Y "DESKTOP_SETUP.md" "dist\PharmaLedger\DESKTOP_SETUP.md" >nul
copy /Y "database.sql" "dist\PharmaLedger\database.sql" >nul
echo.
echo SUCCESS: dist\PharmaLedger\PharmaLedger.exe
echo Keep the entire dist\PharmaLedger folder together.
echo Copy your configured .env beside the EXE. Never share your .env.
pause
exit /b 0
:failed
echo.
echo BUILD FAILED. Review the error above.
pause
exit /b 1
