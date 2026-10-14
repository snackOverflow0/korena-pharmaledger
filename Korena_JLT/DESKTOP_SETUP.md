# PharmaLedger Windows Desktop Edition

This package converts the original Flask website into a **Windows application window**, using pywebview (Microsoft Edge WebView2) and a local loopback-only Waitress server. It **does not** make the MySQL database standalone or cloud-hosted. The app retains its Journal, General Ledger, Trial Balance, login, and admin audit log at `/audit`.

## Build the EXE (Windows 10/11)

1. Install Python 3.11+ and Microsoft Edge WebView2 Runtime (normally already on Windows 11).
2. Extract the entire project folder. Double-click `build_exe.bat` (or run it in Command Prompt). Internet access is needed the first time to install Python packages.
3. The finished app is `dist\PharmaLedger\PharmaLedger.exe`. **Copy the whole `dist\PharmaLedger` folder**, not only the exe.
4. Copy your **working** original `.env` into `dist\PharmaLedger\.env`. Do not publish this file or embed passwords in the executable. Never overwrite an existing, working `.env` with the example.
5. Start MySQL in XAMPP. Your existing database and journal/audit records remain unchanged. Double-click `PharmaLedger.exe`.

## New computer / first-time database setup

1. Install XAMPP and start MySQL. In phpMyAdmin, run `CREATE DATABASE IF NOT EXISTS pharma_ledger CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;` (the included `database.sql` can also create the database).
2. In the **source project folder** (the folder containing `manage.py`), copy `.env.example` to `.env` and edit `DATABASE_URL`, `FLASK_SECRET_KEY`, `ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD`. Choose your own secure secrets, and never commit/share `.env`.
3. Run `py -m venv .venv`, then `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
4. Run `.venv\Scripts\python.exe manage.py check-db` then `.venv\Scripts\python.exe manage.py init-db` **once**. This creates missing tables and the first admin account. If an account already exists, its password is not reset.
5. Copy that configured `.env` beside the packaged exe and open it. **Keep XAMPP MySQL running** while using the app.

## Troubleshooting

- `Unknown database 'pharma_ledger'`: create the database in phpMyAdmin, then run `manage.py init-db` from the source.
- Missing tables: run `manage.py init-db` from the source.
- Can't connect to MySQL: start XAMPP MySQL and verify the password/port in `.env`.
- Login incorrect: use the administrator account **in your existing database**, not necessarily the `.env` defaults. Use the source project's `reset_admin_password.py` if necessary.
- Blank application window: install/repair **Microsoft Edge WebView2 Runtime**.
- To share the app with another PC, copy the **entire** `dist\PharmaLedger` folder, supply its own private `.env`, and make sure it can reach the MySQL database. Default database settings only work if MySQL is running on the same PC.

## Security and scope

This is an educational demo, not a certified or hardened production accounting system. The desktop window communicates over `127.0.0.1` only; no public server is created. The EXE contains application code, templates, and static assets, but no saved database or private passwords. Do not use real patient data. Back up MySQL before changing configuration. Do not distribute files containing actual secrets.
