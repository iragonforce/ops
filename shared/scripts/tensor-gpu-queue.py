#!/usr/bin/env python3
"""Durable Tensor GPU job *admission simulator*; Stage 1 never executes GPU work.

Usage: tensor-gpu-queue.py --help
Source of truth: iragonforce/ops; public snapshot target: iragonforce/tensor.

Only synthetic jobs are accepted until request-specific adapters and a trustworthy
idle signal are validated. This deliberately does NOT run arbitrary commands.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
import uuid

SCHEMA_VERSION = 1
DEFAULT_DIR = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "tensor-gpu-queue"
RETRY_BASE_SECONDS = 60
MAX_SOURCE_LEN = 256


class QueueError(Exception):
    """Expected operator/recovery failure with no traceback required."""


def ensure_private_state(db_path: Path) -> None:
    """Reject symlinks, unexpected owners and insecure existing permissions."""
    parent = db_path.parent
    if parent.is_symlink() or db_path.is_symlink():
        raise QueueError("Refusing symlink queue state")
    if not parent.exists():
        parent.mkdir(mode=0o700, parents=True)
    info = parent.stat()
    if not parent.is_dir() or info.st_uid != os.geteuid() or (info.st_mode & 0o077):
        raise QueueError("Queue directory must be owned by the caller and mode 0700")
    if db_path.exists():
        info = db_path.stat()
        if not db_path.is_file() or info.st_uid != os.geteuid() or (info.st_mode & 0o077):
            raise QueueError("Queue database must be caller-owned, regular, mode 0600")


def idempotency_key(kind: str, source: str) -> str:
    # Only synthetic fixture names are accepted in Stage 1. Future real jobs
    # must use a source-content digest + operation/configuration revision.
    return hashlib.sha256((kind + "\0" + source).encode("utf-8")).hexdigest()


class Queue:
    def __init__(self, path: Path):
        self.path = path
        ensure_private_state(path)
        previous = os.umask(0o077)
        try:
            self.db = sqlite3.connect(str(path), timeout=20, isolation_level=None)
        finally:
            os.umask(previous)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=20000")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self._initialize()

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "Queue":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextlib.contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _initialize(self) -> None:
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, SCHEMA_VERSION):
            raise QueueError(f"Unsupported database schema version: {version}")
        with self.transaction():
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT NOT NULL UNIQUE,
                    kind TEXT NOT NULL CHECK(kind = 'synthetic'),
                    source TEXT NOT NULL,
                    dedup_key TEXT NOT NULL UNIQUE,
                    priority INTEGER NOT NULL,
                    state TEXT NOT NULL CHECK(state IN
                        ('pending','retry','running','completed','failed','cancelled')),
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    available_at REAL NOT NULL,
                    lease_owner TEXT,
                    lease_until REAL,
                    last_error TEXT,
                    result_ref TEXT
                )
            """)
            self.db.execute("""
                CREATE INDEX IF NOT EXISTS jobs_ready
                ON jobs(state, available_at, priority DESC, seq)
            """)
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL
                )
            """)
            self.db.execute("INSERT OR IGNORE INTO settings VALUES('paused','0')")
            self.db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

    @staticmethod
    def _check_source(source: str) -> None:
        if not source or len(source) > MAX_SOURCE_LEN or any(ord(c) < 32 for c in source):
            raise QueueError("Synthetic source must contain 1–256 printable characters")

    def submit(self, source: str, priority: int = 0, max_attempts: int = 3, now: float | None = None) -> tuple[str, bool]:
        rows = self.submit_batch([source], priority, max_attempts, now)
        return rows[0]

    def submit_batch(self, sources: list[str], priority: int = 0, max_attempts: int = 3,
                     now: float | None = None) -> list[tuple[str, bool]]:
        if not (-20 <= priority <= 20) or not (1 <= max_attempts <= 10):
            raise QueueError("priority must be -20..20 and max-attempts 1..10")
        if not (1 <= len(sources) <= 1000):
            raise QueueError("Submit 1–1000 synthetic jobs per batch")
        for source in sources:
            self._check_source(source)
        now = time.time() if now is None else now
        result: list[tuple[str, bool]] = []
        with self.transaction():
            for source in sources:
                key = idempotency_key("synthetic", source)
                job_id = str(uuid.uuid4())
                row = self.db.execute("""
                    INSERT INTO jobs (
                        id,kind,source,dedup_key,priority,state,attempts,max_attempts,
                        created_at,updated_at,available_at
                    ) VALUES (?, 'synthetic', ?, ?, ?, 'pending',0,?,?,?,?)
                    ON CONFLICT(dedup_key) DO NOTHING
                    RETURNING id
                """, (job_id, source, key, priority, max_attempts, now, now, now)).fetchone()
                if row is None:
                    existing = self.db.execute("SELECT id FROM jobs WHERE dedup_key=?", (key,)).fetchone()
                    if existing is None:
                        raise QueueError("Deduplication lookup unexpectedly failed")
                    result.append((existing["id"], False))
                else:
                    result.append((row["id"], True))
        return result

    def paused(self) -> bool:
        return self.db.execute("SELECT value FROM settings WHERE key='paused'").fetchone()[0] == "1"

    def set_paused(self, value: bool) -> None:
        with self.transaction():
            self.db.execute("UPDATE settings SET value=? WHERE key='paused'", ("1" if value else "0",))

    def recover_stale(self, now: float | None = None) -> int:
        """Requeue expired ownership; side-effect idempotency is adapter's duty."""
        now = time.time() if now is None else now
        with self.transaction():
            rows = self.db.execute("""
                SELECT id,attempts,max_attempts FROM jobs
                WHERE state='running' AND lease_until<=?
            """, (now,)).fetchall()
            for row in rows:
                failed = row["attempts"] >= row["max_attempts"]
                self.db.execute("""
                    UPDATE jobs SET state=?,updated_at=?,available_at=?,
                        lease_owner=NULL,lease_until=NULL,
                        last_error='Expired worker lease; previous attempt outcome unknown'
                    WHERE id=?
                """, ("failed" if failed else "retry", now,
                      now + RETRY_BASE_SECONDS * 2 ** max(0, row["attempts"] - 1), row["id"]))
            return len(rows)

    def claim(self, activity: str, worker: str, now: float | None = None,
              lease_seconds: int = 300) -> dict | None:
        """Synthetic policy gate: only *explicit simulated* idle admits a job."""
        if activity not in ("active", "idle", "unknown"):
            raise QueueError("Invalid simulated activity")
        if not worker or lease_seconds < 10:
            raise QueueError("Worker identity and lease >=10s required")
        if activity != "idle":
            return None
        now = time.time() if now is None else now
        with self.transaction():
            if self.paused():
                return None
            row = self.db.execute("""
                SELECT id,source,attempts FROM jobs
                WHERE state IN ('pending','retry') AND available_at<=?
                ORDER BY priority DESC, seq ASC LIMIT 1
            """, (now,)).fetchone()
            if row is None:
                return None
            self.db.execute("""
                UPDATE jobs SET state='running', attempts=attempts+1,
                    lease_owner=?,lease_until=?,updated_at=?
                WHERE id=?
            """, (worker, now+lease_seconds, now, row["id"]))
            return dict(row)

    def finish(self, job_id: str, worker: str, now: float | None = None,
               error: str | None = None) -> str:
        now = time.time() if now is None else now
        with self.transaction():
            row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if row is None or row["state"] != "running" or row["lease_owner"] != worker:
                raise QueueError("Job is not running under this worker lease")
            if error is None:
                state = "completed"
                due = now
                result_ref = "synthetic:completed"
                last_error = None
            else:
                state = "retry" if row["attempts"] < row["max_attempts"] else "failed"
                due = now + RETRY_BASE_SECONDS * 2 ** max(0, row["attempts"] - 1)
                result_ref = None
                last_error = error[:512]
            self.db.execute("""
                UPDATE jobs SET state=?, available_at=?, updated_at=?,
                    lease_owner=NULL, lease_until=NULL, result_ref=?, last_error=?
                WHERE id=?
            """, (state, due, now, result_ref, last_error, job_id))
            return state

    def transition(self, job_id: str, operation: str, now: float | None = None) -> str:
        now = time.time() if now is None else now
        with self.transaction():
            row = self.db.execute("SELECT state FROM jobs WHERE id=?", (job_id,)).fetchone()
            if row is None:
                raise QueueError("Unknown job")
            state = row["state"]
            if operation == "cancel" and state in ("pending", "retry", "failed"):
                target = "cancelled"
                self.db.execute("UPDATE jobs SET state=?,updated_at=? WHERE id=?", (target, now, job_id))
            elif operation == "retry" and state == "failed":
                target = "pending"
                self.db.execute("""
                    UPDATE jobs SET state=?,attempts=0,available_at=?,updated_at=?,last_error=NULL
                    WHERE id=?
                """, (target, now, now, job_id))
            else:
                raise QueueError(f"Refusing {operation} for {state} job")
            return target

    def summary(self) -> dict:
        counts = {r["state"]: r["n"] for r in self.db.execute(
            "SELECT state,COUNT(*) AS n FROM jobs GROUP BY state"
        ).fetchall()}
        return {"paused": self.paused(), "counts": counts, "total": sum(counts.values())}

    def list_jobs(self, limit: int = 30) -> list[dict]:
        if not (1 <= limit <= 100):
            raise QueueError("limit must be 1..100")
        rows = self.db.execute("""
            SELECT id,kind,priority,state,attempts,max_attempts,seq
            FROM jobs ORDER BY seq DESC LIMIT ?
        """, (limit,)).fetchall()
        # Source strings, file paths, error details and tokens never printed.
        return [dict(r) for r in rows]


@contextlib.contextmanager
def worker_lock(state_dir: Path):
    lock_path = state_dir / "worker.lock"
    if lock_path.is_symlink():
        raise QueueError("Refusing symlink worker lock")
    old = os.umask(0o077)
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    finally:
        os.umask(old)
    try:
        info = os.fstat(fd)
        if info.st_uid != os.geteuid() or (info.st_mode & 0o077):
            raise QueueError("Insecure worker lock permissions")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise QueueError("Synthetic worker already running") from exc
        yield
    finally:
        os.close(fd)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=DEFAULT_DIR / "queue.sqlite3", help="Private SQLite database path")
    subs = ap.add_subparsers(dest="action", required=True)
    subs.add_parser("status")
    p = subs.add_parser("list")
    p.add_argument("--limit", type=int, default=30)
    p = subs.add_parser("submit")
    p.add_argument("--source", required=True, help="Synthetic fixture ID only; not a document path")
    p.add_argument("--priority", type=int, default=0)
    p.add_argument("--max-attempts", type=int, default=3)
    p = subs.add_parser("submit-batch")
    p.add_argument("--prefix", default="fixture-")
    p.add_argument("--count", type=int, default=30)
    p.add_argument("--priority", type=int, default=0)
    p.add_argument("--max-attempts", type=int, default=3)
    p = subs.add_parser("run-synthetic", help="Explicit no-GPU simulation; unknown/active never claim")
    p.add_argument("--activity", choices=("idle", "active", "unknown"), default="unknown")
    p.add_argument("--limit", type=int, default=30)
    p = subs.add_parser("recover", help="Requeue only expired running leases")
    for action in ("cancel", "retry"):
        p = subs.add_parser(action)
        p.add_argument("job_id")
    subs.add_parser("pause")
    subs.add_parser("resume")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    with Queue(args.db) as queue:
        if args.action == "status":
            print(json.dumps(queue.summary(), sort_keys=True))
        elif args.action == "list":
            print(json.dumps(queue.list_jobs(args.limit), sort_keys=True))
        elif args.action == "submit":
            ident, created = queue.submit(args.source, args.priority, args.max_attempts)
            print(json.dumps({"id": ident, "created": created}))
        elif args.action == "submit-batch":
            if not (1 <= args.count <= 1000):
                raise QueueError("count must be 1..1000")
            rows = queue.submit_batch([f"{args.prefix}{i:04d}" for i in range(1, args.count+1)],
                                      args.priority, args.max_attempts)
            print(json.dumps({"total": len(rows), "created": sum(created for _, created in rows),
                              "reused": sum(not created for _, created in rows)}))
        elif args.action == "run-synthetic":
            if not (1 <= args.limit <= 1000):
                raise QueueError("limit must be 1..1000")
            processed = 0
            with worker_lock(args.db.parent):
                worker = str(uuid.uuid4())
                queue.recover_stale()
                for _ in range(args.limit):
                    row = queue.claim(args.activity, worker)
                    if row is None:
                        break
                    queue.finish(row["id"], worker)
                    processed += 1
            print(json.dumps({"activity_simulated": args.activity, "synthetic_completed": processed}))
        elif args.action == "recover":
            print(json.dumps({"expired_leases_recovered": queue.recover_stale()}))
        elif args.action in ("pause", "resume"):
            queue.set_paused(args.action == "pause")
            print(json.dumps({"paused": queue.paused()}))
        elif args.action in ("cancel", "retry"):
            print(json.dumps({"id": args.job_id, "state": queue.transition(args.job_id, args.action)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (QueueError, sqlite3.Error, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
