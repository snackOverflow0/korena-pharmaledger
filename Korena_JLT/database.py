"""XAMPP MySQL/MariaDB database connector. SQLite optional for tests/demo."""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from models import Base, User
from accounting import create_default_accounts

load_dotenv(Path(__file__).resolve().parent / '.env')
DEFAULT_DATABASE = 'mysql+pymysql://root:@127.0.0.1:3306/pharma_ledger?charset=utf8mb4'

def connect(url=None):
    url = url or os.environ.get('DATABASE_URL', DEFAULT_DATABASE)
    params = {'pool_pre_ping': True}
    if url.startswith('sqlite'):
        params['connect_args'] = {'check_same_thread': False}
    engine = create_engine(url, **params)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)

def initialize(engine, sessions, email=None, password=None):
    """Non-destructive: creates missing tables, leaves old data intact."""
    Base.metadata.create_all(engine)
    with sessions.begin() as db:
        create_default_accounts(db)
        if not db.query(User).first():
            if not password or len(password) < 10:
                raise ValueError('Set INITIAL_ADMIN_PASSWORD to 10+ characters in .env.')
            db.add(User(email=(email or 'admin@pharmaledger.local').lower().strip(),
                        password_hash=generate_password_hash(password), role='admin'))
