@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0" || (echo ERROR: Cannot open the Korena project folder.& pause & exit /b 1)
title Korena - Accounting System

echo ===================================================
echo   KORENA - Journal, Ledger and Trial Balance

echo ===================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Python environment is missing.
    echo Double-click setup_windows.bat first.
    goto :failed
)
if not exist ".env" (
    echo ERROR: .env settings file is missing.
    echo Double-click setup_windows.bat first.
    goto :failed
)
if not exist "app.py" (
    echo ERROR: app.py was not found in this folder.
    goto :failed
)

echo [1/3] Checking connection to XAMPP MySQL...
".venv\Scripts\python.exe" manage.py check-db
if errorlevel 1 (
    echo.
    echo ERROR: Cannot connect to your MySQL database.
    echo Start MySQL in XAMPP and check DATABASE_URL in .env.
    echo If this is the first run, launch setup_windows.bat.
    goto :failed
)

echo.
echo [2/3] Preparing the browser...
set "APP_PORT=5000"
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /I "%%A"=="PORT" set "APP_PORT=%%B"
)
rem Accept numeric ports only. Invalid values fall back to 5000.
echo(%APP_PORT%|findstr /R "^[0-9][0-9]*$" >nul
if errorlevel 1 set "APP_PORT=5000"

echo [3/3] Starting Korena at http://127.0.0.1:%APP_PORT%/
echo Please KEEP THIS WINDOW OPEN while using Korena.
echo Press Ctrl+C to stop the server.
echo.
rem In a separate minimized process, wait until Flask responds before opening a browser.
start "Korena Browser" /min powershell.exe -NoProfile -Command "$u='http://127.0.0.1:%APP_PORT%/'; for($i=0;$i -lt 30;$i++){try { Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 2 -ErrorAction Stop | Out-Null; Start-Process $u; break } catch { Start-Sleep -Seconds 1 }}"
".venv\Scripts\python.exe" app.py
if errorlevel 1 (
    echo.
    echo Korena stopped with an error. Read the message above.
    goto :failed
)
echo Korena has stopped.
pause
exit /b 0

:failed
pause
exit /b 1
