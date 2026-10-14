"""Basic verification of the running integrated server (no credentials printed)."""
import os
import sys
from urllib.request import urlopen
from urllib.error import URLError

base = os.environ.get('KORENA_SERVER_URL', 'http://localhost:8000').rstrip('/')
if not base.startswith('https://') and not base.startswith(('http://localhost:', 'http://127.0.0.1:')):
    sys.exit('ERROR: Set KORENA_SERVER_URL to an HTTPS endpoint (or localhost for tests).')
try:
    with urlopen(base + '/health', timeout=10) as r:
        print('Health check:', r.status, r.read(256).decode('utf-8', 'replace'))
        if r.status != 200:
            sys.exit(1)
except URLError as e:
    sys.exit('Server unreachable: ' + str(e))
print('Server reachable. Next: verify login and accounting operations manually on each device.')
