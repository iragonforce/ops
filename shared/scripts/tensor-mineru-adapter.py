#!/usr/bin/env python3
"""Stage per-PDF MinerU work in the existing Tensor queue (source-only adapter).

Usage: tensor-mineru-adapter.py --help. Requires Python 3.12+, the sibling
queue module and a caller-supplied verified shared GPU admission context and
MinerU conversion callback. This module deliberately has no production CLI
for dispatch and does not submit native API requests by itself.
"""
from __future__ import annotations

import argparse
from contextlib import AbstractContextManager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Callable

_spec = importlib.util.spec_from_file_location("tensor_gpu_queue", Path(__file__).with_name("tensor-gpu-queue.py"))
assert _spec and _spec.loader
_queue = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_queue)
Queue = _queue.Queue
QueueError = _queue.QueueError
worker_lock = _queue.worker_lock
MAX_PDF_BYTES = 128 * 1024 * 1024


def _atomic(path: Path, data: bytes) -> None:
    fd, name = tempfile.mkstemp(prefix=".staging-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
        dirfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class PDFAdapter:
    """Protected payloads and output checkpoints; not a GPU admission policy."""

    def __init__(self, queue: Queue, payload_root: Path, output_root: Path):
        self.queue = queue
        self.root = payload_root
        self.output_root = output_root.resolve()
        if payload_root.is_symlink():
            raise QueueError("Symlink payload root")
        payload_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = payload_root.stat()
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise QueueError("Payload root must be private")

    def _manifest(self, token: str) -> Path:
        _queue._token(token, "payload_ref")
        return self.root / token / "progress.json"

    def _read(self, token: str) -> dict:
        path = self._manifest(token)
        if path.is_symlink() or path.stat().st_mode & 0o077:
            raise QueueError("Insecure progress manifest")
        return json.loads(path.read_text())

    def _write(self, token: str, value: dict) -> None:
        _atomic(self._manifest(token), json.dumps(value, sort_keys=True).encode())

    def submit_files(self, paths: list[Path], revision: str) -> list[tuple[str, bool]]:
        """One durable queue record per PDF, with immutable private input copies."""
        _queue._token(revision, "operation_revision")
        result = []
        for path in paths:
            if path.suffix.lower() != ".pdf" or path.is_symlink():
                raise QueueError("Only regular, non-symlink PDFs can be staged")
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_PDF_BYTES:
                    raise QueueError("PDF source is not regular")
                # Capture bytes before acknowledging submission. A changed input
                # cannot change the queued job after this point.
                with os.fdopen(fd, "rb", closefd=False) as source:
                    content = source.read(MAX_PDF_BYTES + 1)
                if len(content) != info.st_size:
                    raise QueueError("PDF input changed or exceeds size limit")
            finally:
                os.close(fd)
            digest = hashlib.sha256(content).hexdigest()
            token = _queue.typed_idempotency_key("mineru_pdf", revision, digest)
            folder = self.root / token
            folder.mkdir(mode=0o700, exist_ok=True)
            if folder.is_symlink() or folder.stat().st_mode & 0o077:
                raise QueueError("Insecure PDF payload directory")
            staged = folder / "input.pdf"
            if not staged.exists():
                _atomic(staged, content)
            if staged.is_symlink() or hashlib.sha256(staged.read_bytes()).hexdigest() != digest:
                raise QueueError("Staged PDF digest mismatch")
            manifest = self._manifest(token)
            if not manifest.exists():
                self._write(token, {"phase": "staged", "digest": digest, "revision": revision})
            record = self._read(token)
            if record["digest"] != digest or record["revision"] != revision:
                raise QueueError("PDF payload identity changed")
            result.append(self.queue.submit_typed("mineru_pdf", revision, digest, token))
        return result

    def _artifacts(self, root: Path) -> str:
        resolved = root.resolve(strict=True)
        if root.is_symlink() or resolved.parent != self.output_root / "gradio":
            raise QueueError("Result must be a MinerU WebUI run directory")
        for name in ("middle_json.json", "markdown.md", "structured_content.json"):
            item = resolved / name
            if item.is_symlink() or not item.is_file():
                raise QueueError("Incomplete MinerU output")
            with item.open("rb") as stream:
                os.fsync(stream.fileno())  # durable before recording completion
        return resolved.name

    def run_one(self, *, admit: Callable[[], AbstractContextManager],
                convert: Callable[[Path], Path], worker: str = "mineru-adapter",
                lease_seconds: int = 7200) -> str | None:
        """Run one PDF only under a caller-verified shared GPU admission lease.

        `convert` must return the existing WebUI's persisted artifacts.root.
        Its call may POST a native task: a pre-call checkpoint is written and
        *any* crash or exception after that point prohibits automatic replay.
        """
        with worker_lock(self.queue.path.parent), admit():
            job = self.queue.claim("idle", worker, kinds=("mineru_pdf",), lease_seconds=lease_seconds)
            if job is None:
                return None
            token = job["payload_ref"]
            try:
                progress = self._read(token)
                staged = self.root / token / "input.pdf"
                if progress["phase"] != "staged" or hashlib.sha256(staged.read_bytes()).hexdigest() != job["input_digest"]:
                    raise QueueError("PDF is not safe to dispatch")
                self._write(token, {**progress, "phase": "dispatch_unknown"})
                result = convert(staged)
                result_ref = self._artifacts(result)
                self._write(token, {**progress, "phase": "result_persisted", "result_ref": result_ref})
                self.queue.finish(job["id"], worker, attempt=job["attempt"],
                                  lease_token=job["lease_token"], result_ref=result_ref)
                return job["id"]
            except Exception:
                # Exceptions (including unknown POST outcome) are NOT retryable.
                try:
                    self.queue.finish(job["id"], worker, attempt=job["attempt"],
                                      lease_token=job["lease_token"], error="pdf_outcome_unknown")
                except QueueError:
                    pass  # Expired lease is recovered fail-closed by the queue.
                raise

    def reconcile(self, job_id: str) -> str:
        """Complete a failed record only from an already-durable result marker."""
        row = self.queue.db.execute("SELECT kind,state,payload_ref FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None or row["kind"] != "mineru_pdf" or row["state"] != "failed":
            raise QueueError("Only failed PDF records can be reconciled")
        token = row["payload_ref"]
        progress = self._read(token)
        if progress["phase"] != "result_persisted":
            raise QueueError("Unknown native POST/output outcome; investigate manually, never replay")
        result_ref = progress["result_ref"]
        if self._artifacts(self.output_root / "gradio" / result_ref) != result_ref:
            raise QueueError("Result identity mismatch")
        self.queue.reconcile_pdf_result(job_id, token, result_ref)
        return result_ref


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print("Source-only adapter: no live dispatch CLI; inject verified GPU admission and MinerU conversion.")
