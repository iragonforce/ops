"""Notify the existing systemd.path watcher without copying chat content.

Installed only in the default Hermes profile. The hourly Nexus timer recovers
missed notifications; the writer independently verifies a durable close in
read-only SQLite before selecting any text. This hook never touches Qdrant.
"""
from pathlib import Path
import os

from hermes_constants import get_hermes_home

MARKER = Path('/opt/data/state/qdrant-memory/session-close-trigger')


def on_session_finalize(**kwargs):
    if not kwargs.get('session_id') or Path(get_hermes_home()).resolve() != Path('/opt/data'):
        return
    if not MARKER.is_file() or MARKER.is_symlink():
        return
    # PathChanged observes close-after-write; utime() alone is metadata-only
    # and need not wake systemd.path. Keep a single byte, never a transcript.
    fd = os.open(MARKER, os.O_WRONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        os.write(fd, b'1')
    finally:
        os.close(fd)


def register(ctx):
    ctx.register_hook('on_session_finalize', on_session_finalize)
