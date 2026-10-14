"""Audit trail: append-only, hash-chained log of security and accounting events.

record() only *stages* a row in the caller's session, so the audit row is committed
in the SAME transaction as the action it describes (no action without a log, no log
without an action). For events with no business transaction (failed login, rejected
input) call commit_record(), which commits by itself.
"""
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal

from flask import has_request_context, request
from sqlalchemy import event, select

from models import AuditLog

GENESIS = '0' * 64

# Action names used by the app (also used for the filter drop-down on /audit).
ACTIONS = (
    'login.success', 'login.failed', 'logout',
    'journal.posted', 'account.created', 'action.rejected',
    'export.csv', 'audit.exported', 'password.reset',
)


class AuditError(RuntimeError):
    pass


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def _digest(prev_hash, created_at, user_id, user_email, action,
            entity_type, entity_id, summary, details):
    payload = json.dumps([prev_hash, created_at.isoformat(), user_id, user_email, action,
                          entity_type, entity_id, summary, details],
                         separators=(',', ':'), sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _client_ip():
    if has_request_context():
        return (request.remote_addr or '')[:45] or None
    return 'cli'


def record(db, action, summary, *, user=None, user_id=None, user_email=None,
           entity_type=None, entity_id=None, details=None, ip=None):
    """Stage one audit row in `db`. The caller commits."""
    if user is not None:
        user_id, user_email = user.id, user.email
    created_at = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    details_json = (json.dumps(details, sort_keys=True, default=_json_default, ensure_ascii=True)
                    if details is not None else None)
    summary = (summary or '')[:255]
    user_email = user_email[:160] if user_email else None

    # autoflush keeps the chain correct if two rows are staged in one transaction.
    last = db.scalar(select(AuditLog.row_hash).order_by(AuditLog.id.desc()).limit(1))
    prev_hash = last or GENESIS
    row = AuditLog(created_at=created_at, user_id=user_id, user_email=user_email,
                   action=action, entity_type=entity_type, entity_id=entity_id,
                   summary=summary, details=details_json,
                   ip_address=ip or _client_ip(), prev_hash=prev_hash,
                   row_hash=_digest(prev_hash, created_at, user_id, user_email, action,
                                    entity_type, entity_id, summary, details_json))
    db.add(row)
    db.flush()
    return row


def commit_record(db, action, summary, **kwargs):
    """Record and commit immediately (for events without a business transaction)."""
    row = record(db, action, summary, **kwargs)
    db.commit()
    return row


def verify_chain(db):
    """Recompute every hash in order. Returns (ok, rows_checked, first_bad_id)."""
    prev, count = GENESIS, 0
    for r in db.scalars(select(AuditLog).order_by(AuditLog.id)):
        count += 1
        expected = _digest(prev, r.created_at, r.user_id, r.user_email, r.action,
                           r.entity_type, r.entity_id, r.summary, r.details)
        if r.prev_hash != prev or r.row_hash != expected:
            return False, count, r.id
        prev = r.row_hash
    return True, count, None


# ORM-level guard: audit rows can be inserted but never changed or deleted by the app.
@event.listens_for(AuditLog, 'before_update')
def _block_update(mapper, connection, target):
    raise AuditError('Audit log entries cannot be modified.')


@event.listens_for(AuditLog, 'before_delete')
def _block_delete(mapper, connection, target):
    raise AuditError('Audit log entries cannot be deleted.')
