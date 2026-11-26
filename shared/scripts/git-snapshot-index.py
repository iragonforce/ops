#!/usr/bin/env python3
"""Incrementally index curated Git code/config snapshots into existing Qdrant.

Input: HEAD of clean, local iragonforce/nexus and iragonforce/tensor checkouts.
Output: source-linked code/config passages with origin=git_repo_snapshot.
Purpose: semantic code retrieval without replacing authoritative private ops.

Run --dry-run first. --apply embeds changed/new chunks and upserts them.
Only --apply --prune-stale deletes obsolete points belonging to selected repos;
pruning is forbidden with --only. No Git checkout, source file, or model is altered.
The keyword credential filter is not a comprehensive secrets audit.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tensor_gpu_embedding import writer_embed

GIT = '/usr/bin/git'
QDRANT = 'http://127.0.0.1:6333'
OLLAMA = 'http://192.168.1.3:11434'
COLLECTION = 'qdrant_memory'
MODEL = 'qwen3-embedding:8b-fp16'
DIMENSIONS = 4096
MAX_CHARS = 2200
MAX_FILE_BYTES = 128 * 1024
BATCH = 3
ROOTS = {
    'nexus': Path('/home/iragonforce/src/nexus'),
    'tensor': Path('/home/iragonforce/src/tensor'),
}
ALLOWED_SUFFIXES = {
    '.md', '.py', '.sh', '.bash', '.zsh', '.lua', '.yaml', '.yml', '.json',
    '.jsonc', '.conf', '.service', '.timer', '.socket', '.mount', '.automount',
    '.nft', '.rules', '.exports', '.jq', '.rasi', '.css', '.toml', '.ini',
    '.desktop', '.target', '.path', '.network', '.netdev', '.link', '.xml',
    '.js', '.ts', '.c', '.h', '.rs', '.go', '.sql', '.fish', '.txt',
}
ALLOWED_NAMELESS = {
    'AGENTS.md', 'README.md', 'Caddyfile', 'Dockerfile', 'Makefile', 'fstab',
    'exports', 'sshd_config', 'nfs.conf', 'smb.conf', 'nftables.conf',
    '.bashrc', '.zshrc', '.zprofile', '.profile',
}
BLOCKED_COMPONENTS = {
    '.git', 'node_modules', '.venv', 'venv', '__pycache__', '.cache',
    'backups', 'backup', 'secrets', 'credentials', 'private', 'keys',
    'runtime', 'state', 'logs', 'vendor', 'dist', 'build',
}
BLOCKED_NAME = re.compile(
    r'(?i)(?:^\.env(?:\.|$)|(?:^|[._-])(?:password|credential|secret|private.?key|'
    r'identity|token)(?:[._-]|$)|\.lock$|\.pem$|\.p12$|\.pfx$|\.key$|'
    r'\.crt$|\.cer$|\.pub$|\.sqlite(?:3)?$)'
)
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
STRUCTURAL = re.compile(
    r'^\s*(?:#{1,6}\s+|(?:async\s+)?def\s+|class\s+|'
    r'function\s+|local\s+function\s+|func\s+|'
    r'\[(?:Unit|Service|Install|Timer|Socket|Mount|Network|Match)\]|'
    r'services\s*:|\w[\w-]*\s*:\s*$)'
)


def git(repo_dir, *args):
    process = subprocess.run(
        [GIT, '-C', str(repo_dir), *args],
        capture_output=True, check=True,
    )
    return process.stdout


def request(url, data=None, method=None):
    payload = json.dumps(data).encode() if data is not None else None
    req = Request(
        url, data=payload,
        method=method or ('POST' if payload is not None else 'GET'),
        headers={'Content-Type': 'application/json'},
    )
    with urlopen(req, timeout=150) as response:
        return json.load(response)


def inspect_repo(name):
    root = ROOTS[name]
    if not (root / '.git').exists():
        raise SystemExit(f'STOP: Git checkout missing: {root}')
    branch = git(root, 'branch', '--show-current').decode().strip()
    if branch != 'main':
        raise SystemExit(f'STOP: {name} is on {branch!r}, expected main')
    origin = git(root, 'config', '--get', 'remote.origin.url').decode().strip()
    if not re.search(rf'github\.com[:/]iragonforce/{re.escape(name)}(?:\.git)?/?$', origin):
        raise SystemExit(f'STOP: unexpected origin for {name}')
    changes = git(root, 'status', '--porcelain', '--untracked-files=no')
    if changes:
        raise SystemExit(f'STOP: tracked working-tree changes in {name}; index HEAD only once clean')
    sha = git(root, 'rev-parse', 'HEAD').decode().strip()
    rows = git(root, 'ls-tree', '-rz', '--full-tree', 'HEAD').split(b'\0')
    return root, sha, [row for row in rows if row]


def allowed(path):
    parts = Path(path).parts
    if any(part.lower() in BLOCKED_COMPONENTS for part in parts[:-1]):
        return False
    name = parts[-1]
    if BLOCKED_NAME.search(name) or name == '.gitignore':
        return False
    if name in ALLOWED_NAMELESS or Path(name).suffix.lower() in ALLOWED_SUFFIXES:
        return True
    # Executable extensionless scripts under the public snapshot's approved paths.
    return any(part in ('scripts', 'bin', 'sbin', 'libexec') for part in parts[:-1]) and '.' not in name


def language(path):
    name = Path(path).name
    ext = Path(path).suffix.lower()
    if ext in ('.py',):
        return 'python'
    if ext in ('.lua',):
        return 'lua'
    if ext in ('.sh', '.bash', '.zsh') or name in ('.bashrc', '.zshrc', '.zprofile'):
        return 'shell'
    if ext in ('.yaml', '.yml'):
        return 'yaml'
    if ext in ('.service', '.timer', '.socket', '.mount', '.automount', '.target', '.path'):
        return 'systemd'
    if ext in ('.md',):
        return 'markdown'
    if ext in ('.json', '.jsonc'):
        return 'json'
    return ext.lstrip('.') or 'configuration'


def chunk_text(raw):
    """Line-preserving structural splits, with a strict 2200-char cap."""
    lines = raw.splitlines(keepends=True)
    buf = []
    size = 0
    start = end = 1
    for line_no, line in enumerate(lines, 1):
        if buf and size >= 650 and STRUCTURAL.match(line):
            yield start, end, ''.join(buf)
            buf, size = [], 0
        while line:
            if not buf:
                start = line_no
            free = MAX_CHARS - size
            part, line = line[:free], line[free:]
            buf.append(part)
            size += len(part)
            end = line_no
            if size == MAX_CHARS:
                yield start, end, ''.join(buf)
                buf, size = [], 0
    if buf and ''.join(buf).strip():
        yield start, end, ''.join(buf)


def scan(name, root, commit, rows):
    counts = Counter()
    records = []
    credential_paths = []
    for entry in rows:
        header, separator, name_bytes = entry.partition(b'\t')
        if not separator:
            raise SystemExit(f'STOP: malformed Git tree in {name}')
        mode, obj_type, blob_bytes = header.decode().split(' ')
        if obj_type != 'blob' or mode == '120000':
            counts['not_regular_file'] += 1
            continue
        path = name_bytes.decode('utf-8', errors='strict')
        if not allowed(path):
            counts['not_allowlisted'] += 1
            continue
        blob = blob_bytes
        # Read committed Git content, not a potentially changed working file.
        content = git(root, 'cat-file', 'blob', blob)
        if len(content) > MAX_FILE_BYTES:
            counts['oversize'] += 1
            continue
        if b'\0' in content:
            counts['binary'] += 1
            continue
        try:
            raw = content.decode('utf-8')
        except UnicodeDecodeError:
            counts['non_utf8'] += 1
            continue
        if SENSITIVE.search(raw):
            counts['credential_review'] += 1
            credential_paths.append(path)
            continue
        if not raw.strip():
            counts['empty'] += 1
            continue
        counts['eligible_files'] += 1
        source = f'{name}/{path}'
        file_sha256 = hashlib.sha256(content).hexdigest()
        for ordinal, (start, end, text) in enumerate(chunk_text(raw)):
            if not text.strip():
                continue
            point_id = str(uuid.uuid5(
                uuid.NAMESPACE_URL, f'git_repo_snapshot:iragonforce/{name}:main:{path}:{ordinal}'
            ))
            payload = {
                'origin': 'git_repo_snapshot',
                'repository': f'iragonforce/{name}',
                'branch': 'main',
                'source': source,
                'file_path': path,
                'language': language(path),
                'line_start': start,
                'line_end': end,
                'text': text,
                'content_sha256': hashlib.sha256(text.encode()).hexdigest(),
                'file_sha256': file_sha256,
                'git_blob_sha': blob,
                'indexed_snapshot_commit': commit,
                'kind': 'code_or_configuration',
                'authority': 'snapshot_not_live',
            }
            records.append((point_id, payload))
            counts['passages'] += 1
    counts['git_entries'] = len(rows)
    return counts, records, credential_paths


def existing_points(repo_name):
    result = {}
    offset = None
    while True:
        req = {
            'limit': 256,
            'with_payload': ['content_sha256', 'file_sha256', 'source'],
            'with_vector': False,
            'filter': {'must': [
                {'key': 'origin', 'match': {'value': 'git_repo_snapshot'}},
                {'key': 'repository', 'match': {'value': f'iragonforce/{repo_name}'}}
            ]}
        }
        if offset is not None:
            req['offset'] = offset
        page = request(f'{QDRANT}/collections/{COLLECTION}/points/scroll', req)['result']
        for point in page['points']:
            result[str(point['id'])] = point.get('payload', {})
        offset = page.get('next_page_offset')
        if offset is None:
            return result


def verify_collection():
    info = request(f'{QDRANT}/collections/{COLLECTION}')['result']
    vectors = info['config']['params']['vectors']
    if vectors.get('size') != DIMENSIONS or vectors.get('distance') != 'Cosine':
        raise SystemExit('STOP: Qdrant dimension or distance mismatch')


def upsert(batch):
    prompts = [
        f'Repository: {p["repository"]}\nFile: {p["file_path"]}\nLanguage: {p["language"]}\n{p["text"]}'
        for _, p in batch
    ]
    vectors = writer_embed(prompts, lambda values: request(f'{OLLAMA}/api/embed', {
        'model': MODEL, 'input': values, 'keep_alive': '10m',
    })['embeddings'])
    if len(vectors) != len(batch) or any(len(vector) != DIMENSIONS for vector in vectors):
        raise SystemExit('STOP: embedding vector count/dimensions mismatch')
    reply = request(
        f'{QDRANT}/collections/{COLLECTION}/points?wait=true',
        {'points': [
            {'id': pid, 'vector': vector, 'payload': p}
            for (pid, p), vector in zip(batch, vectors)
        ]}, method='PUT'
    )
    if reply.get('status') != 'ok':
        raise SystemExit('STOP: Qdrant upsert failed')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--apply', action='store_true')
    ap.add_argument('--repo', action='append', choices=tuple(ROOTS),
                    help='Selected repo; repeat, defaults to both')
    ap.add_argument('--only', action='append', default=[], metavar='REPO_RELATIVE_PATH',
                    help='Select a specific tracked file (only with one --repo); repeat')
    ap.add_argument('--prune-stale', action='store_true',
                    help='Explicitly remove stale git_repo_snapshot points (full sync only)')
    args = ap.parse_args()
    repos = list(dict.fromkeys(args.repo or ROOTS))
    if args.only and (len(repos) != 1 or args.prune_stale):
        ap.error('--only requires exactly one --repo and forbids --prune-stale')
    if args.prune_stale and not args.apply:
        ap.error('--prune-stale requires --apply')

    all_records = {}
    print('=== GIT SNAPSHOT SOURCE PREFLIGHT ===', flush=True)
    for repo in repos:
        root, commit, rows = inspect_repo(repo)
        counts, entries, credential_paths = scan(repo, root, commit, rows)
        if args.only:
            selected = set(args.only)
            found = {p['file_path'] for _, p in entries}
            missing = selected - found
            if missing:
                ap.error(f'Files not eligible for indexing: {sorted(missing)}')
            entries = [(pid, payload) for pid, payload in entries
                       if payload['file_path'] in selected]
        if not entries:
            raise SystemExit(f'STOP: {repo} has no eligible passages')
        if len(entries) != len({pid for pid, _ in entries}):
            raise SystemExit(f'STOP: duplicate point IDs in {repo}')
        all_records[repo] = entries
        print(f'{repo}: commit={commit[:12]}; {dict(sorted(counts.items()))}; selected_passages={len(entries)}', flush=True)
        for rel in credential_paths[:20]:
            print(f'  credential_review (excluded): {rel}', flush=True)

    print(f'Collection={COLLECTION}; model={MODEL}; origin=git_repo_snapshot', flush=True)
    if args.dry_run:
        print('DRY RUN: no embeddings or Qdrant writes', flush=True)
        return

    verify_collection()
    for repo in repos:
        records = all_records[repo]
        previous = existing_points(repo)
        desired = {pid for pid, _ in records}
        if args.only:
            sources = {p['source'] for _, p in records}
            previous = {pid: p for pid, p in previous.items() if p.get('source') in sources}
        todo = [(pid, p) for pid, p in records
                if previous.get(pid, {}).get('content_sha256') != p['content_sha256']
                or previous.get(pid, {}).get('file_sha256') != p['file_sha256']]
        stale = sorted(set(previous) - desired)
        print(f'{repo}: existing={len(previous)}, changed/new={len(todo)}, stale={len(stale)}', flush=True)
        for i in range(0, len(todo), BATCH):
            batch = todo[i:i+BATCH]
            upsert(batch)
            print(f'{repo}: upserted={i + len(batch)}/{len(todo)}', flush=True)
        if stale and not args.prune_stale:
            print(f'{repo}: kept {len(stale)} stale points; run a reviewed full --prune-stale sync to delete', flush=True)
        elif stale:
            # Guard against an accidental mass purge caused by a bad source checkout.
            if len(stale) > max(25, len(previous) // 10):
                raise SystemExit(f'STOP: {repo} stale purge exceeds safety threshold ({len(stale)})')
            for i in range(0, len(stale), 100):
                reply = request(f'{QDRANT}/collections/{COLLECTION}/points/delete?wait=true',
                                {'points': stale[i:i+100]})
                if reply.get('status') != 'ok':
                    raise SystemExit('STOP: Qdrant stale-point deletion failed')
            print(f'{repo}: pruned={len(stale)}', flush=True)
        after = existing_points(repo)
        if not desired.issubset(after):
            raise SystemExit(f'STOP: {repo} has missing Qdrant points')
        print(f'PASS: {repo} indexed {len(desired)} selected passages', flush=True)


if __name__ == '__main__':
    main()
