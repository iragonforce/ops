#!/usr/bin/env python3
"""Tensor Stage 2D wallpaper startup arbitration (source-only contract).

Runs a trusted, injected synchronous wallpaper-launch operation under the SAME
flock file as LeaseManager. No CLI option can start a service. Future systemd
integration must use Type=notify startup and must NOT wait for this lock from
LeaseManager._finalize_restore(), which currently holds it across systemctl.

See man/tensor/tensor-gpu-wallpaper-arbiter.1. Source: iragonforce/ops.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
from typing import Callable

SCRIPT_DIR = Path(__file__).resolve().parent
GUARD_SCRIPT = SCRIPT_DIR / 'tensor-gpu-lifecycle-guard.py'


class ArbitrationError(RuntimeError):
    """Unknown security, lock, or startup state. Never infer permission."""


@dataclass(frozen=True)
class StartDecision:
    started: bool
    reason: str


def _load_policy():
    spec = importlib.util.spec_from_file_location('tensor_gpu_lifecycle_guard_for_arbiter', GUARD_SCRIPT)
    if not spec or not spec.loader:
        raise ArbitrationError('Cannot load lifecycle guard')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _lock_file(db: Path) -> int:
    """Use the exact existing lease-manager lock; never replace or chmod it."""
    parent = db.parent
    if parent.is_symlink() or not parent.is_dir():
        raise ArbitrationError('Lease state directory unavailable')
    info = parent.stat()
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ArbitrationError('Lease state directory owner/mode invalid')
    lock_path = parent / 'gpu-lease.lock'
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise ArbitrationError('Lease lock owner/type/mode invalid')
        return fd
    except BaseException:
        os.close(fd)
        raise


def try_start(db: Path, launch: Callable[[], None], ready: Callable[[], bool],
              abort: Callable[[], None], *,
              gpu_safe: Callable[[], bool], policy=None) -> StartDecision:
    """Attempt an atomic, *synthetic* startup under the lease lock.

    `launch` must have initiated the supervised wallpaper process before
    returning. `ready` must verify process startup and send systemd READY=1
    while this lock remains held. Callbacks must be bounded and must never
    invoke a blocking systemctl start/stop transaction that reacquires this
    lock. `abort` must terminate ONLY this candidate and its children, and is
    invoked under the lock if launch/readiness fails. A refusal invokes no
    callback. No live CLI uses this method.

    A service still in `activating` when another GPU lease arrives must cause
    the lease adapter to fail closed, not wait for its startup under the lock.
    """
    db = Path(db)
    guard = policy if policy is not None else _load_policy()
    fd = _lock_file(db)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return StartDecision(False, 'lease_lock_busy')
        try:
            state = guard.read_state(db)
            allowed, reason = guard.wallpaper_start_policy(state)
        except (guard.GuardError, OSError, ValueError) as exc:
            return StartDecision(False, 'unverified_lease_state:' + str(exc))
        if not allowed:
            return StartDecision(False, reason)
        try:
            gpu_clear = gpu_safe()
        except Exception:
            return StartDecision(False, 'unverified_gpu_residency')
        if gpu_clear is not True:
            return StartDecision(False, 'gpu_residency_veto')
        # Hold the SAME lock across eligibility, process creation, and READY.
        # This closes the read-check/start race with LeaseManager.acquire().
        try:
            launch()
            if ready() is not True:
                raise ArbitrationError('Wallpaper launch not confirmed ready')
        except BaseException:
            try:
                abort()  # Clean up ONLY the just-started candidate, still locked.
            except BaseException as cleanup_exc:
                raise ArbitrationError('Candidate cleanup failed; intervention required') from cleanup_exc
            raise
        return StartDecision(True, 'launched_under_lease_lock')
    finally:
        os.close(fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version='stage2d-wallpaper-arbiter-source-only')
    parser.parse_args()
    print(json.dumps({'mode': 'read-only', 'live_control_enabled': False,
                      'reason': 'No service startup CLI or unit hooks installed; '
                                'atomic synthetic callback API only.'}, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
