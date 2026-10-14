"""Compatible with original PharmaLedger users/accounts/entries/lines tables.
Other legacy tables in an existing database are left untouched.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Numeric, Boolean, Index, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(160), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='staff')

class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    category = Column(String(20), nullable=False)
    active = Column(Boolean, nullable=False, default=True)

class Entry(Base):
    __tablename__ = 'entries'
    id = Column(Integer, primary_key=True)
    posted_on = Column(Date, nullable=False)
    reference = Column(String(80), unique=True, nullable=False)
    description = Column(String(255), nullable=False)
    kind = Column(String(32), nullable=False, default='general')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    lines = relationship('Line', back_populates='entry', order_by='Line.id')
    __table_args__ = (Index('ix_entries_posted_on', 'posted_on'),)

class Line(Base):
    __tablename__ = 'lines'
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('entries.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    debit = Column(Numeric(15, 2), nullable=False, default=0)
    credit = Column(Numeric(15, 2), nullable=False, default=0)
    entry = relationship('Entry', back_populates='lines')
    account = relationship('Account')


class AuditLog(Base):
    """Append-only record of who did what and when.

    user_id is deliberately NOT a foreign key and user_email is a snapshot, so the
    history survives even if a user row is later changed or removed.
    prev_hash/row_hash form a hash chain that makes edits or deletions detectable.
    """
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String(160), nullable=True)
    action = Column(String(40), nullable=False)
    entity_type = Column(String(30), nullable=True)
    entity_id = Column(Integer, nullable=True)
    summary = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)          # JSON text
    ip_address = Column(String(45), nullable=True)
    prev_hash = Column(String(64), nullable=False)
    row_hash = Column(String(64), nullable=False)
    __table_args__ = (Index('ix_audit_created_at', 'created_at'),
                      Index('ix_audit_action', 'action'),
                      Index('ix_audit_user_id', 'user_id'))
