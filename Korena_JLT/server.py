"""WSGI entry point for the hosted Korena Pharmacy system."""
import os
from app import create_app
from database import connect, initialize

# Require an explicit database and admin setup, never silently use developer MySQL.
if not os.environ.get('DATABASE_URL'):
    raise RuntimeError('DATABASE_URL is required for the shared server.')
if not os.environ.get('FLASK_SECRET_KEY') or len(os.environ['FLASK_SECRET_KEY']) < 32:
    raise RuntimeError('FLASK_SECRET_KEY must contain 32+ characters.')

engine, sessions = connect()
initialize(engine, sessions, os.environ.get('ADMIN_EMAIL'), os.environ.get('INITIAL_ADMIN_PASSWORD'))
app = create_app()
