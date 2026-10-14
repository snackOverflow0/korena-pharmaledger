@echo off
setlocal
cd /d "%~dp0" || (echo ERROR: Cannot open Korena project folder.& pause & exit /b 1)
title Korena - Administrator Password Reset

echo ================================================
echo     KORENA - ADMIN PASSWORD RECOVERY
echo ================================================
echo.
echo Run this only on a Korena database you administer.
echo No journals, ledger lines or trial balances are erased.
echo.

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Python environment missing.
  echo Run setup_windows.bat first, then try again.
  pause
  exit /b 1
)
if not exist "reset_admin_password.py" (
  echo ERROR: reset_admin_password.py was not found.
  echo Copy BOTH reset files into the same folder as app.py.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" "reset_admin_password.py"
if errorlevel 1 (
  echo.
  echo Password reset did not complete. See the message above.
  pause
  exit /b 1
)
echo.
echo Now open the Korena login page and try your new password.
pause
exit /b 0
