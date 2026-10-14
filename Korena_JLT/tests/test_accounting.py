"""Offline accounting integration tests; independent of Flask/MySQL."""
import os
import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models import Base, Account, Entry, Line, User
from accounting import (AccountingError, create_default_accounts, add_account, post_journal,
                        ledger_rows, trial_balance)
from seed import seed_demo

class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + self.tmp.name + '/testing.db')
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions.begin() as db:
            create_default_accounts(db)
            db.add(User(email='admin@test.local', password_hash='test-only', role='admin'))

    def tearDown(self):
        self.engine.dispose()
        self.tmp.cleanup()

    def test_valid_journal_creates_lines(self):
        with self.sessions.begin() as db:
            e=post_journal(db, posted_on=date(2026,9,7), reference='T001',
                           description='Cash sales', lines=[('1000','2300','0'),('4000','0','2300')], user_id=1)
            self.assertEqual(e.reference,'T001')
        with self.sessions() as db:
            e=db.scalar(select(Entry).where(Entry.reference=='T001'))
            self.assertEqual(len(e.lines),2)
            self.assertEqual(sum((l.debit for l in e.lines),Decimal('0')),Decimal('2300.00'))

    def test_unbalanced_entry_rejected_without_writes(self):
        with self.assertRaisesRegex(AccountingError,'not balanced'):
            with self.sessions.begin() as db:
                post_journal(db,posted_on=date(2026,9,7),reference='T002',description='Wrong entry',
                             lines=[('1000','2000','0'),('4000','0','1999')])
        with self.sessions() as db:
            self.assertEqual(db.scalar(select(func.count(Entry.id))),0)

    def test_double_sided_row_rejected(self):
        with self.assertRaisesRegex(AccountingError,'not both'):
            with self.sessions.begin() as db:
                post_journal(db,posted_on=date(2026,9,7),reference='T003',description='Invalid line',
                             lines=[('1000','100','100'),('4000','0','100')])

    def test_invalid_precision_rejected(self):
        with self.assertRaisesRegex(AccountingError,'two decimal'):
            with self.sessions.begin() as db:
                post_journal(db,posted_on=date(2026,9,7),reference='T004',description='Invalid amount',
                             lines=[('1000','23.999','0'),('4000','0','23.999')])

    def test_duplicate_reference_rejected(self):
        with self.sessions.begin() as db:
            post_journal(db,posted_on=date(2026,9,7),reference='T005',description='First entry',
                         lines=[('1000','50','0'),('4000','0','50')])
        with self.assertRaisesRegex(AccountingError,'already exists'):
            with self.sessions.begin() as db:
                post_journal(db,posted_on=date(2026,9,8),reference='T005',description='Second entry',
                             lines=[('1000','60','0'),('4000','0','60')])
        with self.sessions() as db:
            self.assertEqual(db.scalar(select(func.count(Entry.id))),1)

    def test_ledger_opening_period_and_running(self):
        with self.sessions.begin() as db:
            for ref, raw_day, val, debit in [('A','2026-09-01','1000',True),('B','2026-09-10','200',False),('C','2026-10-01','400',True)]:
                post_journal(db,posted_on=date.fromisoformat(raw_day),reference=ref,description='Sample entry',
                             lines=[('1000',val if debit else '0','0' if debit else val),
                                    ('3000','0' if debit else val,val if debit else '0')])
        with self.sessions() as db:
            a=db.scalar(select(Account).where(Account.code=='1000'))
            opening,rows,ending=ledger_rows(db,a,start=date(2026,9,5),end=date(2026,9,30))
            self.assertEqual(opening,Decimal('1000.00'))
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['balance'],Decimal('800.00'))
            self.assertEqual(ending,Decimal('800.00'))
            self.assertEqual(ledger_rows(db,a,end=date(2026,10,1))[2],Decimal('1200.00'))

    def test_trial_balance_asof(self):
        with self.sessions.begin() as db:
            post_journal(db, posted_on=date(2026,9,9),reference='X',description='Cash equity',
                         lines=[('1000','1000','0'),('3000','0','1000')])
            post_journal(db, posted_on=date(2026,10,2),reference='Y',description='Cash sales',
                         lines=[('1000','500','0'),('4000','0','500')])
        with self.sessions() as db:
            sep,dr,cr=trial_balance(db,date(2026,9,30))
            self.assertEqual((dr,cr),(Decimal('1000.00'),Decimal('1000.00')))
            octo,dr2,cr2=trial_balance(db,date(2026,10,10))
            self.assertEqual((dr2,cr2),(Decimal('1500.00'),Decimal('1500.00')))

    def test_demo_seeds_10_plus_opening_and_balances(self):
        with self.sessions.begin() as db:
            seed_demo(db)
        with self.sessions() as db:
            self.assertEqual(db.scalar(select(func.count(Entry.id))),11)
            rows,dr,cr=trial_balance(db,date(2026,9,30))
            self.assertEqual(dr,cr)
            self.assertEqual(dr,Decimal('129250.00'))
            values={r['account'].code:r['signed'] for r in rows}
            self.assertEqual(values['1000'],Decimal('83050.00'))
            self.assertEqual(values['2000'],Decimal('-7000.00'))
        with self.assertRaisesRegex(ValueError,'already has journal entries'):
            with self.sessions.begin() as db:
                seed_demo(db)

    def test_custom_account(self):
        with self.sessions.begin() as db:
            add_account(db,'5600','Transportation Expense','expense')
        with self.sessions() as db:
            self.assertIsNotNone(db.scalar(select(Account).where(Account.code=='5600')))

    def test_original_schema_columns(self):
        # The four original tables remain intact; the audit_log table is added without changing them.
        self.assertEqual(set(Base.metadata.tables),{'users','accounts','entries','lines','audit_log'})
        self.assertEqual({c.name for c in Entry.__table__.columns},
            {'id','posted_on','reference','description','kind','created_by','created_at'})
        self.assertEqual({c.name for c in Line.__table__.columns},
            {'id','entry_id','account_id','debit','credit'})

if __name__=='__main__': unittest.main()
