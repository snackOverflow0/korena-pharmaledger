# PharmaLedger — Journal • General Ledger • Trial Balance

A simplified **Python (Flask) + XAMPP MySQL** academic project. There are **only three accounting modules** in the sidebar:

1. **Journal:** record transactions as debit/credit entries; entries must balance before posting.
2. **General Ledger:** automatically displays each account's journal activity and running balance.
3. **Trial Balance:** automatically calculates the debit/credit balances of every account as of a selected date.

Supporting functionality includes local login, account creation within the Journal screen, date filtering and CSV export. **No sales, inventory management, payroll, expiry, balance sheet, closing or income-statement screens.** Journal entries can cover sales, inventory, and expenses by selecting the corresponding accounts manually; there are no automated pharmacy inventory quantities.

**Important:** This is an educational demonstration system, not a production / BIR-certified accounting platform. Do not use real pharmacy client or patient information. All demo amounts are fictional examples, not official pharmacy receipts.

## If you already set up the FIRST PharmaLedger version

**Good news: the same existing XAMPP database (`pharma_ledger`) works.** This version uses the same four tables (`users`, `accounts`, `entries`, `lines`). Other unused tables from the earlier version remain untouched, and your existing journal transactions remain available.

1. Extract this ZIP into its **own new folder** named `PharmaLedger_JLT` (do **not** delete the previous folder).
2. Open the new `PharmaLedger_JLT` folder in **Antigravity IDE** using File → Open Folder.
3. Open Terminal → New Terminal. Check that the prompt is inside `PharmaLedger_JLT`.
4. Start **MySQL** in XAMPP Control Panel.
5. Install Python dependencies (one command at a time):

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

6. **Copy your working `.env` from the OLD project into this NEW folder** to preserve your database connection. If you have not made one yet, copy `.env.example` into `.env`, then change the secret and password yourself (details below). Never share `.env` publicly.
7. Run:

   ```powershell
   .\.venv\Scripts\python.exe manage.py check-db
   .\.venv\Scripts\python.exe manage.py init-db
   .\.venv\Scripts\python.exe app.py
   ```

8. Browse to **http://127.0.0.1:5000** and log in with the administrator account previously initialized. **If an admin user already existed, `init-db` does not reset that password:** use the same login credentials as the old app.

**Already imported `database.sql` in phpMyAdmin? No need to import it again.** `init-db` safely creates any missing core tables without deleting your data. **Do not run `seed-demo` on a database that has entries:** it will refuse to insert duplicates.

> If you prefer Command Prompt rather than PowerShell, the `.venv\Scripts\python.exe` commands still work. If `py` is not recognized but `python` works, run `python -m venv .venv` instead.

### Starting from scratch (without the previous app)

1. Install Python 3.11+ and XAMPP; start MySQL. If you use phpMyAdmin, start Apache too.
2. Import `database.sql` in phpMyAdmin (SQL tab) **or** SQLyog. This creates database `pharma_ledger`, not the tables.
3. In Antigravity, open the project folder and run the two Python setup commands above.
4. In terminal, run `Copy-Item .env.example .env` and edit `.env`:

   ```ini
   DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/pharma_ledger?charset=utf8mb4
   FLASK_SECRET_KEY=PUT_A_LONG_RANDOM_VALUE_HERE
   ADMIN_EMAIL=admin@pharmaledger.local
   INITIAL_ADMIN_PASSWORD=CHOOSE_AT_LEAST_10_CHARACTERS
   PORT=5000
   ```

   Default XAMPP root user has an empty password; if you configured one, update the DB URL. Generate a secret key with `py -c "import secrets; print(secrets.token_hex(32))"`. Save `.env`. Protect these values; do not use placeholder strings.
5. Run the commands:

   ```powershell
   .\.venv\Scripts\python.exe manage.py check-db
   .\.venv\Scripts\python.exe manage.py init-db
   .\.venv\Scripts\python.exe manage.py seed-demo
   .\.venv\Scripts\python.exe app.py
   ```

   **`seed-demo` is optional** and should only be run on an empty database. It loads one fictional opening capital entry and 10 fictional example pharmacy transactions. Otherwise, skip it.
6. Open `http://127.0.0.1:5000` in your browser.

**You do not need to place any files inside `C:\xampp\htdocs`.** Flask runs the website on port `5000`; XAMPP supplies MySQL only.

### How to use the three modules

**Journal:** Click **New journal entry**, pick a date and enter a description. Choose accounts and enter debits or credits; the totals must match. Example: cash medicine sale of ₱2,000 is Debit Cash ₱2,000, Credit Sales Revenue ₱2,000. Click **Post journal entry**. Posted journal entries are immutable in this demo; correct errors with a new reversing/correcting entry.

**General Ledger:** Choose account `1000 – Cash on Hand`, then click **View account**. Every debit and credit from journal entries that affected cash appears in chronological order, with running balance. Filter by date if needed.

**Trial Balance:** Open **Trial Balance** and choose an as-of date that is after your demo transactions (e.g. `2026-09-30`). The account balances are displayed on either the debit or credit side; both total columns should match. Click **Export CSV** to submit in a spreadsheet if needed.

**Database:** SQLyog and phpMyAdmin view the same database. Main tables are `users`, `accounts`, `entries` and `lines`. Leave existing other tables in place if migrating from the original project; deleting them would be destructive.

### Common issues

| Error | What to do |
|---|---|
| `py` not found | Try `python` instead or install Python 3.11+ |
| `No module named flask` | Run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| `Unknown database pharma_ledger` | Import `database.sql` through phpMyAdmin |
| `Can't connect to MySQL` | Start MySQL in XAMPP; verify `.env` password and port |
| `Access denied for user root` | Set the configured MySQL root password in DATABASE_URL |
| `User already exists / can't log in` | Use the **existing** administrator email/password; `init-db` does not reset it |
| Port 5000 already in use | Stop the old Python app (Ctrl+C) or set `PORT=5001` in `.env` |
| `seed-demo` says journal already contains entries | This is expected. Skip it; existing transactions are preserved |
| PowerShell activation error | Do not activate the environment; use `.\.venv\Scripts\python.exe` directly as instructed |

### Automated tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests run in their own temporary SQLite database and **do not** change your MySQL project data.

## Audit log

Admins get an **Audit Log** page in the sidebar (`/audit`). It records, with user, UTC time and IP address:

| Action | When |
| --- | --- |
| `login.success` / `login.failed` / `logout` | sign-in activity (failed attempts note whether the email exists) |
| `journal.posted` | every posted entry, including all lines and totals |
| `account.created` | new chart-of-accounts entries |
| `action.rejected` | input refused by validation (e.g. an unbalanced journal) |
| `export.csv` / `audit.exported` | any CSV download |
| `password.reset` | `reset_admin_password.py` was used |

Passwords are never logged. Each row stores the hash of the previous row, so editing or deleting a row is detected by **Verify integrity** on the page. The app has no edit/delete path for the log.

**Setup:** run `python manage.py init-db` once. It only creates the missing `audit_log` table and leaves existing data alone.

**Tests:** `python -m unittest discover tests`

**Hardening (recommended):** do not run the app as MySQL `root`. Create a dedicated user and limit it on the log table:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON pharma_ledger.* TO 'korena'@'localhost';
REVOKE UPDATE, DELETE ON pharma_ledger.audit_log FROM 'korena'@'localhost';
```
