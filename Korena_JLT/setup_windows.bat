@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0" || (echo ERROR: Cannot open the Korena project folder.& pause & exit /b 1)
title Korena - First-time Setup

echo ===================================================
echo   KORENA - Journal, Ledger and Trial Balance

echo   First-time installation (Windows)
echo ===================================================
echo.

if not exist "requirements.txt" (
    echo ERROR: requirements.txt is missing.
    echo Put this BAT file beside app.py and requirements.txt.
    goto :failed
)
if not exist "manage.py" (
    echo ERROR: manage.py is missing.
    echo Put this BAT file in the MAIN Korena project folder.
    goto :failed
)

echo [1/5] Preparing the Python environment...
if exist ".venv\Scripts\python.exe" goto :environment_ready

where py >nul 2>&1
if not errorlevel 1 (
    py -3 -m venv ".venv"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python was not found.
        echo Install Python 3.11 or later and enable Add Python to PATH.
        goto :failed
    )
    python -m venv ".venv"
)
if errorlevel 1 (
    echo ERROR: Could not create the Python environment.
    goto :failed
)

:environment_ready
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo ERROR: This project needs Python 3.11 or later.
    echo If .venv contains an old Python version, delete ONLY .venv and retry.
    goto :failed
)
echo Python environment is ready.
echo.

echo [2/5] Installing required Python packages...
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    echo Check your internet connection, then rerun this setup file.
    goto :failed
)
echo.

echo [3/5] Preparing .env settings...
if not exist ".env" (
    if not exist ".env.example" (
        echo ERROR: .env.example is missing.
        goto :failed
    )
    copy /Y ".env.example" ".env" >nul
    if errorlevel 1 (
        echo ERROR: Could not create the .env file.
        goto :failed
    )
    echo Created .env from .env.example.
) else (
    echo Kept your existing .env file. Nothing was overwritten.
)
echo.
echo The .env file holds your MySQL connection, secret key and admin login.
echo Do NOT share .env or your passwords in a submitted ZIP.
echo If you already have a working .env, you can keep it.
choice /C YN /N /M "Open .env in Notepad to review it? [Y/N] "
if errorlevel 2 goto :validate_settings
start "" notepad.exe ".env"
echo Save .env in Notepad, then return to this window.
pause

:validate_settings
echo.
echo [4/5] Checking your configuration (without printing passwords)...
".venv\Scripts\python.exe" -c "import os,sys; from dotenv import load_dotenv; load_dotenv('.env'); k=os.getenv('FLASK_SECRET_KEY',''); p=os.getenv('INITIAL_ADMIN_PASSWORD',''); d=os.getenv('DATABASE_URL',''); sys.exit(0 if len(k)>=24 and not k.startswith('REPLACE_') and len(p)>=10 and p!='ChangeThisPassword123!' and not p.startswith('REPLACE_') and bool(d) else 1)"
if not errorlevel 1 goto :database_setup

echo.
echo ACTION NEEDED: .env still has missing or sample settings.
echo Set FLASK_SECRET_KEY to a random 24+ character value.
echo Set INITIAL_ADMIN_PASSWORD to your own 10+ character password.
echo Check DATABASE_URL against your XAMPP MySQL login and port.
echo To generate a random secret in Antigravity terminal, use:
echo   py -c "import secrets; print(secrets.token_hex(32))"
echo.
choice /C RE /N /M "[R] Reopen .env or [E] Exit to edit it later? "
if errorlevel 2 goto :not_finished
start "" notepad.exe ".env"
echo Save .env, then return to this window.
pause
goto :validate_settings

:database_setup
echo Configuration looks ready.
echo.
echo [5/5] Connecting to XAMPP MySQL and creating missing tables...
echo IMPORTANT: MySQL must be running in XAMPP.
echo IMPORTANT: The database.sql file must have been imported first.
".venv\Scripts\python.exe" manage.py check-db
if errorlevel 1 (
    echo.
    echo ERROR: Korena could not connect to MySQL.
    echo Start MySQL in XAMPP, check DATABASE_URL in .env,
    echo and import database.sql in phpMyAdmin if you have not done so.
    echo Your existing database was not deleted.
    goto :failed
)
".venv\Scripts\python.exe" manage.py init-db
if errorlevel 1 (
    echo.
    echo ERROR: Database initialization failed. Read the error above.
    echo Fix the configuration, then rerun setup_windows.bat.
    goto :failed
)
echo.
echo Core database setup succeeded. Existing entries were preserved.
echo.
choice /C YN /N /M "Load 10 FICTIONAL pharmacy demo entries into an EMPTY journal? [Y/N] "
if errorlevel 2 goto :success
".venv\Scripts\python.exe" manage.py seed-demo
if errorlevel 1 (
    echo.
    echo Demo data was NOT added. This is normal if journal entries already exist.
    echo Your existing journal records were protected.
    goto :success
)

:success
echo.
echo ===================================================
echo   Setup complete!
echo   Next: double-click start_windows.bat
echo   If an admin user existed, use its ORIGINAL password.
echo ===================================================
pause
exit /b 0

:not_finished
echo.
echo Setup paused. Finish editing .env, then run this BAT file again.
pause
exit /b 1

:failed
echo.
echo Setup was not completed. Correct the issue above and rerun.
pause
exit /b 1
