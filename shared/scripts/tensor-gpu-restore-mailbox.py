#!/usr/bin/env python3
"""Private, single-consumer restoration grant mailbox for Tensor GPU lifecycle.

This module is source-only. A future trusted backend publishes a grant while
holding gpu-restore.lock; the Wallpaper Engine Type=notify entrypoint consumes
it once. The guarded arbiter independently checks the grant against SQLite
under gpu-lease.lock. No API starts services or touches a GPU.

Usage: tensor-gpu-restore-mailbox.py [--help | --version]
Source: iragonforce/ops, Stage 2F.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import uuid

MAILBOX_NAME = 'wallpaper-restore.grant'


class MailboxError(RuntimeError):
    """Refuse access when ownership, permissions, or format cannot be verified."""


def _directory(db: Path) -> Path:
    db = Path(db)
    parent = db.parent
    if parent.is_symlink() or db.is_symlink() or not parent.is_dir() or not db.is_file():
        raise MailboxError('Verified lease state unavailable')
    for path, mode in ((parent, 0o700), (db, 0o600)):
        info = path.stat()
        if (info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != mode
                or not (stat.S_ISDIR(info.st_mode) if path == parent else stat.S_ISREG(info.st_mode))):
            raise MailboxError('Lease state ownership or mode incorrect')
    return parent


def _grant(value: str) -> bytes:
    if (not isinstance(value, str) or len(value) != 32
            or any(c not in '0123456789abcdef' for c in value)):
        raise MailboxError('Invalid restoration grant format')
    return (value + '\n').encode('ascii')


def _verify_existing(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
        raise MailboxError('Untrusted mailbox file')


def publish(db: Path, grant: str) -> None:
    """Atomically publish current grant; never put it in argv, env, or logs.

    Caller must serialize all restoration attempts with gpu-restore.lock.
    Replacing the pending value invalidates the prior delivery; only the DB
    restoration grant, independently checked by the arbiter, authorizes use.
    """
    encoded = _grant(grant)
    directory = _directory(db)
    target = directory / MAILBOX_NAME
    _verify_existing(target)
    fd, temporary = tempfile.mkstemp(prefix='.wallpaper-grant-', dir=directory)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'wb', closefd=True) as stream:
            fd = -1
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        # Replace is atomic within the protected 0700 directory.
        _verify_existing(target)
        os.replace(temporary, target)
        temporary = ''
        dirfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        if fd >= 0:
            os.close(fd)
        if temporary:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def consume(db: Path) -> str | None:
    """Atomically remove pending delivery, returning token to trusted caller.

    None means no delivery. The token must only be passed as a Python argument
    to arbiter.try_start(), never printed, logged, exported, or placed in argv.
    The arbiter validates it against the durable SQLite restoration state.
    """
    directory = _directory(db)
    target = directory / MAILBOX_NAME
    temporary = directory / ('.wallpaper-consumed-' + uuid.uuid4().hex)
    try:
        os.rename(target, temporary)
    except FileNotFoundError:
        return None
    try:
        fd = os.open(temporary, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
                    or info.st_size != 33):
                raise MailboxError('Untrusted restoration mailbox')
            raw = os.read(fd, 34)
        finally:
            os.close(fd)
        try:
            value = raw.decode('ascii')
        except UnicodeDecodeError as exc:
            raise MailboxError('Invalid restoration mailbox encoding') from exc
        if not value.endswith('\n'):
            raise MailboxError('Invalid restoration mailbox termination')
        _grant(value[:-1])
        return value[:-1]
    finally:
        # Never leave a consumed capability behind, even after a bad file.
        temporary.unlink(missing_ok=True)


def revoke(db: Path, grant: str) -> bool:
    """Remove only this caller's unconsumed grant; requires restore lock.

    This is called by the trusted backend after the systemctl start transaction
    completes (successfully or not). It never clears SQLite restore intent.
    """
    encoded = _grant(grant)
    directory = _directory(db)
    target = directory / MAILBOX_NAME
    try:
        fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    except FileNotFoundError:
        return False
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise MailboxError('Untrusted restoration mailbox')
        raw = os.read(fd, 34)
    finally:
        os.close(fd)
    if raw != encoded:
        return False
    target.unlink()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version='tensor-gpu-restore-mailbox stage2f-source-only')
    parser.parse_args()
    print(json.dumps({'mode': 'source-only', 'production_control_enabled': False,
                      'note': 'Library interface only; no service or GPU operations'}, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
