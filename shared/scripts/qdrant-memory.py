#!/usr/bin/env python3
"""Qdrant memory inbox and controlled dispatcher for existing Nexus indexers.

Purpose: let the owner drop UTF-8 .md/.txt files into a local inbox and index
those passages using tensor's Ollama and Nexus's existing Qdrant collection.
Inputs: inbox at ~/qdrant-inbox; optional file or source name (ops/nexus/tensor/
obsidian); local indexers beside this script; existing private Qdrant endpoint.
Outputs: source-linked origin=manual_inbox points and diagnostics. The separate
sync-hermes command indexes conservatively filtered, historical main-profile
compaction findings as origin=hermes_session; it never prunes other origins.
Deletion: inbox reconciliation prunes stale manual_inbox points only, with
empty-inbox and mass-purge guards. No secrets are intentionally emitted to logs.

Credential detection is heuristic and not a comprehensive secrets scanner.
Only put reviewed, non-sensitive text into the inbox; Qdrant stores text payloads.
"""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import uuid
from collections import Counter
from urllib.request import Request, urlopen

# The remote receiver also imports this file directly via importlib.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from heading_chunk_filter import merge_heading_only_chunks

HOME = Path('/home/iragonforce')
INBOX = Path(os.environ.get('QDRANT_MEMORY_INBOX', str(HOME / 'qdrant-inbox')))
STATE = Path(os.environ.get('QDRANT_MEMORY_STATE', str(HOME / '.local/state/qdrant-memory')))
INDEXERS = Path(os.environ.get('QDRANT_MEMORY_INDEXERS', str(HOME / 'ops/shared/scripts')))
QDRANT = os.environ.get('QDRANT_MEMORY_QDRANT', 'http://127.0.0.1:6333')
OLLAMA = os.environ.get('QDRANT_MEMORY_OLLAMA', 'http://192.168.1.3:11434')
COLLECTION = 'qdrant_memory'
MODEL = 'qwen3-embedding:8b-fp16'
ORIGIN = 'manual_inbox'
DIMENSIONS = 4096
MAX_FILE_BYTES = 256 * 1024
MAX_CHARS = 2200
BATCH = 3
MARKER = '.qdrant-memory-inbox-v1'
ALLOWED_SUFFIXES = {'.md', '.txt'}
SENSITIVE_NAME = re.compile(r'(?i)(^\.env(?:\.|$)|(?:^|[_.-])(?:secret|token|password|credential|private.?key)(?:[_.-]|$)|\.(?:pem|key|p12|pfx)$)')
SENSITIVE = re.compile(
    r'-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----|'
    r'(?i:Authorization\s*:\s*(?:Bearer|Basic)\s+[^\s"\']+)|'
    r'(?i:\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|'
    r'AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{24,}|xox[baprs]-[A-Za-z0-9-]{20,}))|'
    r'(?im:^\s*(?:(?:export\s+)?[A-Za-z_][A-Za-z0-9_-]*'
    r'(?:TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY|ACCESS_KEY|CLIENT_SECRET)'
    r'[A-Za-z0-9_-]*\s*[:=]\s*|'
    r'(?:password|api[_-]?key|client[_-]?secret|access[_-]?token|private[_-]?key)'
    r'\s*:\s*)["\']?[^\s#"\'${}][^\s#"\']{7,})'
)


def request(url, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    req = Request(url, data=body,
                  method=method or ('POST' if body is not None else 'GET'),
                  headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=150) as res:
        return json.load(res)


def count_origin(origin):
    result = request(f'{QDRANT}/collections/{COLLECTION}/points/count', {
        'filter': {'must': [{'key': 'origin', 'match': {'value': origin}}]},
        'exact': True,
    })
    return result['result']['count']


def verify_collection():
    info = request(f'{QDRANT}/collections/{COLLECTION}')['result']
    config = info['config']['params']['vectors']
    if config.get('size') != DIMENSIONS or config.get('distance') != 'Cosine':
        raise RuntimeError('STOP: unexpected Qdrant vector dimensions/distance')
    if info.get('status') != 'green':
        raise RuntimeError(f'STOP: Qdrant collection is not green: {info.get("status")}')


def existing_points(origin=ORIGIN):
    output, offset = {}, None
    while True:
        req = {
            'limit': 256,
            'with_payload': ['content_sha256', 'source'],
            'with_vector': False,
            'filter': {'must': [{'key': 'origin', 'match': {'value': origin}}]},
        }
        if offset is not None:
            req['offset'] = offset
        page = request(f'{QDRANT}/collections/{COLLECTION}/points/scroll', req)['result']
        for item in page['points']:
            output[str(item['id'])] = item.get('payload', {})
        offset = page.get('next_page_offset')
        if offset is None:
            return output


def init_inbox():
    INBOX.mkdir(mode=0o700, parents=True, exist_ok=True)
    if INBOX.is_symlink() or not INBOX.is_dir():
        raise RuntimeError('STOP: inbox must be a real directory')
    os.chmod(INBOX, 0o700)
    marker = INBOX / MARKER
    if marker.is_symlink():
        raise RuntimeError('STOP: inbox marker must not be a symlink')
    if not marker.exists():
        with marker.open('x', encoding='utf-8') as out:
            out.write('Qdrant manual inbox v1; text files are indexed into qdrant_memory.\n')
        os.chmod(marker, 0o600)
    print(f'PASS: inbox ready: {INBOX}')


def check_inbox():
    if INBOX.is_symlink() or not INBOX.is_dir() or (INBOX / MARKER).is_symlink() or not (INBOX / MARKER).is_file():
        raise RuntimeError(f'STOP: inbox missing or not initialized: {INBOX} (run: qdrant-memory init)')
    if not stat.S_ISDIR(INBOX.stat().st_mode):
        raise RuntimeError('STOP: inbox not a directory')
    if INBOX.stat().st_uid != os.geteuid():
        raise RuntimeError('STOP: inbox not owned by invoking user')
    if INBOX.stat().st_mode & 0o077:
        raise RuntimeError('STOP: inbox permissions are too broad; expected 0700')


def resolve_file(name):
    supplied = Path(name)
    if supplied.is_absolute():
        target = supplied
    elif len(supplied.parts) == 1 and supplied.name not in ('', '.', '..'):
        target = INBOX / supplied
    else:
        raise RuntimeError('STOP: relative file names must be direct children of the inbox')
    if target.parent != INBOX or target.name in ('', '.', '..', MARKER):
        raise RuntimeError('STOP: only direct inbox files are eligible')
    return target


def read_text(path):
    if path.name == MARKER or path.name.startswith('.') or path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError('not an eligible .md/.txt file')
    if SENSITIVE_NAME.search(path.name):
        raise ValueError('filename suggests credential material')
    if path.is_symlink():
        raise ValueError('symlink not allowed')
    # O_NOFOLLOW plus fstat ensure a symbolic link or FIFO cannot be followed.
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('not a regular file')
        if before.st_size > MAX_FILE_BYTES:
            raise ValueError(f'file exceeds {MAX_FILE_BYTES} bytes')
        with os.fdopen(fd, 'rb', closefd=False) as src:
            content = src.read(MAX_FILE_BYTES + 1)
        if len(content) > MAX_FILE_BYTES or b'\0' in content:
            raise ValueError('oversized or binary data')
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError as e:
            raise ValueError('not valid UTF-8') from e
        # A short stability interval avoids indexing a partially copied file.
        time.sleep(0.2)
        after = path.stat(follow_symlinks=False)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        ):
            raise RuntimeError('file changed while reading; retry next sync')
        if SENSITIVE.search(text):
            raise ValueError('suspected credential; excluded')
        return text
    finally:
        os.close(fd)


def _original_chunks(path, text):
    """Heading-aware chunks, deterministic UUIDs and provenance per passage."""
    heading = path.stem
    buffer, size, start, end, ordinal = [], 0, 1, 1, 0

    def emit():
        nonlocal buffer, size, ordinal
        raw = ''.join(buffer)
        buffer, size = [], 0
        if not raw.strip():
            return None
        payload = {
            'origin': ORIGIN,
            'source': f'qdrant-inbox/{path.name}',
            'file_path': path.name,
            'heading': heading,
            'line_start': start,
            'line_end': end,
            'text': raw,
            'kind': 'user_supplied_text',
            'authority': 'user_supplied_unverified',
            'content_sha256': hashlib.sha256((heading + '\n' + str(start) + '\n' + raw).encode()).hexdigest(),
        }
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f'{ORIGIN}:{path.name}:{ordinal}'))
        ordinal += 1
        return point_id, payload

    for lineno, original in enumerate(text.splitlines(keepends=True), 1):
        if path.suffix.lower() == '.md':
            match = re.match(r'^#{1,6}\s+(.+)', original)
            if match:
                item = emit()
                if item is not None:
                    yield item
                heading = match.group(1).strip()
        line = original
        while line:
            if not buffer:
                start = lineno
            take = MAX_CHARS - size
            part, line = line[:take], line[take:]
            buffer.append(part)
            size += len(part)
            end = lineno
            if size == MAX_CHARS:
                item = emit()
                if item is not None:
                    yield item
    item = emit()
    if item is not None:
        yield item


def chunks(path, text):
    yield from merge_heading_only_chunks(_original_chunks(path, text), MAX_CHARS)


def source_records(specific=None):
    check_inbox()
    candidates = [specific] if specific else sorted(INBOX.iterdir())
    records = []
    selected = 0
    skipped = 0
    for file in candidates:
        if file is None or file.name == MARKER:
            continue
        if not file.exists() and not file.is_symlink():
            if specific:
                # Deletions of previously indexed files are reconciled below.
                continue
            raise RuntimeError(f'STOP: file vanished during inventory: {file.name}')
        if not file.is_file() or file.is_symlink() or file.name.startswith('.') or file.suffix.lower() not in ALLOWED_SUFFIXES:
            skipped += 1
            continue
        try:
            text = read_text(file)
        except ValueError as exc:
            print(f'EXCLUDED {file.name}: {exc}', flush=True)
            skipped += 1
            continue
        selected += 1
        records.extend(chunks(file, text))
    return records, selected, skipped


def upsert(records):
    for start in range(0, len(records), BATCH):
        batch = records[start:start + BATCH]
        inputs = [f'Source: {p["source"]}\nHeading: {p["heading"]}\n{p["text"]}' for _, p in batch]
        embeddings = request(f'{OLLAMA}/api/embed', {
            'model': MODEL,
            'input': inputs,
            'keep_alive': '10m',
        })['embeddings']
        if len(embeddings) != len(batch) or any(len(v) != DIMENSIONS for v in embeddings):
            raise RuntimeError('STOP: unexpected Ollama embedding dimensions/count')
        result = request(f'{QDRANT}/collections/{COLLECTION}/points?wait=true', {
            'points': [
                {'id': pid, 'vector': vector, 'payload': payload}
                for (pid, payload), vector in zip(batch, embeddings)
            ]
        }, method='PUT')
        if result.get('status') != 'ok':
            raise RuntimeError('STOP: Qdrant rejected upsert')
        print(f'upserted={start + len(batch)}/{len(records)}', flush=True)


def delete_stale(ids):
    for start in range(0, len(ids), 100):
        result = request(f'{QDRANT}/collections/{COLLECTION}/points/delete?wait=true', {
            'points': ids[start:start + 100]
        })
        if result.get('status') != 'ok':
            raise RuntimeError('STOP: Qdrant refused stale-point deletion')


def update_inbox(specific=None, dry_run=False, allow_empty=False):
    records, files, excluded = source_records(specific)
    if len(records) > 5000:
        raise RuntimeError('STOP: more than 5000 inbox passages; review before indexing')
    if len(records) != len({pid for pid, _ in records}):
        raise RuntimeError('STOP: duplicate inbox point IDs')
    print(f'INBOX files={files} excluded={excluded} passages={len(records)} mode={"dry-run" if dry_run else "apply"}', flush=True)
    if dry_run:
        print('DRY RUN: no embeddings or Qdrant writes', flush=True)
        return
    verify_collection()
    existing = existing_points()
    if specific:
        source = f'qdrant-inbox/{specific.name}'
        existing = {pid: p for pid, p in existing.items() if p.get('source') == source}
    desired = {pid for pid, _ in records}
    stale = sorted(set(existing) - desired)
    changed = [(pid, p) for pid, p in records if existing.get(pid, {}).get('content_sha256') != p['content_sha256']]
    print(f'existing={len(existing)} changed/new={len(changed)} stale={len(stale)}', flush=True)
    if not specific and len(existing) and not files and not allow_empty:
        raise RuntimeError('STOP: inbox is empty; refusing to remove all records without --allow-empty')
    max_prune = max(25, len(existing) // 10)
    if len(stale) > max_prune and not allow_empty:
        raise RuntimeError(f'STOP: {len(stale)} stale points exceeds safe pruning threshold {max_prune}')
    upsert(changed)
    if stale:
        delete_stale(stale)
    after = existing_points()
    if specific:
        after = {pid: p for pid, p in after.items() if p.get('source') == f'qdrant-inbox/{specific.name}'}
    if set(after) != desired:
        raise RuntimeError(f'STOP: expected {len(desired)} inbox records for selected scope; found {len(after)}')
    print(f'PASS: inbox indexed {len(desired)} passages; removed {len(stale)} obsolete manual_inbox points', flush=True)


def subprocess_index(cmd, dry_run):
    print('RUN:', ' '.join(str(p) for p in cmd), flush=True)
    subprocess.run(cmd, check=True)


def update_ops(dry_run):
    indexer = INDEXERS / 'homelab-index-ops.py'
    spec = importlib.util.spec_from_file_location('qdrant_ops_indexer', indexer)
    if not spec or not spec.loader:
        raise RuntimeError(f'STOP: could not read indexer {indexer}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.COLLECTION != COLLECTION or module.QDRANT != QDRANT:
        raise RuntimeError('STOP: ops indexer Qdrant collection/endpoint differs from memory configuration')
    if not dry_run:
        verify_collection()
        old = existing_points('ops')
        new_ids = {pid for pid, _ in module.chunks(HOME / 'ops')}
        if not new_ids:
            raise RuntimeError('STOP: ops chunk scan empty')
        stale = set(old) - new_ids
        threshold = max(25, len(old) // 10)
        print(f'ops preflight: existing={len(old)} desired={len(new_ids)} stale={len(stale)} max_stale={threshold}')
        if len(stale) > threshold:
            raise RuntimeError('STOP: ops indexer would delete too many previous points; review before applying')
    subprocess_index([sys.executable, '-u', str(indexer), '--dry-run' if dry_run else '--apply'], dry_run)


def update_repo(source, dry_run):
    subprocess_index([
        sys.executable, '-u', str(INDEXERS / 'git-snapshot-index.py'),
        '--dry-run' if dry_run else '--apply', '--repo', source,
    ], dry_run)


def update_obsidian(dry_run):
    subprocess_index([
        sys.executable, '-u', str(INDEXERS / 'obsidian-index.py'),
        '--dry-run' if dry_run else '--apply',
    ], dry_run)


def lock():
    if STATE.is_symlink():
        raise RuntimeError('STOP: state directory must not be a symlink')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    if STATE.stat().st_uid != os.geteuid():
        raise RuntimeError('STOP: state directory owner differs')
    os.chmod(STATE, 0o700)
    fd = os.open(STATE / 'index.lock', os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise RuntimeError('STOP: another qdrant-memory update is running')
    return fd


def show_status():
    verify_collection()
    for origin in ('ops', 'git_history', 'obsidian_history', 'git_repo_snapshot', ORIGIN, 'hermes_session'):
        print(f'{origin}: {count_origin(origin)}')
    print(f'inbox: {INBOX}')


def load_exporter():
    path = INDEXERS / 'hermes-compaction-export.py'
    spec = importlib.util.spec_from_file_location('hermes_compaction_export', path)
    if not spec or not spec.loader:
        raise RuntimeError('STOP: missing Hermes compaction exporter')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checkpoint_read():
    path = STATE / 'hermes-compaction-checkpoint.json'
    if path.is_symlink():
        raise RuntimeError('STOP: checkpoint symlink')
    if not path.exists():
        return {'version': 1, 'processed': {}}
    if path.stat().st_mode & 0o077 or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise RuntimeError('STOP: checkpoint permissions too broad')
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('version') not in (1, 2) or not isinstance(value.get('processed'), dict):
        raise RuntimeError('STOP: incompatible checkpoint')
    if any(not isinstance(k, str) or type(v) not in (str, int)
           for k, v in value['processed'].items()):
        raise RuntimeError('STOP: invalid checkpoint entries')
    if value['version'] == 2 and value.get('sha256') != checkpoint_hash(value['processed']):
        raise RuntimeError('STOP: checkpoint integrity mismatch')
    return value


def checkpoint_hash(processed):
    return hashlib.sha256(json.dumps(processed, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def checkpoint_write(value):
    path = STATE / 'hermes-compaction-checkpoint.json'
    tmp = STATE / 'hermes-compaction-checkpoint.tmp'
    value['version'] = 2
    value['sha256'] = checkpoint_hash(value['processed'])
    if tmp.exists() or tmp.is_symlink():
        info = tmp.lstat()
        if tmp.is_symlink() or not tmp.is_file() or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise RuntimeError('STOP: unsafe interrupted checkpoint staging file')
        # The exclusive process lock proves this is an orphan of a killed run.
        tmp.unlink()
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        directory = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if tmp.exists():
            tmp.unlink()


def sync_hermes(dry_run=False, limit=None):
    """Idempotent main-profile reconciliation; no implicit deletion or DB writes."""
    exporter = load_exporter()
    database = Path(os.environ.get('QDRANT_MEMORY_HERMES_DB', '/opt/data/state.db'))
    repository = Path(os.environ.get('QDRANT_MEMORY_OPS', '/opt/data/workspace/ops'))
    if database.is_symlink() or not database.is_file():
        raise RuntimeError('STOP: main Hermes session database missing or linked')
    if not (repository / '.git').exists():
        raise RuntimeError('STOP: public ops checkout missing')
    _, candidates = exporter.fetch_candidates(database, strict=False)
    scanner_path = INDEXERS / 'git-snapshot-index.py'
    scanner_spec = importlib.util.spec_from_file_location('git_snapshot_scanner', scanner_path)
    if scanner_spec is None or scanner_spec.loader is None:
        raise RuntimeError('STOP: missing Git credential scanner')
    scanner = importlib.util.module_from_spec(scanner_spec)
    scanner_spec.loader.exec_module(scanner)
    scanners = (SENSITIVE, scanner.SENSITIVE)
    dates = exporter.observation_dates(database)
    if dry_run:
        checkpoint = {'version': 1, 'processed': {}}
        existing = {}
    else:
        verify_collection()
        checkpoint = checkpoint_read()
        existing = existing_points('hermes_session')
    counts = Counter()
    seen = {p.get('content_sha256') for p in existing.values()}
    for parent, child, message_id, content in candidates[:limit]:
        records, rejected = exporter.build_findings((parent, child, message_id, content), repository, scanners)
        counts.update(rejected)
        fresh = []
        for pid, payload in records:
            payload['observed_at'] = dates.get(parent)
            if payload['content_sha256'] in seen and pid not in existing:
                counts['duplicate'] += 1
                continue
            seen.add(payload['content_sha256'])
            if existing.get(pid, {}).get('content_sha256') != payload['content_sha256']:
                fresh.append((pid, payload))
        counts['eligible'] += len(records)
        counts['new_or_changed'] += len(fresh)
        if not dry_run:
            upsert(fresh)
            if fresh:
                observed = existing_points('hermes_session')
                if any(observed.get(pid, {}).get('content_sha256') != payload['content_sha256']
                       for pid, payload in fresh):
                    raise RuntimeError('STOP: Hermes point readback differs; checkpoint not advanced')
            for pid, payload in fresh:
                existing[pid] = payload
            checkpoint['processed'][parent] = message_id
            checkpoint_write(checkpoint)
        counts['processed'] += 1
    print('HERMES ' + ' '.join(f'{k}={v}' for k, v in sorted(counts.items())), flush=True)
    if dry_run:
        print('DRY RUN: no embeddings, Qdrant writes or checkpoint writes', flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init', help='Initialize the private watched inbox with a marker')
    sub.add_parser('status', help='Display Qdrant point counts by origin')
    hermes_parser = sub.add_parser('sync-hermes', help='Reconcile historical main-profile compaction findings')
    hermes_parser.add_argument('--dry-run', action='store_true')
    hermes_parser.add_argument('--limit', type=int, help='Pilot only the first N completed compactions')
    inbox_parser = sub.add_parser('sync-inbox', help='Reconcile the entire inbox; including deletions')
    inbox_parser.add_argument('--dry-run', action='store_true')
    inbox_parser.add_argument('--allow-empty', action='store_true', help='Explicitly allow an emptied inbox / large prune')
    update_parser = sub.add_parser('update', help='Index one inbox file or named source')
    update_parser.add_argument('target', help='inbox filename/path, ops, nexus, tensor, obsidian, or all')
    update_parser.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    if args.cmd == 'init':
        init_inbox()
        return
    if args.cmd == 'status':
        show_status()
        return
    if args.cmd == 'sync-hermes' and args.dry_run:
        sync_hermes(dry_run=True, limit=args.limit)
        return
    if args.cmd == 'sync-inbox' and args.dry_run:
        update_inbox(dry_run=True, allow_empty=args.allow_empty)
        return
    if args.cmd == 'update' and args.dry_run:
        run_update(args.target, dry_run=True)
        return
    with os.fdopen(lock(), 'r+') as _held_lock:
        if args.cmd == 'sync-inbox':
            update_inbox(allow_empty=args.allow_empty)
        elif args.cmd == 'sync-hermes':
            sync_hermes(limit=args.limit)
        elif args.cmd == 'update':
            run_update(args.target, dry_run=False)


def run_update(target, dry_run):
    if target == 'ops':
        update_ops(dry_run)
    elif target in ('nexus', 'tensor'):
        update_repo(target, dry_run)
    elif target == 'obsidian':
        update_obsidian(dry_run)
    elif target == 'all':
        update_ops(dry_run)
        for name in ('nexus', 'tensor'):
            update_repo(name, dry_run)
        update_obsidian(dry_run)
        update_inbox(dry_run=dry_run)
    else:
        update_inbox(specific=resolve_file(target), dry_run=dry_run)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print(f'ERROR: {error}', file=sys.stderr, flush=True)
        sys.exit(1)
