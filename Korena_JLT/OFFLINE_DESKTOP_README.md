# PharmaLedger Offline Windows Desktop (one-file edition)

## Build on Windows

1. Unzip the project into a folder; do not overwrite or delete your original MySQL installation.
2. Double-click `build_offline_onefile.bat` (or in PowerShell run `./build_offline_onefile.bat`).
3. If the build succeeds, send **only** `dist/PharmaLedger.exe` to your classmate.
4. On each Windows computer, double-click the EXE, supply an admin email and password of at least 10 characters in the first-run dialogs, then sign in with that email/password.

No XAMPP/MySQL or `.env` is required for the offline EXE. Windows may require the Microsoft Edge WebView2 Runtime to be installed. Antivirus/SmartScreen may warn about newly compiled unsigned EXEs. The EXE is built **on Windows**, not inside this ZIP.

## Where your data lives

Each PC stores **its own independent data** in `%LOCALAPPDATA%\PharmaLedger\pharmaledger.sqlite3` and a local private Flask signing key in `%LOCALAPPDATA%\PharmaLedger\.flask_secret`.

Do **not** delete this directory if you want to keep the accounts, journal entries, or audit trail. Back up the SQLite file while the application is closed. The EXE can be replaced without deleting data. Classmates do NOT automatically share entries or audit logs.

## Important limitations

- This is an **offline local SQLite edition**, not a synchronization/migration of the existing MySQL database. MySQL data will **not** appear automatically; export/import is a separate task.
- The audit trail works with the local SQLite database; it is not synchronized between devices.
- The single-file EXE unpacks temporary runtime files when started; this is normal for PyInstaller.
- The EXE is **not compiled here**. Build it on Windows and verify it before distribution.
- Treat the EXE and database as local files and keep appropriate backups. SQLite is suited to a single-PC demonstration, not concurrent multi-PC updates.
