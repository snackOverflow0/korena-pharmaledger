"""Journal, ledger and trial balance: simplified PharmaLedger Flask app."""
import csv
import json
import os
import secrets
import sys
from pathlib import Path
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from functools import wraps
from io import StringIO
from flask import Flask, Response, abort, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
from database import connect
from models import Account, AuditLog, Entry, Line, User
from audit import ACTIONS, commit_record, record, verify_chain
from accounting import AccountingError, ACCOUNT_TYPES, add_account, ledger_rows, money, post_journal, trial_balance


def create_app(test_config=None):
    resources = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    app = Flask(__name__, template_folder=str(resources / "templates"),
                static_folder=str(resources / "static"))
    app.config.update(SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', 'CHANGE_ME_IN_ENV'),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                      MAX_CONTENT_LENGTH=64*1024)
    if os.environ.get('KORENA_PUBLIC_SERVER') == '1':
        key = app.config['SECRET_KEY']
        if not key or key == 'CHANGE_ME_IN_ENV' or len(key) < 32:
            raise RuntimeError('Set a strong FLASK_SECRET_KEY (32+ characters) before hosting PharmaLedger.')
        app.config.update(SESSION_COOKIE_SECURE=os.environ.get('KORENA_HTTPS', '1') == '1')
    if test_config:
        app.config.update(test_config)
    engine, Sessions = connect(app.config.get('DATABASE_URL'))
    app.extensions['db_engine'] = engine
    app.extensions['db_sessions'] = Sessions

    @app.before_request
    def open_db():
        g.db = Sessions()
        g.user = g.db.get(User, session.get('uid')) if session.get('uid') else None
        if request.method == 'POST':
            token = session.get('_csrf')
            supplied = request.form.get('_csrf')
            if not token or not supplied or not secrets.compare_digest(token, supplied):
                abort(400, 'Form security token missing. Refresh the page and try again.')

    @app.teardown_request
    def close_db(error):
        db = getattr(g, 'db', None)
        if db:
            if error:
                db.rollback()
            db.close()

    @app.context_processor
    def inject():
        if '_csrf' not in session:
            session['_csrf'] = secrets.token_urlsafe(32)
        return dict(me=getattr(g, 'user', None), csrf=session['_csrf'], today=date.today(),
                    moneyfmt=lambda x: f'₱{money(x):,.2f}', account_types=ACCOUNT_TYPES)

    def login_required(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not g.user:
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapped

    def admin_only(fn):
        @wraps(fn)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user.role != 'admin':
                abort(403)
            return fn(*args, **kwargs)
        return wrapped

    def parse_date(raw, field='date'):
        try:
            return date.fromisoformat(raw)
        except (ValueError, TypeError):
            raise AccountingError(f'Invalid {field}. Use YYYY-MM-DD.')

    @app.errorhandler(AccountingError)
    @app.errorhandler(IntegrityError)
    def handle_accounting_error(error):
        g.db.rollback()
        message = str(error) if isinstance(error, AccountingError) else 'A duplicate value or invalid database record was submitted.'
        if getattr(g, 'user', None):
            try:
                commit_record(g.db, 'action.rejected', f'Rejected {request.method} {request.path}: {message}',
                              user=g.user, details={'endpoint': request.endpoint, 'message': message})
            except Exception:  # auditing must never turn a validation message into a crash
                g.db.rollback()
        flash(message, 'error')
        return redirect(request.referrer if request.referrer and request.referrer.startswith(request.host_url) else url_for('journals'))

    @app.get('/health')
    def health():
        return {'status': 'ok', 'modules': ['journal', 'ledger', 'trial_balance', 'audit_log']}

    @app.get('/')
    def home():
        return redirect(url_for('journals'))

    @app.get('/login')
    def login():
        if g.user:
            return redirect(url_for('journals'))
        return render_template('login.html')

    @app.post('/login')
    def do_login():
        email = request.form.get('email', '').strip().lower()
        user = g.db.scalar(select(User).where(User.email == email))
        if not user or not check_password_hash(user.password_hash, request.form.get('password', '')):
            commit_record(g.db, 'login.failed', f'Failed login for {email[:100] or "(blank email)"}',
                          user_id=user.id if user else None, user_email=email or None,
                          details={'reason': 'unknown_email' if not user else 'wrong_password'})
            flash('Incorrect email or password.', 'error')
            return redirect(url_for('login'))
        commit_record(g.db, 'login.success', f'{user.email} signed in', user=user)
        session.clear()
        session['uid'] = user.id
        session['_csrf'] = secrets.token_urlsafe(32)
        return redirect(url_for('journals'))

    @app.post('/logout')
    @login_required
    def logout():
        commit_record(g.db, 'logout', f'{g.user.email} signed out', user=g.user)
        session.clear()
        return redirect(url_for('login'))

    @app.get('/journal')
    @login_required
    def journals():
        raw_start, raw_end = request.args.get('start', ''), request.args.get('end', '')
        start = parse_date(raw_start, 'start date') if raw_start else None
        end = parse_date(raw_end, 'end date') if raw_end else None
        if start and end and start > end:
            raise AccountingError('Start date cannot come after end date.')
        stmt = select(Entry).order_by(Entry.posted_on.desc(), Entry.id.desc())
        if start:
            stmt = stmt.where(Entry.posted_on >= start)
        if end:
            stmt = stmt.where(Entry.posted_on <= end)
        entries = list(g.db.scalars(stmt.limit(500)))
        total_entries = g.db.query(Entry).count()
        return render_template('journal.html', entries=entries, total_entries=total_entries,
                               start=raw_start, end=raw_end)

    @app.route('/journal/new', methods=['GET', 'POST'])
    @login_required
    def new_journal():
        if request.method == 'POST':
            codes = request.form.getlist('code')
            debits = request.form.getlist('debit')
            credits = request.form.getlist('credit')
            if not (len(codes) == len(debits) == len(credits)):
                raise AccountingError('Invalid journal row data.')
            pairs = []
            for code, debit, credit in zip(codes, debits, credits):
                if not (code.strip() or debit.strip() or credit.strip()):
                    continue
                if not code.strip():
                    raise AccountingError('Choose an account for every row containing an amount.')
                pairs.append((code, debit, credit))
            ref = request.form.get('reference', '').strip() or ('JRN-' + uuid.uuid4().hex[:10].upper())
            entry = post_journal(g.db,
                                 posted_on=parse_date(request.form.get('posted_on'), 'posting date'),
                                 reference=ref,
                                 description=request.form.get('description', ''),
                                 lines=pairs, user_id=g.user.id)
            posted = [(ln.account.code, str(ln.debit), str(ln.credit)) for ln in entry.lines]
            record(g.db, 'journal.posted', f'Posted journal {entry.reference}', user=g.user,
                   entity_type='entry', entity_id=entry.id,
                   details={'reference': entry.reference, 'posted_on': entry.posted_on,
                            'description': entry.description,
                            'lines': [{'account': c, 'debit': d, 'credit': cr} for c, d, cr in posted],
                            'total': str(sum((ln.debit for ln in entry.lines), Decimal('0.00')))})
            g.db.commit()
            flash(f'Journal {entry.reference} was posted. The ledger and trial balance have updated automatically.', 'success')
            return redirect(url_for('entry_detail', entry_id=entry.id))
        accounts = list(g.db.scalars(select(Account).where(Account.active.is_(True)).order_by(Account.code)))
        return render_template('new_journal.html', accounts=accounts)

    @app.get('/journal/<int:entry_id>')
    @login_required
    def entry_detail(entry_id):
        entry = g.db.get(Entry, entry_id)
        if not entry:
            abort(404)
        return render_template('entry.html', entry=entry)

    @app.post('/journal/accounts')
    @admin_only
    def create_account():
        account = add_account(g.db, request.form.get('code', ''),
                              request.form.get('name', ''), request.form.get('category', ''))
        record(g.db, 'account.created', f'Created account {account.code} {account.name}', user=g.user,
               entity_type='account', entity_id=account.id,
               details={'code': account.code, 'name': account.name, 'category': account.category})
        g.db.commit()
        flash('Account created. It is now available in the journal account list.', 'success')
        return redirect(url_for('new_journal'))

    @app.get('/ledger')
    @login_required
    def ledger():
        accounts = list(g.db.scalars(select(Account).order_by(Account.code)))
        code = request.args.get('code', '').strip() or (accounts[0].code if accounts else '')
        account = next((acc for acc in accounts if acc.code == code), None)
        if not account:
            abort(404)
        raw_start, raw_end = request.args.get('start', ''), request.args.get('end', '')
        start = parse_date(raw_start, 'start date') if raw_start else None
        end = parse_date(raw_end, 'end date') if raw_end else None
        if start and end and start > end:
            raise AccountingError('Start date cannot come after end date.')
        opening, rows, closing = ledger_rows(g.db, account, start=start, end=end)
        debits = sum((r['line'].debit for r in rows), Decimal('0.00'))
        credits = sum((r['line'].credit for r in rows), Decimal('0.00'))
        return render_template('ledger.html', accounts=accounts, account=account,
                               rows=rows, opening=opening, closing=closing, debits=debits, credits=credits,
                               start=raw_start, end=raw_end)

    @app.get('/trial-balance')
    @login_required
    def trial():
        latest = g.db.scalar(select(Entry.posted_on).order_by(Entry.posted_on.desc()).limit(1)) or date.today()
        selected_date = parse_date(request.args.get('as_of', latest.isoformat()), 'as-of date')
        rows, total_debits, total_credits = trial_balance(g.db, selected_date)
        show_all = request.args.get('show_all') == '1'
        if not show_all:
            rows = [r for r in rows if r['debit'] or r['credit']]
        return render_template('trial.html', as_of=selected_date, rows=rows,
                               total_debits=total_debits, total_credits=total_credits,
                               balanced=(total_debits == total_credits), show_all=show_all)

    @app.get('/export/<report>.csv')
    @login_required
    def export(report):
        output = StringIO()
        writer = csv.writer(output)
        if report == 'journal':
            writer.writerow(['Date', 'Reference', 'Description', 'Account code', 'Account', 'Debit PHP', 'Credit PHP'])
            query = (select(Entry, Line, Account).join(Line, Line.entry_id == Entry.id)
                     .join(Account, Line.account_id == Account.id)
                     .order_by(Entry.posted_on, Entry.id, Line.id))
            for e, ln, a in g.db.execute(query):
                writer.writerow([e.posted_on, e.reference, e.description, a.code, a.name, ln.debit, ln.credit])
        elif report == 'trial':
            latest = g.db.scalar(select(Entry.posted_on).order_by(Entry.posted_on.desc()).limit(1)) or date.today()
            as_of = parse_date(request.args.get('as_of', latest.isoformat()), 'as-of date')
            writer.writerow(['Trial Balance as of', as_of.isoformat()])
            writer.writerow(['Code', 'Account', 'Debit PHP', 'Credit PHP'])
            rows, debits, credits = trial_balance(g.db, as_of)
            for r in rows:
                if r['debit'] or r['credit']:
                    writer.writerow([r['account'].code, r['account'].name, r['debit'], r['credit']])
            writer.writerow(['', 'TOTAL', debits, credits])
        elif report == 'ledger':
            code = request.args.get('code', '')
            account = g.db.scalar(select(Account).where(Account.code == code))
            if not account:
                abort(404)
            start = parse_date(request.args['start']) if request.args.get('start') else None
            end = parse_date(request.args['end']) if request.args.get('end') else None
            if start and end and start > end:
                raise AccountingError('Start date cannot come after end date.')
            opening, rows, closing = ledger_rows(g.db, account, start, end)
            writer.writerow([f'General Ledger - {account.code} {account.name}'])
            writer.writerow(['', '', 'Opening balance (Debit - Credit)', '', '', opening])
            writer.writerow(['Date', 'Reference', 'Description', 'Debit PHP', 'Credit PHP', 'Running balance'])
            for r in rows:
                writer.writerow([r['entry'].posted_on, r['entry'].reference, r['entry'].description,
                                 r['line'].debit, r['line'].credit, r['balance']])
            writer.writerow(['', '', 'Closing balance', '', '', closing])
        else:
            abort(404)
        commit_record(g.db, 'export.csv', f'Exported {report} CSV', user=g.user,
                      details={'report': report, 'filters': request.args.to_dict()})
        return Response('\ufeff' + output.getvalue(), content_type='text/csv; charset=utf-8',
                        headers={'Content-Disposition': f'attachment; filename="Korena_{report}.csv"'})

    # ---- Audit log (admin only) ------------------------------------------------
    AUDIT_PAGE_SIZE = 50

    def audit_filters():
        action = request.args.get('action', '').strip()
        who = request.args.get('user', '').strip()
        raw_start, raw_end = request.args.get('start', ''), request.args.get('end', '')
        start = parse_date(raw_start, 'start date') if raw_start else None
        end = parse_date(raw_end, 'end date') if raw_end else None
        if start and end and start > end:
            raise AccountingError('Start date cannot come after end date.')
        stmt = select(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if who:
            stmt = stmt.where(AuditLog.user_email.contains(who, autoescape=True))
        if start:
            stmt = stmt.where(AuditLog.created_at >= datetime.combine(start, time.min))
        if end:
            stmt = stmt.where(AuditLog.created_at < datetime.combine(end + timedelta(days=1), time.min))
        return stmt, dict(action=action, user=who, start=raw_start, end=raw_end)

    @app.template_filter('prettyjson')
    def prettyjson(value):
        try:
            return json.dumps(json.loads(value), indent=2, sort_keys=True, ensure_ascii=False)
        except (TypeError, ValueError):
            return value or ''

    @app.get('/audit')
    @admin_only
    def audit_log():
        stmt, filters = audit_filters()
        total = g.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        pages = max((total + AUDIT_PAGE_SIZE - 1) // AUDIT_PAGE_SIZE, 1)
        page = min(max(request.args.get('page', 1, type=int), 1), pages)
        rows = list(g.db.scalars(stmt.order_by(AuditLog.id.desc())
                                 .limit(AUDIT_PAGE_SIZE).offset((page - 1) * AUDIT_PAGE_SIZE)))
        chain = verify_chain(g.db) if request.args.get('verify') == '1' else None
        keep = {k: v for k, v in filters.items() if v}
        return render_template('audit.html', rows=rows, total=total, page=page, pages=pages,
                               actions=ACTIONS, chain=chain, keep=keep, **filters)

    @app.get('/audit/export.csv')
    @admin_only
    def audit_export():
        stmt, filters = audit_filters()
        def safe(value):  # neutralise spreadsheet formula injection from user-typed values
            text = '' if value is None else str(value)
            return "'" + text if text[:1] in ('=', '+', '-', '@', '\t', '\r') else text
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Time (UTC)', 'User', 'Action', 'Entity', 'Entity ID', 'Summary', 'IP', 'Details'])
        for r in g.db.scalars(stmt.order_by(AuditLog.id).limit(50000)):
            writer.writerow([r.id, r.created_at.isoformat(sep=' '), safe(r.user_email), r.action,
                             r.entity_type or '', r.entity_id or '', safe(r.summary), r.ip_address or '',
                             safe(r.details)])
        commit_record(g.db, 'audit.exported', 'Exported audit log CSV', user=g.user,
                      details={'filters': {k: v for k, v in filters.items() if v}})
        return Response('\ufeff' + output.getvalue(), content_type='text/csv; charset=utf-8',
                        headers={'Content-Disposition': 'attachment; filename="Korena_audit_log.csv"'})

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.environ.get('PORT', '5000')), debug=False)
