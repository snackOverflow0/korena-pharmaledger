"""Local account recovery for Korena (Journal / Ledger / Trial Balance).

Place this file next to app.py, database.py and models.py. This script updates
only the selected administrator's password hash. It does not delete or edit any
accounting records. Run only on a computer whose database you administer.
"""

from getpass import getpass
import sys

from sqlalchemy import select
from werkzeug.security import generate_password_hash

from audit import record
from database import connect
from models import User


def main():
    print("\nKORENA — Administrator password reset\n")
    print("This updates the password of an existing Korena admin account.")
    print("No accounting entries, accounts, or balances will be changed.\n")

    engine, Session = connect()  # Reads DATABASE_URL from the project's .env
    try:
        with Session.begin() as db:
            admins = list(db.scalars(select(User).where(User.role == "admin").order_by(User.id)))
            if not admins:
                print("No administrator account was found in this database.")
                print("Check DATABASE_URL in .env; for a fresh empty database run:")
                print(r"  .\.venv\Scripts\python.exe manage.py init-db")
                return 1

            print("Existing administrator email(s):")
            for number, admin in enumerate(admins, start=1):
                print(f"  {number}. {admin.email}")

            if len(admins) == 1:
                selected = admins[0]
            else:
                selection = input("Choose an account number to reset: ").strip()
                if not selection.isdigit() or not 1 <= int(selection) <= len(admins):
                    print("Invalid selection; no changes were made.")
                    return 1
                selected = admins[int(selection) - 1]

            print(f"\nResetting password for: {selected.email}")
            password = getpass("New password (at least 10 characters): ")
            if len(password) < 10:
                print("Password must have at least 10 characters. No changes were made.")
                return 1
            confirmation = getpass("Confirm new password: ")
            if password != confirmation:
                print("Passwords did not match. No changes were made.")
                return 1

            selected.password_hash = generate_password_hash(password)
            db.flush()
            try:  # audit trail; skipped (not fatal) if audit_log table has not been created yet
                with db.begin_nested():
                    record(db, 'password.reset', f'Password reset from command line for {selected.email}',
                           user=selected, details={'method': 'reset_admin_password.py'})
            except Exception:
                print("Note: audit entry not written (run manage.py init-db to create the audit_log table).")
            email = selected.email

        print("\nPassword changed successfully!")
        print(f"Use this email to sign in to Korena: {email}")
        print("Use the NEW password you just entered.")
        print("You do not need to rerun setup or seed-demo.")
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCanceled. No changes were made.")
        sys.exit(1)
    except Exception as error:
        print(f"\nCould not reset the account: {error}")
        print("Check that XAMPP MySQL is running and .env points to the correct database.")
        sys.exit(1)
