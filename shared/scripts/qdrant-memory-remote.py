#!/usr/bin/env python3
"""Nexus-only SSH transport for qdrant-memory (not a network service).

Purpose: accept size-limited UTF-8 text from qubit/tensor, atomically copy it
into the existing Nexus inbox, and invoke the validated local indexer. Manage
per-host inbox manifests so one host cannot prune other hosts' records.
Also support temporary GitHub repo clones for read-only committed-code indexing.
No listening sockets, credentials, services, or Qdrant collections are added.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid

HOME = Path('/home/iragonforce')
SCRIPTS = HOME / 'ops/shared/scripts'
CORE_FILE = SCRIPTS / 'qdrant-memory.py'
GIT_FILE = SCRIPTS / 'git-snapshot-index.py'
STATE = HOME / '.local/state/qdrant-memory'
INBOX = HOME / 'qdrant-inbox'
HOSTS = ('nexus', 'qubit', 'tensor')
SAFE_NAME = re.compile(r'^(nexus|qubit|tensor)--[A-Za-z0-9._-]{1,95}-[a-f0-9]{12}\.md$')
GIT_REPO = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
MAX_CONTENT = 256 * 1024
MAX_REPO_CHUNKS = 2000
MAX_REPO_BLOBS = 2000
MAX_TOTAL_TEXT = 12 * 1024 * 1024


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f'Indexer missing: {path}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def core_cmd(*args):
    command = [sys.executable, '-u', str(CORE_FILE), *args]
    for attempt in range(8):
        rc = subprocess.run(command, check=False).returncode
        if rc == 0:
            return
        # Another source may have invoked the indexer via Nexus's path unit.
        if rc and attempt < 7:
            time.sleep(2)
    raise RuntimeError(f'Local indexer failed: {" ".join(args)}')


def need_inbox():
    if INBOX.is_symlink() or not INBOX.is_dir() or not (INBOX / '.qdrant-memory-inbox-v1').is_file():
        raise RuntimeError(f'Inbox is missing/uninitialized: {INBOX}')
    if INBOX.stat().st_uid != os.geteuid() or INBOX.stat().st_mode & 0o077:
        raise RuntimeError('Inbox ownership/permissions incorrect')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STATE, 0o700)


def check_name(host, name):
    if host not in HOSTS or not SAFE_NAME.fullmatch(name) or not name.startswith(host + '--'):
        raise RuntimeError('Invalid host-owned inbox filename')
    return INBOX / name


def text_to_markdown(data, original):
    ext = Path(original).suffix.lower()
    if ext in ('.md', '.txt'):
        return data
    # Preserve the original extension and render non-Markdown source as code.
    lang = ext.lstrip('.') or 'text'
    code = data.decode('utf-8')
    return (f'# Imported source: {original}\n\n```{lang}\n{code.rstrip()}\n```\n').encode()


def receive(args):
    need_inbox()
    dst = check_name(args.host, args.name)
    if args.scope not in ('inbox', 'direct'):
        raise RuntimeError('Invalid source scope')
    if Path(args.original).name != args.original or args.original.startswith('.'):
        raise RuntimeError('Invalid original filename')
    base = load(CORE_FILE, 'qdrant_core')
    if base.SENSITIVE_NAME.search(args.original):
        raise RuntimeError('Original filename suggests secret material')
    raw = sys.stdin.buffer.read(MAX_CONTENT + 1)
    if len(raw) > MAX_CONTENT or b'\0' in raw:
        raise RuntimeError('Input exceeds 256 KiB or is binary')
    try:
        raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise RuntimeError('Input must be UTF-8') from exc
    if base.SENSITIVE.search(raw.decode('utf-8')):
        raise RuntimeError('Input resembles credential material; refusing to store')
    content = text_to_markdown(raw, args.original)
    if len(content) > base.MAX_FILE_BYTES or base.SENSITIVE.search(content.decode('utf-8')):
        raise RuntimeError('Wrapped content fails inbox security or size filter')
    if dst.is_symlink():
        raise RuntimeError('Refusing symlink destination')
    if dst.is_file() and dst.read_bytes() == content:
        print(f'UNCHANGED: {dst.name}', flush=True)
    else:
        fd, tmp = tempfile.mkstemp(prefix='.upload-', dir=INBOX)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, 'wb') as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            os.replace(tmp, dst)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        print(f'RECEIVED: {dst.name} ({len(content)} bytes)', flush=True)
    core_cmd('update', dst.name)


def manifest(args):
    need_inbox()
    try:
        supplied = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise RuntimeError('Manifest must be JSON') from exc
    if not isinstance(supplied, dict) or not isinstance(supplied.get('names'), list):
        raise RuntimeError('Manifest missing names array')
    names = supplied['names']
    if len(names) > 200 or not all(isinstance(n, str) for n in names):
        raise RuntimeError('Invalid file count or name')
    if len(names) != len(set(names)):
        raise RuntimeError('Duplicate manifest entries')
    for name in names:
        dst = check_name(args.host, name)
        if dst.is_symlink() or not dst.is_file():
            raise RuntimeError(f'Manifest entry has no matching file: {name}')
    manifest_file = STATE / f'client-manifest-{args.host}.json'
    if manifest_file.is_symlink():
        raise RuntimeError('Refusing symbolic-link manifest')
    previous = set()
    if manifest_file.is_file():
        old = json.loads(manifest_file.read_text(encoding='utf-8'))
        if not isinstance(old, list):
            raise RuntimeError('Corrupt previous manifest')
        for name in old:
            check_name(args.host, name)
        previous = set(old)
    missing = sorted(previous - set(names))
    if missing and not names and not args.allow_empty:
        raise RuntimeError('Refusing to delete all host files; use sync-inbox --allow-empty')
    if len(missing) > max(5, len(previous) // 10) and not args.allow_empty:
        raise RuntimeError(f'Refusing large deletion ({len(missing)} files); review first')
    # Move old host-owned file away, let the validated core indexer reconcile
    # exactly its source records; restore file on indexing failure.
    for name in missing:
        dst = check_name(args.host, name)
        if not dst.is_file() or dst.is_symlink():
            raise RuntimeError(f'Stale source is missing or invalid: {name}')
        fd, backup = tempfile.mkstemp(prefix='.qdrant-deletion-', dir=STATE)
        os.close(fd)
        os.unlink(backup)
        os.replace(dst, backup)
        try:
            core_cmd('update', name)
        except BaseException:
            os.replace(backup, dst)
            raise
        os.unlink(backup)
        print(f'PRUNED host={args.host} file={name}', flush=True)
    fd, tmp = tempfile.mkstemp(prefix='.manifest-', dir=STATE)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(sorted(names), handle, indent=2)
            handle.write('\n')
        os.replace(tmp, manifest_file)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print(f'PASS: manifest for {args.host}: files={len(names)}, removed={len(missing)}')


def clone_repo(slug, dry_run):
    if not GIT_REPO.fullmatch(slug) or '..' in slug:
        raise RuntimeError('Expected GitHub owner/repository')
    if slug.lower() in ('iragonforce/ops', 'iragonforce/nexus', 'iragonforce/tensor'):
        raise RuntimeError('Use qdrant-memory update ops|nexus|tensor for managed repositories')
    git_index = load(GIT_FILE, 'qdrant_git_index')
    base = load(CORE_FILE, 'qdrant_core')
    base.verify_collection()
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.environ.setdefault('GIT_TERMINAL_PROMPT', '0')
    url = 'https://github.com/' + slug + '.git'
    with tempfile.TemporaryDirectory(prefix='qdrant-git-', dir=STATE) as temp:
        checkout = Path(temp) / 'repo'
        env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
        print(f'CLONE (no checkout, no submodules): {slug}', flush=True)
        subprocess.run(['/usr/bin/git', '-c', 'core.hooksPath=/dev/null',
                        '-c', 'protocol.file.allow=never', 'clone', '--no-checkout',
                        '--depth', '1', '--filter=blob:none', '--single-branch',
                        '--no-tags', '--', url, str(checkout)], check=True, env=env, timeout=240)
        commit = git_index.git(checkout, 'rev-parse', 'HEAD').decode().strip()
        branch = git_index.git(checkout, 'symbolic-ref', '--short', 'HEAD').decode().strip()
        entries = [x for x in git_index.git(checkout, 'ls-tree', '-rz', '--full-tree', 'HEAD').split(b'\0') if x]
        if len(entries) > MAX_REPO_BLOBS:
            raise RuntimeError(f'Too many tracked entries ({len(entries)}); maximum {MAX_REPO_BLOBS}')
        records = []
        total_bytes = 0
        counts = {'eligible': 0, 'skipped': 0, 'sensitive': 0}
        for row in entries:
            metadata, sep, pathbytes = row.partition(b'\t')
            if not sep:
                raise RuntimeError('Malformed Git tree record')
            mode, objtype, blob_sha = metadata.decode('ascii').split(' ')
            if objtype != 'blob' or mode == '120000':
                counts['skipped'] += 1
                continue
            rel = pathbytes.decode('utf-8')
            if not git_index.allowed(rel):
                counts['skipped'] += 1
                continue
            data = git_index.git(checkout, 'cat-file', 'blob', blob_sha)
            if len(data) > git_index.MAX_FILE_BYTES or b'\0' in data:
                counts['skipped'] += 1
                continue
            try:
                contents = data.decode('utf-8')
            except UnicodeDecodeError:
                counts['skipped'] += 1
                continue
            if git_index.SENSITIVE.search(contents):
                counts['sensitive'] += 1
                continue
            if not contents.strip():
                counts['skipped'] += 1
                continue
            total_bytes += len(data)
            if total_bytes > MAX_TOTAL_TEXT:
                raise RuntimeError('Repository exceeds 12 MiB eligible text limit')
            counts['eligible'] += 1
            for idx, (start, end, body) in enumerate(git_index.chunk_text(contents)):
                if not body.strip():
                    continue
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL,
                    f'git_repo_ephemeral:{slug}:{rel}:{idx}'))
                records.append((point_id, {
                    'origin': 'git_repo_ephemeral', 'repository': slug,
                    'branch': branch, 'source': f'github/{slug}/{rel}',
                    'file_path': rel, 'language': git_index.language(rel),
                    'line_start': start, 'line_end': end,
                    'text': body, 'content_sha256': hashlib.sha256(body.encode()).hexdigest(),
                    'file_sha256': hashlib.sha256(data).hexdigest(),
                    'git_blob_sha': blob_sha, 'indexed_snapshot_commit': commit,
                    'kind': 'code_or_configuration', 'authority': 'external_snapshot_unverified',
                }))
                if len(records) > MAX_REPO_CHUNKS:
                    raise RuntimeError('Repository exceeds 2000 passage limit')
        if not records:
            raise RuntimeError('No eligible code/configuration passages found')
        print(f'REPO {slug} HEAD={commit[:12]} branch={branch} files={counts["eligible"]} passages={len(records)} sensitive_files_excluded={counts["sensitive"]} skipped={counts["skipped"]}', flush=True)
        if dry_run:
            print('DRY RUN: no embedding or Qdrant writes', flush=True)
            return
        result, offset = {}, None
        while True:
            payload = {'limit': 256, 'with_payload': ['content_sha256', 'file_sha256'],
                       'with_vector': False, 'filter': {'must': [
                           {'key':'origin', 'match':{'value':'git_repo_ephemeral'}},
                           {'key':'repository', 'match':{'value':slug}},
                       ]}}
            if offset is not None:
                payload['offset'] = offset
            data = git_index.request(f'{git_index.QDRANT}/collections/{git_index.COLLECTION}/points/scroll', payload)['result']
            for point in data['points']:
                result[str(point['id'])] = point.get('payload', {})
            offset = data.get('next_page_offset')
            if offset is None:
                break
        todo = [(pid, p) for pid, p in records if result.get(pid, {}).get('content_sha256') != p['content_sha256'] or result.get(pid, {}).get('file_sha256') != p['file_sha256']]
        print(f'EXISTING {len(result)}; NEW_OR_CHANGED {len(todo)}; STALE_RETAINED {len(set(result)-{pid for pid,_ in records})}', flush=True)
        for start in range(0, len(todo), git_index.BATCH):
            batch = todo[start:start + git_index.BATCH]
            git_index.upsert(batch)
            print(f'upserted={start+len(batch)}/{len(todo)}', flush=True)
        print(f'PASS: indexed {len(records)} GitHub passages for {slug}; temporary clone removed at end', flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='action', required=True)
    rec = sub.add_parser('receive')
    rec.add_argument('--host', required=True, choices=HOSTS)
    rec.add_argument('--scope', required=True, choices=['inbox', 'direct'])
    rec.add_argument('--name', required=True)
    rec.add_argument('--original', required=True)
    man = sub.add_parser('manifest')
    man.add_argument('--host', required=True, choices=HOSTS)
    man.add_argument('--allow-empty', action='store_true')
    src = sub.add_parser('update')
    src.add_argument('--source', required=True, choices=['ops','nexus','tensor','obsidian','all'])
    src.add_argument('--dry-run', action='store_true')
    sub.add_parser('status')
    rp = sub.add_parser('repo')
    rp.add_argument('--repo', required=True)
    rp.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    if args.action == 'receive':
        receive(args)
    elif args.action == 'manifest':
        manifest(args)
    elif args.action == 'update':
        core_cmd('update', args.source, *(['--dry-run'] if args.dry_run else []))
    elif args.action == 'status':
        core_cmd('status')
        base = load(CORE_FILE, 'qdrant_core_status')
        print(f'git_repo_ephemeral: {base.count_origin("git_repo_ephemeral")}', flush=True)
    elif args.action == 'repo':
        clone_repo(args.repo, args.dry_run)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError, KeyError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr, flush=True)
        sys.exit(1)
