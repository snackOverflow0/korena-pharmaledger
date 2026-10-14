@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (py -3 -m venv .venv || goto :fail)
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :fail
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name KorenaPharmaLedger korena_desktop.py || goto :fail
echo.
echo SUCCESS: dist\KorenaPharmaLedger.exe created.
echo Set KORENA_SERVER_URL in Windows system environment before running.
pause
exit /b 0
:fail
echo BUILD FAILED
pause
exit /b 1
