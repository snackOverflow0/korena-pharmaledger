"""Korena Pharmacy hosted desktop client. Stores only the server address locally."""
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
import webview

APP_DIR = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'KorenaPharmaLedger'
CONFIG_FILE = APP_DIR / 'client.json'


def validate_url(value):
    value = (value or '').strip().rstrip('/')
    parsed = urlsplit(value)
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('localhost', '127.0.0.1')):
        raise ValueError('Use an HTTPS server URL. HTTP is allowed only for localhost.')
    if not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/') or parsed.hostname.endswith('.example'):
        raise ValueError('Enter only a valid base server address, such as https://ledger.example.org')
    return value


def get_saved_url():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding='utf-8')).get('server_url', '')
        except (ValueError, OSError):
            return ''
    return ''


def prompt_server_url(initial):
    import tkinter as tk
    from tkinter import simpledialog, messagebox
    root = tk.Tk()
    root.withdraw()
    while True:
        result = simpledialog.askstring('Korena Pharmacy — Server setup',
            'Enter the shared PharmaLedger HTTPS address\n(provided by your administrator):',
            initialvalue=initial, parent=root)
        if result is None:
            root.destroy()
            raise SystemExit(0)
        try:
            url = validate_url(result)
            APP_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps({'server_url': url}), encoding='utf-8')
            root.destroy()
            return url
        except (ValueError, OSError) as exc:
            messagebox.showerror('Invalid address', str(exc), parent=root)
            initial = result


def main():
    configured = os.environ.get('KORENA_SERVER_URL') or get_saved_url()
    try:
        url = validate_url(configured)
    except (ValueError, AttributeError):
        url = prompt_server_url(configured)
    webview.create_window('Korena Pharmacy | PharmaLedger', url, width=1200,
                          height=800, min_size=(390, 600))
    webview.start(debug=False, private_mode=False)


if __name__ == '__main__':
    main()
