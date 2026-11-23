#!/usr/bin/env python3
# Report network state for the existing Glance dashboard. See glance-network-status.py(1) for source and integration details.
"""Fixed-inventory endpoint checks; public checks bypass split DNS using DoH."""

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Report network state for the existing Glance dashboard.\nUsage: glance-network-status.py \n\nSource: hosts/nexus/files/usr/local/libexec/glance-network-status.py in ~/ops\nSee man glance-network-status.py for the existing call sites and argument handling.')
        raise SystemExit(0)
import concurrent.futures
import http.client
import json
from pathlib import Path
import socket
import ssl
import time
import urllib.parse
import urllib.request

CATALOG = Path('/srv/containers/data/glance/config/assets/homelab-services.json')
OUTPUT = CATALOG.with_name('homelab-status.json')
dns_cache = {}

def public_ip(host):
    cached = dns_cache.get(host)
    if cached and time.monotonic() - cached[0] < 600:
        return cached[1]
    query = urllib.parse.urlencode({'name': host, 'type': 'A'})
    request = urllib.request.Request('https://dns.google/resolve?' + query, headers={'Accept': 'application/dns-json'})
    with urllib.request.urlopen(request, timeout=8) as response:
        data = json.load(response)
    value = next((a['data'] for a in data.get('Answer', []) if a['type'] == 1), None)
    dns_cache[host] = (time.monotonic(), value)
    return value

class PublicHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address, port):
        super().__init__(host, port, timeout=7)
        self.address = address
    def connect(self):
        raw = socket.create_connection((self.address, self.port), self.timeout)
        self.sock = self._context.wrap_socket(raw, server_hostname=self.host)

def check(service, mode):
    url = service['urls'].get(mode)
    if not url:
        return service['id'], {'state': 'private', 'label': 'Not published' if mode == 'external' else 'Use Tailscale'}
    # A health path is allowed only from this fixed, local inventory.
    url = service.get('checks', {}).get(mode, url)
    parsed = urllib.parse.urlsplit(url)
    connection = None
    start = time.monotonic()
    try:
        if mode == 'external':
            address = public_ip(parsed.hostname)
            if not address:
                return service['id'], {'state': 'unpublished', 'label': 'No public DNS'}
            connection = PublicHTTPS(parsed.hostname, address, parsed.port or 443)
        elif parsed.scheme == 'https':
            context = ssl._create_unverified_context() if service.get('self_signed_local') and mode == 'local' else ssl.create_default_context()
            connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443, timeout=6, context=context)
        else:
            connection = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=6)
        path = urllib.parse.urlunsplit(('', '', parsed.path or '/', parsed.query, ''))
        connection.request('GET', path, headers={'User-Agent': 'Homelab-Glance-Endpoint-Check/1', 'Host': parsed.netloc})
        response = connection.getresponse()
        code = response.status
        location = response.getheader('Location', '')
        protected = 'cloudflareaccess.com' in location or 'cdn-cgi/access' in location
        if protected or code == 401:
            state, label = 'protected', 'Protected · login required'
        elif code == 403:
            state, label = 'restricted', 'Restricted · HTTP 403'
        elif 200 <= code < 400:
            state, label = 'up', 'Reachable' if code < 300 else 'Reachable · redirect'
        else:
            state, label = 'down', 'HTTP ' + str(code)
        return service['id'], {'state': state, 'label': label, 'code': code,
                              'latency_ms': round((time.monotonic() - start) * 1000)}
    except ssl.SSLError:
        return service['id'], {'state': 'down', 'label': 'TLS error'}
    except (OSError, ValueError, http.client.HTTPException):
        return service['id'], {'state': 'down', 'label': 'Unreachable'}
    finally:
        if connection:
            connection.close()

def refresh():
    catalog = json.loads(CATALOG.read_text())
    jobs = [(service, mode) for service in catalog['services'] for mode in ['local', 'tailscale', 'external']]
    result = {'checked_at': time.time(), 'modes': {mode: {} for mode in ['local', 'tailscale', 'external']}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        tasks = [(mode, pool.submit(check, service, mode)) for service, mode in jobs]
        for mode, task in tasks:
            ident, value = task.result()
            result['modes'][mode][ident] = value
    temp = OUTPUT.with_suffix('.new')
    temp.write_text(json.dumps(result) + '\n')
    temp.chmod(0o644)
    temp.replace(OUTPUT)
    print('Endpoint inventory refreshed: ' + str(len(catalog['services'])) + ' services', flush=True)

while True:
    try:
        refresh()
    except Exception as error:
        print('Endpoint inventory refresh failed: ' + type(error).__name__, flush=True)
    time.sleep(60)
