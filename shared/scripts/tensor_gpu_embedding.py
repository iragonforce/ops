#!/usr/bin/env python3
"""Protected Tensor embedding handoff for existing Nexus writers.

Usage: tensor_gpu_embedding.py --help. Dependencies: Python stdlib and the
existing tensor-gpu-queue.py, tensor-gpu-lease.py and
tensor-gpu-systemd-adapter.py. The worker is one transient systemd job while
pending work exists; no persistent daemon or free-running GPU request.
The submit/result CLI is intended for a pinned SSH command, never a public HTTP
listener. Private payloads and vectors stay outside Git and the queue database.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from urllib.request import ProxyHandler, Request, build_opener

MODULE = Path(__file__).with_name('tensor-gpu-queue.py')
spec = importlib.util.spec_from_file_location('tensor_gpu_queue', MODULE)
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)
Queue = queue_module.Queue
QueueError = queue_module.QueueError
MODEL = 'qwen3-embedding:8b-fp16'
REVISION = 'qdrant-embed-v1-qwen3-8b-fp16-source-heading'
DIMENSIONS = 4096
MAX_INPUTS = 3
MAX_INPUT_CHARS = 8000
MAX_WIRE_BYTES = 48000
MAX_RESULT_BYTES = 1024 * 1024
WORKER_UNIT = 'tensor-gpu-embedding-worker'
STANDBY_COMMAND = Path.home() / '.local/bin/hibernate'
DB = Path(os.environ.get('TENSOR_GPU_EMBED_DB', str(queue_module.DEFAULT_DIR / 'queue.sqlite3')))


class HandoffError(RuntimeError):
    """Fail closed without disclosing protected batch text or vectors."""


def canonical(inputs):
    if (not isinstance(inputs, list) or not 1 <= len(inputs) <= MAX_INPUTS
            or any(not isinstance(s, str) or not s or len(s) > MAX_INPUT_CHARS for s in inputs)):
        raise HandoffError('Invalid embedding batch')
    return json.dumps({'model': MODEL, 'inputs': inputs}, ensure_ascii=False,
                      sort_keys=True, separators=(',', ':')).encode('utf-8')


def digest(inputs):
    return hashlib.sha256(canonical(inputs)).hexdigest()


def private_file(directory, name, data):
    """Write-once durable file; reject links/foreign ownership and weak modes."""
    path = directory / name
    if len(data) > MAX_RESULT_BYTES or path.is_symlink():
        raise HandoffError('Invalid protected handoff file')
    old = os.umask(0o077)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        dirfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        os.umask(old)
    return path


def read_private(directory, name):
    if not isinstance(name, str) or not queue_module.TOKEN.fullmatch(name):
        raise HandoffError('Invalid handoff reference')
    path = directory / name
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if (not __import__('stat').S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_mode & 0o077 or info.st_size > MAX_RESULT_BYTES):
            raise HandoffError('Unsafe protected handoff file')
        with os.fdopen(fd, 'rb', closefd=False) as src:
            return src.read(MAX_RESULT_BYTES + 1)
    finally:
        os.close(fd)


def submit(db, inputs):
    encoded = canonical(inputs)
    if len(encoded) > MAX_WIRE_BYTES:
        raise HandoffError('Oversized embedding batch')
    with Queue(db) as queue:
        ref = 'payload-' + uuid.uuid4().hex
        path = private_file(db.parent, ref, encoded)
        try:
            job_id, created = queue.submit_typed('embedding_batch', REVISION, digest(inputs), ref)
        except BaseException:
            path.unlink()
            raise
        if not created:
            path.unlink()
            row = queue.db.execute('SELECT payload_ref FROM jobs WHERE id=?', (job_id,)).fetchone()
            if row is None or read_private(db.parent, row['payload_ref']) != encoded:
                raise HandoffError('Existing batch payload mismatch')
        return job_id


def result(db, job_id):
    try:
        if str(uuid.UUID(job_id)) != job_id:
            raise ValueError('invalid ID')
    except (ValueError, TypeError):
        raise HandoffError('Invalid job ID') from None
    with Queue(db) as queue:
        row = queue.db.execute('SELECT kind,state,operation_revision,input_digest,result_ref FROM jobs WHERE id=?',
                               (job_id,)).fetchone()
        if row is None or row['kind'] != 'embedding_batch' or row['operation_revision'] != REVISION:
            raise HandoffError('Unknown embedding job')
        if row['state'] in ('failed', 'cancelled'):
            raise HandoffError('Embedding batch unavailable; reconcile before retry')
        if row['state'] != 'completed':
            raise HandoffError('Embedding batch not completed')
        data = json.loads(read_private(db.parent, row['result_ref']))
        if (set(data) != {'revision', 'digest', 'vectors'} or data['revision'] != REVISION
                or data['digest'] != row['input_digest']):
            raise HandoffError('Result integrity mismatch')
        validate_vectors(data['vectors'])
        return data


def validate_vectors(vectors, expected=None):
    if (not isinstance(vectors, list) or not 1 <= len(vectors) <= MAX_INPUTS
            or (expected is not None and len(vectors) != expected)
            or any(not isinstance(v, list) or len(v) != DIMENSIONS
                   or any(type(x) not in (int, float) or not __import__('math').isfinite(x) for x in v)
                   for v in vectors)):
        raise HandoffError('Invalid embedding vectors')


def run_admitted(db, claim, embed):
    """Execute one *externally admitted* claim with a caller-supplied Ollama API.

    No admission is inferred from claim(activity='idle'). The caller must hold
    a verified GPU lease through return; failure never advances a writer cursor.
    """
    with Queue(db) as queue:
        row = queue.db.execute('SELECT * FROM jobs WHERE id=?', (claim['id'],)).fetchone()
        if (row is None or row['kind'] != 'embedding_batch' or row['state'] != 'running'
                or row['lease_token'] != claim['lease_token'] or row['attempts'] != claim['attempt']
                or row['lease_until'] is None or row['lease_until'] <= time.time()
                or row['operation_revision'] != REVISION):
            raise HandoffError('Invalid embedding claim')
        inputs = json.loads(read_private(db.parent, row['payload_ref']))
        if set(inputs) != {'model', 'inputs'} or inputs['model'] != MODEL or digest(inputs['inputs']) != row['input_digest']:
            raise HandoffError('Embedding input integrity mismatch')
        ref = 'result-' + uuid.uuid4().hex
        try:
            vectors = embed(inputs['inputs'], MODEL)
            validate_vectors(vectors, len(inputs['inputs']))
            data = json.dumps({'revision': REVISION, 'digest': row['input_digest'], 'vectors': vectors},
                              allow_nan=False, separators=(',', ':')).encode()
            private_file(db.parent, ref, data)
            queue.finish(row['id'], row['lease_owner'], attempt=claim['attempt'],
                         lease_token=claim['lease_token'], result_ref=ref)
        except Exception:
            (db.parent / ref).unlink(missing_ok=True)
            try:
                queue.finish(row['id'], row['lease_owner'], attempt=claim['attempt'],
                             lease_token=claim['lease_token'], error='embedding_failed')
            except QueueError:
                pass  # Lease expired: recovery controls the next attempt.
            raise HandoffError('Embedding attempt failed; queued retry retained') from None


def _module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    if spec is None or spec.loader is None:
        raise HandoffError('GPU admission component unavailable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _identity(lease):
    pid = os.getpid()
    stat = (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()
    return lease.OwnerIdentity(Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                               pid, int(stat[19]))


def _idle():
    try:
        check = subprocess.run([str(STANDBY_COMMAND), 'status'], capture_output=True,
                               text=True, timeout=5, check=True)
        return check.stdout.strip() == 'visual standby'
    except (OSError, subprocess.SubprocessError):
        return False


def _embed_local(inputs, model):
    encoded = json.dumps({'model': model, 'input': inputs, 'keep_alive': 0}).encode()
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(Request('http://127.0.0.1:11434/api/embed', data=encoded,
                                 headers={'Content-Type': 'application/json'}), timeout=180) as response:
            data = response.read(MAX_RESULT_BYTES + 1)
        if len(data) > MAX_RESULT_BYTES:
            raise HandoffError('Embedding result exceeded bound')
        return json.loads(data)['embeddings']
    except (OSError, ValueError, KeyError):
        raise HandoffError('Ollama embedding unavailable') from None


def _unload_local_model():
    opener = build_opener(ProxyHandler({}))
    for _ in range(20):
        with opener.open('http://127.0.0.1:11434/api/ps', timeout=5) as response:
            resident = [m.get('name') for m in json.loads(response.read(65537)).get('models', [])]
        if MODEL not in resident:
            return
        time.sleep(1)
    # keep_alive=0 requests Ollama to unload when the request finishes. Never
    # force-stop a model potentially shared with an uncoordinated active client.
    raise HandoffError('Embedding model still resident; GPU lease retained')


def _start_worker(db):
    if subprocess.run(['/usr/bin/systemctl', '--user', 'is-active', '--quiet',
                       WORKER_UNIT + '.service'], timeout=5).returncode == 0:
        return
    started = subprocess.run(['/usr/bin/systemd-run', '--user', '--collect', '--unit', WORKER_UNIT,
                              '/usr/bin/python3', str(Path(__file__).resolve()), '--db', str(db), 'worker'],
                             capture_output=True, timeout=10)
    if started.returncode and subprocess.run(['/usr/bin/systemctl', '--user', 'is-active',
                                               '--quiet', WORKER_UNIT + '.service'], timeout=5).returncode:
        raise HandoffError('Embedding worker could not be started; queued job retained')


def worker(db):
    """Drain eligible FIFO batches only in verified visual standby under the shared GPU lease."""
    lease = _module('tensor_gpu_embedding_lease', 'tensor-gpu-lease.py')
    desktop = _module('tensor_gpu_embedding_desktop', 'tensor-gpu-systemd-adapter.py')
    retry_after = 0.0
    with Queue(db) as queue:
        while True:
            queue.recover_stale()
            if time.monotonic() < retry_after:
                time.sleep(min(5, retry_after - time.monotonic()))
            row = queue.db.execute("SELECT id,kind,state,available_at,lease_until FROM jobs "
                                   "WHERE state IN ('pending','retry','running') "
                                   "AND kind IN ('embedding_batch','mineru_pdf') "
                                   "ORDER BY priority DESC,seq LIMIT 1").fetchone()
            if row is None:
                return
            if row['state'] == 'running':
                time.sleep(5)
                continue
            if queue.paused():
                time.sleep(5)
                continue
            if row['kind'] != 'embedding_batch':
                raise HandoffError('Earlier PDF job blocks the FIFO until its native worker is installed')
            if not _idle():
                time.sleep(5)
                continue
            if row['available_at'] > time.time():
                time.sleep(min(5, max(0.1, row['available_at'] - time.time())))
                continue
            with queue_module.worker_lock(db.parent, wait=True):
                if not _idle():
                    continue
                with lease.LeaseManager(db.parent.parent / 'tensor-gpu-lease/queue.sqlite3',
                                        desktop.TensorSleepAwareBackend(),
                                        require_identity=True) as manager:
                    try:
                        token = manager.acquire('embedding-worker', 'ollama:' + MODEL,
                                                activity='idle', identity=_identity(lease))
                    except lease.LeaseError:
                        if manager.status()['mode'] != 'normal':
                            raise HandoffError('Unresolved GPU lifecycle state; job retained') from None
                        retry_after = time.monotonic() + 5
                        continue
                    try:
                        claim = queue.claim('idle', 'embedding-worker', kinds=('embedding_batch',),
                                            lease_seconds=300)
                        if claim is not None:
                            try:
                                run_admitted(db, claim, _embed_local)
                            except HandoffError:
                                pass  # The fenced queue records retry or terminal failure.
                    finally:
                        _unload_local_model()
                        manager.release(token)


def remote_embed(inputs, command, *, timeout=30):
    """Submit over configured SSH argv and wait boundedly; never fall back direct."""
    encoded = canonical(inputs)
    if len(encoded) > MAX_WIRE_BYTES or not command or not isinstance(command, list) or any(
            not isinstance(x, str) or not x for x in command):
        raise HandoffError('Invalid remote embedding command or input')
    def invoke(action, payload=None):
        try:
            proc = subprocess.run([*command, action], input=payload, capture_output=True,
                                  timeout=min(10, timeout), check=False)
            if proc.returncode or len(proc.stdout) > MAX_RESULT_BYTES:
                raise HandoffError('Tensor embedding handoff unavailable')
            return json.loads(proc.stdout)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            raise HandoffError('Tensor embedding handoff unavailable') from None
    job_id = invoke('submit', encoded)['job_id']
    if not isinstance(job_id, str):
        raise HandoffError('Invalid handoff ID')
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        response = invoke('result', job_id.encode())
        if response.get('state') == 'pending':
            time.sleep(min(1, max(0, end - time.monotonic())))
            continue
        if response.get('revision') != REVISION or response.get('digest') != digest(inputs):
            raise HandoffError('Remote result integrity mismatch')
        vectors = response['vectors']
        validate_vectors(vectors, len(inputs))
        return vectors
    raise HandoffError('Embedding queued; writer must retry without checkpoint advance')


def writer_embed(inputs, direct):
    raw = os.environ.get('QDRANT_MEMORY_EMBED_COMMAND')
    if raw is None:
        return direct(inputs)
    try:
        command = json.loads(raw)
        return remote_embed(inputs, command)
    except (ValueError, TypeError, KeyError, HandoffError):
        raise HandoffError('Queued embedding unavailable; writer checkpoint unchanged') from None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--db', type=Path, default=DB)
    sub = ap.add_subparsers(dest='action', required=True)
    sub.add_parser('submit')
    sub.add_parser('result')
    sub.add_parser('worker')
    args = ap.parse_args()
    try:
        if args.action == 'submit':
            raw = sys.stdin.buffer.read(MAX_WIRE_BYTES + 1)
            if len(raw) > MAX_WIRE_BYTES:
                raise HandoffError('Oversized embedding input')
            value = json.loads(raw)
            if set(value) != {'model', 'inputs'} or value['model'] != MODEL:
                raise HandoffError('Invalid embedding schema')
            job_id = submit(args.db, value['inputs'])
            with Queue(args.db) as queue:
                state = queue.db.execute('SELECT state FROM jobs WHERE id=?', (job_id,)).fetchone()['state']
            if state in ('pending', 'retry', 'running'):
                _start_worker(args.db)
            print(json.dumps({'job_id': job_id}))
        elif args.action == 'worker':
            worker(args.db)
        else:
            job_id = sys.stdin.buffer.read(80).decode().strip()
            try:
                print(json.dumps(result(args.db, job_id)))
            except HandoffError as exc:
                if str(exc) != 'Embedding batch not completed':
                    raise
                print('{"state":"pending"}')
        return 0
    except (HandoffError, QueueError, OSError, ValueError, KeyError):
        print('STOP: embedding handoff unavailable', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
