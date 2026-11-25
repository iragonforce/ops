#!/usr/bin/env python3
"""Stage 2D read-only wallpaper admission and GPU owner-identity policy.

Does not start/stop services, evict a GPU process, or repair a lease.
No production hook should use this predicate until the coordinator implements
atomic start arbitration and owner registration/recovery.

Usage: tensor-gpu-lifecycle-guard.py [--db PATH] [--check-wallpaper-start]
Source: iragonforce/ops. Public copy: iragonforce/tensor after acceptance.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sqlite3
import stat
import sys
from urllib.parse import quote

DEFAULT_DB = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'tensor-gpu-lease' / 'queue.sqlite3'
STATES = frozenset({'normal', 'preparing', 'reserved', 'restore_pending'})


class GuardError(RuntimeError):
    """Unknown/unverified state: deny rather than assume the desktop is safe."""


def _secure_regular(path: Path) -> None:
    parent = path.parent
    if parent.is_symlink() or path.is_symlink():
        raise GuardError('Symlink state path')
    if not parent.is_dir() or not path.is_file():
        raise GuardError('Lease state unavailable')
    for item, mode in ((parent, 0o700), (path, 0o600)):
        st = item.stat()
        if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != mode:
            raise GuardError('Unexpected state owner or permissions')


def read_state(db: Path) -> dict:
    """One SQLite read transaction; no database initialization or mutation."""
    db = Path(db)
    _secure_regular(db)
    uri = 'file:' + quote(str(db.resolve()), safe='/') + '?mode=ro'
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=2)
        try:
            conn.execute('PRAGMA query_only=ON')
            conn.execute('BEGIN')
            row = conn.execute('SELECT mode, resource, restore_wallpaper FROM gpu_lease_state WHERE id=1').fetchone()
            count = conn.execute('SELECT COUNT(*) FROM gpu_leases').fetchone()[0]
            conn.rollback()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        raise GuardError('Cannot verify lease database') from exc
    if row is None or row[0] not in STATES or row[2] not in (0, 1) or not isinstance(count, int) or count < 0:
        raise GuardError('Malformed lease state')
    return {'mode': row[0], 'resource': row[1], 'leases': count, 'restore_wallpaper': bool(row[2])}


def wallpaper_start_policy(state: dict) -> tuple[bool, str]:
    """Conservative predicate. Guarded service startup must ALSO be race-safe."""
    if (state.get('mode') == 'normal' and state.get('leases') == 0
            and state.get('resource') is None and state.get('restore_wallpaper') is False):
        return True, 'no_active_reservation'
    return False, 'gpu_lifecycle_not_normal'


@dataclass(frozen=True)
class OwnerIdentity:
    boot_id: str
    pid: int
    start_ticks: int


def parse_proc_stat(raw: str) -> tuple[str, int]:
    """Read Linux /proc/PID/stat state and field 22 despite spaces in comm."""
    open_idx = raw.find(' (')
    idx = raw.rfind(') ')
    if open_idx <= 0 or idx <= open_idx or not raw[:open_idx].isdecimal():
        raise GuardError('Malformed process stat prefix')
    fields = raw[idx + 2:].split()  # starts with field 3: state
    if len(fields) <= 19:
        raise GuardError('Short process stat')
    try:
        ticks = int(fields[19])  # field 22 (starttime)
    except ValueError as exc:
        raise GuardError('Malformed process start time') from exc
    if ticks <= 0 or fields[0] not in 'RSDZTIWXPK':
        raise GuardError('Invalid process state')
    return fields[0], ticks


def inspect_process(identity: OwnerIdentity, *, proc: Path = Path('/proc'), boot_id: str | None = None) -> str:
    """Return live/dead/unknown; never mistake permission errors for death."""
    if identity.pid <= 0 or identity.start_ticks <= 0 or not identity.boot_id:
        return 'unknown'
    try:
        current_boot = boot_id if boot_id is not None else (proc / 'sys/kernel/random/boot_id').read_text().strip()
    except OSError:
        return 'unknown'
    if not current_boot:
        return 'unknown'
    if current_boot != identity.boot_id:
        return 'dead'
    try:
        raw = (proc / str(identity.pid) / 'stat').read_text()
    except FileNotFoundError:
        return 'dead'
    except OSError:
        return 'unknown'
    try:
        status, ticks = parse_proc_stat(raw)
    except GuardError:
        return 'unknown'
    if ticks != identity.start_ticks or status in ('Z', 'X'):
        return 'dead'
    return 'live'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--check-wallpaper-start', action='store_true',
                        help='read-only conservative decision; NOT a live authorization or race-proof service hook')
    args = parser.parse_args()
    try:
        state = read_state(args.db)
        allowed, reason = wallpaper_start_policy(state)
    except (GuardError, OSError) as exc:
        state, allowed, reason = None, False, str(exc)
    print(json.dumps({'mode': 'read-only', 'wallpaper_start_candidate': allowed,
                      'reason': reason, 'state': state,
                      'live_control_enabled': False}, sort_keys=True))
    return 0 if (not args.check_wallpaper_start or allowed) else 1


if __name__ == '__main__':
    sys.exit(main())
