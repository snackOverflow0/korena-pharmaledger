"""CLI: python manage.py check-db | init-db | seed-demo"""
import os
import sys
from sqlalchemy import text
from database import connect, initialize
from seed import seed_demo


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('check-db', 'init-db', 'seed-demo'):
        print('Usage: python manage.py [check-db | init-db | seed-demo]')
        return 2
    try:
        engine, sessions = connect()
        if sys.argv[1] == 'check-db':
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            print('SUCCESS: XAMPP database connection works.')
        elif sys.argv[1] == 'init-db':
            initialize(engine, sessions,
                       os.environ.get('ADMIN_EMAIL', 'admin@pharmaledger.local'),
                       os.environ.get('INITIAL_ADMIN_PASSWORD'))
            print('SUCCESS: Accounts/tables are ready. Existing journal data was preserved.')
        elif sys.argv[1] == 'seed-demo':
            with sessions.begin() as db:
                seed_demo(db)
            print('SUCCESS: Added 10 fictional pharmacy transactions and opening capital.')
    except Exception as ex:
        print('ERROR:', ex)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
