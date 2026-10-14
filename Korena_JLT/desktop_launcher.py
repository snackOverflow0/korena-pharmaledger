"""Offline PharmaLedger desktop launcher. Local SQLite, first-run admin setup."""
import os
import secrets
import socket
import sys
import threading
from pathlib import Path

APP_NAME = 'PharmaLedger'


def data_directory():
    """Never store writable records inside the PyInstaller temporary extraction directory."""
    root = Path(os.environ.get('LOCALAPPDATA') or (Path.home() / '.local' / 'share'))
    target = root / APP_NAME
    target.mkdir(parents=True, exist_ok=True)
    return target


def failure(title, message):
    try:
        import tkinter as tk
        from tkinter import messagebox
        parent = tk.Tk()
        parent.withdraw()
        messagebox.showerror(title, str(message), parent=parent)
        parent.destroy()
    except Exception:
        print(f'{title}: {message}', file=sys.stderr)


def initial_admin_credentials():
    import tkinter as tk
    from tkinter import simpledialog
    root = tk.Tk()
    root.withdraw()
    try:
        email = simpledialog.askstring('PharmaLedger first-time setup',
            'Create an administrator account.\n\nEnter admin email:',
            initialvalue='admin@pharmaledger.local', parent=root)
        if email is None:
            return None
        email = email.strip().lower()
        if '@' not in email or len(email) > 160:
            raise ValueError('Please enter a valid administrator email.')
        password = simpledialog.askstring('PharmaLedger first-time setup',
            'Create an administrator password (at least 10 characters):',
            show='*', parent=root)
        if password is None:
            return None
        if len(password) < 10:
            raise ValueError('Password must contain at least 10 characters.')
        confirm = simpledialog.askstring('PharmaLedger first-time setup',
            'Confirm administrator password:', show='*', parent=root)
        if confirm is None:
            return None
        if confirm != password:
            raise ValueError('Passwords did not match.')
        return email, password
    finally:
        root.destroy()


def available_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    try:
        from sqlalchemy import select
        from database import connect, initialize
        from models import Base, User
        storage = data_directory()
        database_file = storage / 'pharmaledger.sqlite3'
        # All writes go to local application data, never to bundled files.
        os.environ['DATABASE_URL'] = 'sqlite:///' + database_file.as_posix()
        secret_file = storage / '.flask_secret'
        if not secret_file.is_file():
            secret_file.write_text(secrets.token_hex(48), encoding='utf-8')
        os.environ['FLASK_SECRET_KEY'] = secret_file.read_text(encoding='utf-8').strip()
        engine, Sessions = connect()
        Base.metadata.create_all(engine)
        with Sessions() as db:
            first_run = db.scalar(select(User.id).limit(1)) is None
        if first_run:
            try:
                credentials = initial_admin_credentials()
            except ValueError as ex:
                failure('Invalid administrator setup', ex)
                return 1
            if credentials is None:
                return 1
            initialize(engine, Sessions, *credentials)
        from app import create_app
        app = create_app()
        from waitress import create_server
        import webview
        port = available_port()
        server = create_server(app, host='127.0.0.1', port=port, threads=4)
        thread = threading.Thread(target=server.run, daemon=True, name='pharmaledger-server')
        thread.start()
        webview.create_window('PharmaLedger | Offline Accounting',
                              f'http://127.0.0.1:{port}/',
                              width=1250, height=820, min_size=(850, 600), confirm_close=True)
        try:
            webview.start(gui='edgechromium', private_mode=True)
        finally:
            server.close()
        return 0
    except Exception as exc:
        failure('PharmaLedger could not start',
                f'{exc}\n\nCheck that Microsoft Edge WebView2 Runtime is installed.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
