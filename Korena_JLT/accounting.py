"""Journal → ledger → trial balance. Money and balances use Decimal."""
from datetime import date
from decimal import Decimal, InvalidOperation
from sqlalchemy import select, func
from models import Account, Entry, Line

ZERO = Decimal('0.00')
CENT = Decimal('0.01')
ACCOUNT_TYPES = ('asset', 'liability', 'equity', 'revenue', 'expense')
DEFAULT_ACCOUNTS = [
    ('1000', 'Cash on Hand', 'asset'),
    ('1100', 'Medicine Inventory', 'asset'),
    ('1200', 'Accounts Receivable', 'asset'),
    ('2000', 'Accounts Payable', 'liability'),
    ('3000', 'Owner Capital', 'equity'),
    ('3100', 'Retained Earnings', 'equity'),
    ('4000', 'Sales Revenue', 'revenue'),
    ('4100', 'Other Income', 'revenue'),
    ('5000', 'Cost of Goods Sold', 'expense'),
    ('5100', 'Utilities Expense', 'expense'),
    ('5200', 'Wages Expense', 'expense'),
    ('5300', 'Rent Expense', 'expense'),
    ('5400', 'Other Operating Expense', 'expense'),
    ('5500', 'Damaged/Expired Inventory Loss', 'expense'),
]

class AccountingError(ValueError):
    pass

def money(value):
    try:
        number = Decimal(str(value).strip())
        if not number.is_finite() or number.as_tuple().exponent < -2:
            raise InvalidOperation()
        if abs(number) > Decimal('9999999999999.99'):
            raise InvalidOperation()
        return number.quantize(CENT)
    except (ValueError, TypeError, InvalidOperation):
        raise AccountingError('Use a valid peso amount with at most two decimal places.')

def create_default_accounts(db):
    present = set(db.scalars(select(Account.code)).all())
    for code, name, category in DEFAULT_ACCOUNTS:
        if code not in present:
            db.add(Account(code=code, name=name, category=category, active=True))
    db.flush()

def add_account(db, code, name, category):
    code, name, category = code.strip(), name.strip(), category.strip().lower()
    if not code.isdigit() or not (3 <= len(code) <= 10):
        raise AccountingError('Account code must be 3–10 digits.')
    if not (2 <= len(name) <= 120):
        raise AccountingError('Account name must have 2–120 characters.')
    if category not in ACCOUNT_TYPES:
        raise AccountingError('Choose a valid account type.')
    if db.scalar(select(Account.id).where(Account.code == code)):
        raise AccountingError('Account code already exists.')
    account = Account(code=code, name=name, category=category, active=True)
    db.add(account)
    db.flush()
    return account

def post_journal(db, *, posted_on, reference, description, lines, user_id=None):
    """Validate then stage one atomic balanced entry; caller commits or rolls back."""
    if not isinstance(posted_on, date):
        raise AccountingError('Choose a valid journal date.')
    reference = reference.strip()
    description = description.strip()
    if not (1 <= len(reference) <= 80):
        raise AccountingError('Reference must have 1–80 characters.')
    if not (3 <= len(description) <= 255):
        raise AccountingError('Description must have 3–255 characters.')
    if db.scalar(select(Entry.id).where(Entry.reference == reference)):
        raise AccountingError('This reference already exists.')
    if not 2 <= len(lines) <= 25:
        raise AccountingError('Enter between 2 and 25 journal lines.')
    codes = set(str(item[0]).strip() for item in lines)
    accounts = {a.code: a for a in db.scalars(select(Account).where(Account.code.in_(codes), Account.active.is_(True)))}
    prepared = []
    dr_total = ZERO
    cr_total = ZERO
    for code, debit, credit in lines:
        code = str(code).strip()
        if code not in accounts:
            raise AccountingError('Unknown or inactive account: ' + code)
        dr, cr = money(debit or '0'), money(credit or '0')
        if dr < 0 or cr < 0 or (dr > 0 and cr > 0) or (dr == 0 and cr == 0):
            raise AccountingError('Each row must contain a positive debit OR a positive credit, not both.')
        prepared.append((accounts[code], dr, cr))
        dr_total += dr
        cr_total += cr
    if dr_total != cr_total or dr_total <= 0:
        raise AccountingError(f'Journal not balanced. Debit ₱{dr_total:,.2f}; Credit ₱{cr_total:,.2f}.')
    entry = Entry(posted_on=posted_on, reference=reference, description=description, kind='general', created_by=user_id)
    db.add(entry)
    db.flush()
    for account, debit, credit in prepared:
        db.add(Line(entry_id=entry.id, account_id=account.id, debit=debit, credit=credit))
    db.flush()
    return entry

def ledger_rows(db, account, start=None, end=None):
    """Ledger from journal lines. Opening includes transactions before start."""
    stmt = (select(Entry, Line).join(Line, Line.entry_id == Entry.id)
            .where(Line.account_id == account.id)
            .order_by(Entry.posted_on, Entry.id, Line.id))
    opening = ZERO
    balance = ZERO
    rows = []
    for entry, line in db.execute(stmt):
        delta = money(line.debit) - money(line.credit)
        if start and entry.posted_on < start:
            opening += delta
        elif not end or entry.posted_on <= end:
            balance += delta
            rows.append({'entry': entry, 'line': line, 'balance': opening + balance})
    return opening, rows, opening + balance

def trial_balance(db, as_of):
    stmt = (select(Account.id, func.coalesce(func.sum(Line.debit - Line.credit), 0))
            .join(Line, Account.id == Line.account_id)
            .join(Entry, Line.entry_id == Entry.id)
            .where(Entry.posted_on <= as_of)
            .group_by(Account.id))
    values = {accid: money(balance) for accid, balance in db.execute(stmt)}
    result = []
    for a in db.scalars(select(Account).order_by(Account.code)):
        b = values.get(a.id, ZERO)
        result.append({'account': a, 'debit': max(b, ZERO), 'credit': max(-b, ZERO), 'signed': b})
    dr = sum((r['debit'] for r in result), ZERO)
    cr = sum((r['credit'] for r in result), ZERO)
    return result, dr, cr
