#!/usr/bin/env python3
"""Stage 2 *synthetic-only* GPU lease state machine for Tensor.

No systemd, NVIDIA, Ollama, MinerU, or process-management backend is provided.
The only supported runtime backend in this stage is an injected test fake.

This module records desktop-restore intent BEFORE stopping a desktop helper,
refuses competing GPU resources, and never restores until a backend explicitly
confirms all inference allocations have been released.

Usage: tensor-gpu-lease.py --help
Source of truth: iragonforce/ops; reviewed public snapshot: iragonforce/tensor.
"""
from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import stat
import time
import uuid
from typing import Callable, Protocol


class LeaseError(Exception):
    """Operator-safe refusal; state is unchanged unless explicitly documented."""


@dataclass(frozen=True)
class OwnerIdentity:
    """Observed Linux process identity; supplied by a trusted future launcher.

    The CLI currently has NO live acquire entrypoint. A caller-supplied PID is
    not authentication. Production launchers must bind their own kernel identity.
    """
    boot_id: str
    pid: int
    start_ticks: int


def validate_identity(identity: OwnerIdentity | None) -> None:
    if identity is None:
        return
    if (not isinstance(identity, OwnerIdentity)
            or not isinstance(identity.boot_id, str)
            or not 1 <= len(identity.boot_id) <= 128
            or any(c.isspace() or ord(c) < 33 for c in identity.boot_id)
            or type(identity.pid) is not int or identity.pid <= 0
            or type(identity.start_ticks) is not int or identity.start_ticks <= 0):
        raise LeaseError("Invalid Linux process identity")


class DesktopBackend(Protocol):
    """Interface for a future strictly scoped, independently validated adapter."""

    def wallpaper_active(self) -> bool: ...
    def stop_wallpaper(self) -> None: ...
    def start_wallpaper(self) -> None: ...
    def safe_to_acquire(self) -> bool: ...
    def inference_memory_released(self) -> bool: ...


def _safe_state_dir(db_path: Path) -> None:
    parent = db_path.parent
    if not parent.exists():
        parent.mkdir(parents=True, mode=0o700)
    if parent.is_symlink() or not parent.is_dir():
        raise LeaseError("Refusing symlink or non-directory state")
    pstat = parent.stat()
    if pstat.st_uid != os.geteuid() or stat.S_IMODE(pstat.st_mode) != 0o700:
        raise LeaseError("State directory must be caller-owned, 0700")
    if db_path.is_symlink():
        raise LeaseError("Refusing symlink database")
    if db_path.exists():
        dst = db_path.stat()
        if not db_path.is_file() or dst.st_uid != os.geteuid() or stat.S_IMODE(dst.st_mode) != 0o600:
            raise LeaseError("Database must be caller-owned regular file, 0600")


class LeaseManager:
    """Durable admission state; has no way to call a real process/service."""

    def __init__(self, db_path: Path, backend: DesktopBackend, *, require_identity: bool = False):
        self.path = Path(db_path)
        _safe_state_dir(self.path)
        self.backend = backend
        self.require_identity = require_identity
        self._conn = sqlite3.connect(self.path, timeout=8.0, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        os.chmod(self.path, 0o600)
        self._conn.execute("PRAGMA busy_timeout=8000")
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript('''
            CREATE TABLE IF NOT EXISTS gpu_lease_state (
                id INTEGER PRIMARY KEY CHECK (id=1),
                mode TEXT NOT NULL CHECK (mode IN ('normal','preparing','reserved','restore_pending')),
                resource TEXT,
                restore_wallpaper INTEGER NOT NULL CHECK (restore_wallpaper IN (0,1)),
                modified_at INTEGER NOT NULL
            );
            INSERT OR IGNORE INTO gpu_lease_state
                (id,mode,resource,restore_wallpaper,modified_at)
                VALUES (1,'normal',NULL,0,0);
            CREATE TABLE IF NOT EXISTS gpu_leases (
                token TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                resource TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
        ''')
        # Additive migration. Old synthetic leases remain unbound and must
        # never be assumed dead; no state or holder row is deleted here.
        with self._guard():
            self._conn.execute('BEGIN IMMEDIATE')
            try:
                columns = {r['name'] for r in self._conn.execute('PRAGMA table_info(gpu_leases)')}
                for name, sql_type in (
                    ('owner_boot_id', 'TEXT'),
                    ('owner_pid', 'INTEGER'),
                    ('owner_start_ticks', 'INTEGER'),
                ):
                    if name not in columns:
                        self._conn.execute(f'ALTER TABLE gpu_leases ADD COLUMN {name} {sql_type}')
                self._conn.execute('COMMIT')
            except BaseException:
                self._conn.execute('ROLLBACK')
                raise

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @contextlib.contextmanager
    def _guard(self):
        lock_path = self.path.parent / "gpu-lease.lock"
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            if os.fstat(fd).st_uid != os.geteuid() or stat.S_IMODE(os.fstat(fd).st_mode) != 0o600:
                raise LeaseError("Lease lock ownership/mode incorrect")
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)

    def _state(self):
        return self._conn.execute("SELECT * FROM gpu_lease_state WHERE id=1").fetchone()

    def _holders(self) -> list[sqlite3.Row]:
        return list(self._conn.execute("SELECT * FROM gpu_leases ORDER BY created_at, token"))

    def status(self) -> dict:
        with self._guard():
            state = self._state()
            holders = self._holders()
            return dict(mode=state['mode'], resource=state['resource'],
                        restore_wallpaper=bool(state['restore_wallpaper']),
                        leases=len(holders), owners=[r['owner'] for r in holders])

    def _set_state(self, mode: str, resource: str | None, restore: bool) -> None:
        self._conn.execute("UPDATE gpu_lease_state SET mode=?, resource=?, restore_wallpaper=?, modified_at=? WHERE id=1",
                           (mode, resource, int(restore), int(time.time())))

    def _insert_holder(self, token: str, owner: str, resource: str,
                       identity: OwnerIdentity | None) -> None:
        self._conn.execute('''INSERT INTO gpu_leases
            (token, owner, resource, created_at, owner_boot_id, owner_pid, owner_start_ticks)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (token, owner, resource, int(time.time()),
             identity.boot_id if identity else None,
             identity.pid if identity else None,
             identity.start_ticks if identity else None))

    @contextlib.contextmanager
    def _transaction(self):
        self._conn.execute('BEGIN IMMEDIATE')
        try:
            yield
            self._conn.execute('COMMIT')
        except BaseException:
            self._conn.execute('ROLLBACK')
            raise

    def acquire(self, owner: str, resource: str, *, activity: str, foreground: bool = False,
                identity: OwnerIdentity | None = None) -> str:
        """Reserve an identical model/resource; never preempt another resource.

        Explicit foreground requests bypass *idle admission*, not busy-GPU checks.
        The calling adapter is responsible for strong foreground authorization.
        """
        validate_identity(identity)
        if self.require_identity and identity is None:
            raise LeaseError('Verified owner identity required for live admission')
        if not owner or not resource or len(owner) > 128 or len(resource) > 128:
            raise LeaseError("Invalid owner/resource")
        if any(ord(c) < 32 for c in owner + resource):
            raise LeaseError("Control characters disallowed")
        if activity != 'idle' and not foreground:
            raise LeaseError("Background admission denied: user active or idle unknown")
        if activity not in ('idle', 'active', 'unknown'):
            raise LeaseError("Invalid activity signal")
        with self._guard():
            state = self._state()
            holders = self._holders()
            if holders:
                if state['mode'] != 'reserved' or state['resource'] != resource:
                    raise LeaseError("GPU reserved for a different resource")
                token = str(uuid.uuid4())
                self._insert_holder(token, owner, resource, identity)
                return token
            if state['mode'] != 'normal':
                raise LeaseError("Unresolved GPU lifecycle state; reconcile before admission")
            # Intent is durable before a desktop transition. Any exception leaves
            # a recoverable preparing state, never a false 'normal' state.
            initially_active = self.backend.wallpaper_active()
            self._set_state('preparing', resource, initially_active)
            if initially_active:
                self.backend.stop_wallpaper()
            if self.backend.wallpaper_active():
                raise LeaseError("Wallpaper supervisor did not stop; lifecycle needs reconciliation")
            if not self.backend.safe_to_acquire():
                raise LeaseError("Uncoordinated GPU allocation; lifecycle needs reconciliation")
            token = str(uuid.uuid4())
            # Registration and reserved transition commit atomically. If a
            # crash precedes this, 'preparing' remains fail-closed.
            with self._transaction():
                self._insert_holder(token, owner, resource, identity)
                self._set_state('reserved',resource,initially_active)
            return token

    def release(self, token: str) -> str:
        with self._guard():
            state = self._state()
            found = self._conn.execute("SELECT token FROM gpu_leases WHERE token=?",(token,)).fetchone()
            if not found or state['mode'] != 'reserved':
                raise LeaseError("Unknown lease token or invalid lifecycle state")
            with self._transaction():
                self._conn.execute("DELETE FROM gpu_leases WHERE token=?",(token,))
                last_holder = not self._holders()
                if last_holder:
                    self._set_state('restore_pending',state['resource'],bool(state['restore_wallpaper']))
            if not last_holder:
                return 'reserved'
            return self._finalize_restore()

    def _finalize_restore(self) -> str:
        state = self._state()
        if self._holders():
            return 'reserved'
        if not self.backend.inference_memory_released():
            return 'restore_pending'
        if state['restore_wallpaper'] and not self.backend.wallpaper_active():
            self.backend.start_wallpaper()
        # No wallpaper service is started if it was originally inactive.
        self._set_state('normal',None,False)
        return 'normal'

    def recover_dead_owners(self, owner_status: Callable[[OwnerIdentity], str]) -> dict:
        """Recover only independently verified dead identities under the lease lock.

        Unknown/unbound identity prevents *all* mutations this pass. A dead
        owner is removed atomically; if this was the last holder, restoration
        still requires the normal GPU-residency release proof. No model is
        stopped by this method. The caller must use the trusted /proc verifier.
        """
        with self._guard():
            state = self._state()
            holders = self._holders()
            if state['mode'] != 'reserved' or not holders:
                return {'result': state['mode'], 'recovered': 0, 'unverified': 0}
            outcomes = {}
            for row in holders:
                if row['owner_boot_id'] is None or row['owner_pid'] is None or row['owner_start_ticks'] is None:
                    return {'result': 'reserved', 'recovered': 0, 'unverified': 1}
                identity = OwnerIdentity(row['owner_boot_id'], row['owner_pid'], row['owner_start_ticks'])
                try:
                    validate_identity(identity)
                    status = owner_status(identity)
                except (OSError, ValueError, LeaseError):
                    status = 'unknown'
                if status not in ('dead', 'live'):
                    return {'result': 'reserved', 'recovered': 0, 'unverified': 1}
                outcomes[row['token']] = status
            dead = [token for token, status in outcomes.items() if status == 'dead']
            if not dead:
                return {'result': 'reserved', 'recovered': 0, 'unverified': 0}
            with self._transaction():
                for token in dead:
                    self._conn.execute('DELETE FROM gpu_leases WHERE token=?', (token,))
                last_holder = not self._holders()
                if last_holder:
                    self._set_state('restore_pending',state['resource'],bool(state['restore_wallpaper']))
            if not last_holder:
                return {'result': 'reserved', 'recovered': len(dead), 'unverified': 0}
            return {'result': self._finalize_restore(), 'recovered': len(dead), 'unverified': 0}

    def reconcile(self) -> str:
        """Explicit crash/failure recovery; fail closed while GPU is occupied."""
        with self._guard():
            state = self._state()
            if self._holders():
                return 'reserved'
            if state['mode'] == 'normal':
                return 'normal'
            return self._finalize_restore()

    def enforce(self) -> str:
        """Re-stop a wallpaper supervisor externally restarted during a lease."""
        with self._guard():
            state = self._state()
            if self._holders() and state['mode'] == 'reserved':
                if self.backend.wallpaper_active():
                    self.backend.stop_wallpaper()
                if self.backend.wallpaper_active():
                    raise LeaseError("Wallpaper restart could not be contained")
                return 'reserved'
            return state['mode']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version='tensor-gpu-lease stage2-synthetic')
    parser.parse_args()
    print('Stage 2 is library/test-only: real GPU and desktop backends are intentionally unavailable.')


if __name__ == '__main__':
    main()
