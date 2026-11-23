#!/usr/bin/env python3
"""Install the native user-level qdrant-memory file watcher on qubit/tensor.

Creates matching ~/qdrant-inbox, uses the same ~/.local/bin/qdrant-memory
entrypoint. Tensor: systemd --user .service/.path/.timer (no root).
Qubit: one launchd LaunchAgent (WatchPaths and 15-minute reconciliation).
This does not install or modify Nexus's existing system-level watcher.
"""
import argparse
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

HOME = Path.home()
CLI = HOME / '.local/bin/qdrant-memory'
INBOX = HOME / 'qdrant-inbox'
STATE = HOME / '.local/state/qdrant-memory'
LABEL = 'com.blinkwired.qdrant-memory'


def run(*args):
    subprocess.run(args, check=True)


def systemd_files():
    service = '''[Unit]
Description=Qdrant Memory (forward this host inbox to Nexus)
ConditionPathIsDirectory=%h/qdrant-inbox

[Service]
Type=oneshot
WorkingDirectory=%h
ExecStartPre=/usr/bin/sleep 2
ExecStart=%h/.local/bin/qdrant-memory sync-inbox
TimeoutStartSec=0
'''
    path = '''[Unit]
Description=Qdrant Memory (watch inbox on this host)

[Path]
PathModified=%h/qdrant-inbox
Unit=qdrant-memory.service

[Install]
WantedBy=paths.target
'''
    timer = '''[Unit]
Description=Qdrant Memory (periodic inbox reconciliation)

[Timer]
OnBootSec=3min
OnUnitInactiveSec=15min
AccuracySec=1min
Unit=qdrant-memory.service

[Install]
WantedBy=timers.target
'''
    return {f'qdrant-memory.{name}': text.encode() for name, text in
            [('service', service), ('path', path), ('timer', timer)]}


def launchd_file():
    data = {
        'Label': LABEL,
        'ProgramArguments': [str(CLI), 'sync-inbox'],
        'RunAtLoad': True,
        'StartInterval': 900,
        'WatchPaths': [str(INBOX)],
        'EnvironmentVariables': {'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin'},
        'StandardOutPath': str(STATE / 'watch.log'),
        'StandardErrorPath': str(STATE / 'watch-error.log'),
        'ProcessType': 'Background',
    }
    return plistlib.dumps(data, fmt=plistlib.FMT_XML, sort_keys=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    if not args.dry_run and not args.install:
        parser.error('Select --dry-run or --install')
    if not CLI.is_file():
        raise RuntimeError(f'CLI missing: {CLI}')
    if not INBOX.is_dir() or INBOX.is_symlink():
        raise RuntimeError('Inbox missing: run qdrant-memory init --host tensor|qubit')
    host_file = HOME / '.config/qdrant-memory/host'
    if not host_file.is_file():
        raise RuntimeError('Host config missing: run qdrant-memory init --host tensor|qubit')
    host = host_file.read_text(encoding='utf-8').strip()
    if host not in ('tensor', 'qubit'):
        raise RuntimeError('This installer is only for qubit/tensor clients')
    if (sys.platform == 'darwin' and host != 'qubit') or (sys.platform.startswith('linux') and host != 'tensor'):
        raise RuntimeError('Host platform/config mismatch')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STATE, 0o700)
    if sys.platform == 'darwin':
        destination = HOME / 'Library/LaunchAgents' / f'{LABEL}.plist'
        entries = {destination: launchd_file()}
    elif sys.platform.startswith('linux'):
        directory = HOME / '.config/systemd/user'
        entries = {directory / name: data for name, data in systemd_files().items()}
    else:
        raise RuntimeError('Only macOS and Linux supported')
    print(f'PLATFORM={sys.platform} HOST={host}')
    for destination, content in entries.items():
        if destination.is_symlink():
            raise RuntimeError(f'Refusing symlink: {destination}')
        if destination.exists() and destination.read_bytes() != content:
            raise RuntimeError(f'Existing watcher differs; not overwriting: {destination}')
        print(('VERIFY' if args.dry_run else 'INSTALL') + f': {destination}')
    if args.dry_run:
        print('DRY RUN: no files written or watchers activated')
        return
    for destination, content in entries.items():
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not destination.exists():
            with destination.open('xb') as out:
                out.write(content)
    if host == 'tensor':
        run('systemctl', '--user', 'daemon-reload')
        run('systemctl', '--user', 'enable', '--now', 'qdrant-memory.path', 'qdrant-memory.timer')
        run('systemctl', '--user', 'is-active', 'qdrant-memory.path', 'qdrant-memory.timer')
    else:
        domain = f'gui/{os.getuid()}'
        # bootout succeeds only if already loaded; when this is a new install,
        # directly bootstrap. Existing identical launchd job is left untouched.
        result = subprocess.run(['launchctl', 'print', f'{domain}/{LABEL}'],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode:
            run('launchctl', 'bootstrap', domain, str(next(iter(entries))))
        run('launchctl', 'enable', f'{domain}/{LABEL}')
        run('launchctl', 'kickstart', '-k', f'{domain}/{LABEL}')
    print('PASS: qdrant-memory watcher installed; 15-minute reconciliation enabled')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
