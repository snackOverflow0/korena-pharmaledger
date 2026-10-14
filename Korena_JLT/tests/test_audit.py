"""Audit-log tests. Run from the project folder:  python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import select, text
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from audit import AuditError, record, verify_chain
from database import initialize
from models import AuditLog, Entry, User

ADMIN, STAFF, PW = 'admin@test.local', 'staff@test.local', 'correct-horse-123'


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.app = create_app({'DATABASE_URL': f'sqlite:///{self.tmp.name}/audit.db',
                               'TESTING': True, 'SECRET_KEY': 'test'})
        self.engine = self.app.extensions['db_engine']
        self.Sessions = self.app.extensions['db_sessions']
        initialize(self.engine, self.Sessions, ADMIN, PW)
        with self.Sessions.begin() as db:
            db.add(User(email=STAFF, password_hash=generate_password_hash(PW), role='staff'))
        self.client = self.app.test_client()

    def tearDown(self):
        self.engine.dispose()
        self.tmp.cleanup()

    # helpers
    def csrf(self):
        with self.client.session_transaction() as sess:
            sess.setdefault('_csrf', 'tok')
            return sess['_csrf']

    def login(self, email=ADMIN, password=PW):
        return self.client.post('/login', data={'email': email, 'password': password, '_csrf': self.csrf()})

    def logs(self, action=None):
        with self.Sessions() as db:
            stmt = select(AuditLog).order_by(AuditLog.id)
            if action:
                stmt = stmt.where(AuditLog.action == action)
            return list(db.scalars(stmt))

    def post_journal(self, debit='100', credit='100', ref='T-1'):
        return self.client.post('/journal/new', data={
            '_csrf': self.csrf(), 'posted_on': '2026-09-01', 'reference': ref,
            'description': 'Cash sale', 'code': ['1000', '4000'],
            'debit': [debit, '0'], 'credit': ['0', credit]})

    # tests
    def test_login_success_and_failure_are_logged(self):
        self.login(ADMIN, 'wrong-password')
        self.login('nobody@test.local', 'x')
        self.login()
        self.assertEqual([r.action for r in self.logs()], ['login.failed', 'login.failed', 'login.success'])
        failed = self.logs('login.failed')
        self.assertEqual(failed[0].user_email, ADMIN)
        self.assertIn('wrong_password', failed[0].details)
        self.assertIn('unknown_email', failed[1].details)
        self.assertNotIn('wrong-password', ''.join(r.details or '' for r in self.logs()))

    def test_journal_posting_is_logged_with_lines(self):
        self.login()
        self.post_journal()
        rows = self.logs('journal.posted')
        self.assertEqual(len(rows), 1)
        with self.Sessions() as db:
            entry = db.scalar(select(Entry).where(Entry.reference == 'T-1'))
        self.assertEqual(rows[0].entity_id, entry.id)
        self.assertIn('"1000"', rows[0].details)
        self.assertEqual(rows[0].user_email, ADMIN)

    def test_rejected_journal_is_logged_and_writes_nothing(self):
        self.login()
        self.post_journal(debit='100', credit='90', ref='BAD-1')
        with self.Sessions() as db:
            self.assertIsNone(db.scalar(select(Entry).where(Entry.reference == 'BAD-1')))
        self.assertEqual(len(self.logs('action.rejected')), 1)
        self.assertEqual(len(self.logs('journal.posted')), 0)

    def test_chain_verifies_then_detects_tampering(self):
        self.login()
        self.post_journal()
        with self.Sessions() as db:
            ok, count, bad = verify_chain(db)
        self.assertTrue(ok)
        self.assertGreaterEqual(count, 2)
        with self.engine.begin() as conn:  # simulate someone editing the table directly
            conn.execute(text("UPDATE audit_log SET summary = 'edited' WHERE id = 1"))
        with self.Sessions() as db:
            ok, _, bad = verify_chain(db)
        self.assertFalse(ok)
        self.assertEqual(bad, 1)

    def test_deleting_a_row_breaks_the_chain(self):
        self.login()
        self.post_journal()
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM audit_log WHERE id = 2"))
        with self.Sessions() as db:
            ok, _, _ = verify_chain(db)
        self.assertFalse(ok)

    def test_orm_cannot_update_or_delete_audit_rows(self):
        with self.Sessions() as db:
            record(db, 'logout', 'x', user_email='a@b.c')
            db.commit()
            row = db.scalar(select(AuditLog))
            row.summary = 'changed'
            with self.assertRaises(AuditError):
                db.commit()
            db.rollback()
            db.delete(db.scalar(select(AuditLog)))
            with self.assertRaises(AuditError):
                db.commit()

    def test_only_admin_can_view_audit_log(self):
        self.assertEqual(self.client.get('/audit').status_code, 302)  # not logged in
        self.login(STAFF)
        self.assertEqual(self.client.get('/audit').status_code, 403)
        self.assertEqual(self.client.get('/audit/export.csv').status_code, 403)
        self.client.post('/logout', data={'_csrf': self.csrf()})
        self.login()
        page = self.client.get('/audit?verify=1')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Integrity check passed', page.data)

    def test_csv_export_neutralises_formulas_and_is_logged(self):
        self.login('=HYPERLINK("http://evil")', 'x')  # failed login with a formula as the "email"
        self.login()
        resp = self.client.get('/audit/export.csv')
        self.assertEqual(resp.status_code, 200)
        body = resp.data.decode('utf-8')
        self.assertIn("'=hyperlink", body.lower())
        self.assertNotIn(',=hyperlink', body.lower())
        self.assertEqual(len(self.logs('audit.exported')), 1)


if __name__ == '__main__':
    unittest.main()
