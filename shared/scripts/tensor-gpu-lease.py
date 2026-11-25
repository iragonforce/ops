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
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import stat
import time
import uuid
from typing import Protocol


class LeaseError(Exception):
    """Operator-safe refusal; state is unchanged unless explicitly documented."""


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

    def __init__(self, db_path: Path, backend: DesktopBackend):
        self.path = Path(db_path)
        _safe_state_dir(self.path)
        self.backend = backend
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

    def acquire(self, owner: str, resource: str, *, activity: str, foreground: bool = False) -> str:
        """Reserve an identical model/resource; never preempt another resource.

        Explicit foreground requests bypass *idle admission*, not busy-GPU checks.
        The calling adapter is responsible for strong foreground authorization.
        """
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
                self._conn.execute("INSERT INTO gpu_leases VALUES (?,?,?,?)",
                                   (token,owner,resource,int(time.time())))
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
            self._conn.execute("INSERT INTO gpu_leases VALUES (?,?,?,?)",
                               (token,owner,resource,int(time.time())))
            self._set_state('reserved',resource,initially_active)
            return token

    def release(self, token: str) -> str:
        with self._guard():
            state = self._state()
            found = self._conn.execute("SELECT token FROM gpu_leases WHERE token=?",(token,)).fetchone()
            if not found or state['mode'] != 'reserved':
                raise LeaseError("Unknown lease token or invalid lifecycle state")
            self._conn.execute("DELETE FROM gpu_leases WHERE token=?",(token,))
            if self._holders():
                return 'reserved'
            self._set_state('restore_pending',state['resource'],bool(state['restore_wallpaper']))
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
