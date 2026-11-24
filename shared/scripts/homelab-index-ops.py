#!/usr/bin/env python3
"""Incremental, source-linked Markdown -> Ollama -> Qdrant indexing for ops."""
import argparse
import hashlib
import json
import re
import sys
import uuid
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from heading_chunk_filter import merge_heading_only_chunks

MODEL = 'qwen3-embedding:8b-fp16'
QDRANT = 'http://127.0.0.1:6333'
OLLAMA = 'http://192.168.1.3:11434'
COLLECTION = 'qdrant_memory'
MAX_CHARS = 2200
BATCH = 3
EXCLUDE = {'.git', '.venv', 'node_modules', '.obsidian', '__pycache__'}
SENSITIVE = re.compile(
    r'-----BEGIN [A-Z ]*PRIVATE KEY-----|'
    r'(?i:Authorization\s*:\s*(?:Bearer|Basic)\s+\S+)|'
    r'(?im:^\s*(?:export\s+)?[\w-]*(?:TOKEN|SECRET|PASSWORD|API_KEY)[\w-]*\s*[:=]\s*[^\s#]{8,})'
)


def request(url, data=None, method=None):
    body = None if data is None else json.dumps(data).encode()
    req = Request(url, data=body, method=method or ('POST' if body is not None else 'GET'),
                  headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=150) as resp:
        return json.load(resp)


def _original_chunks(root):
    for path in sorted(root.rglob('*.md')):
        if EXCLUDE.intersection(path.relative_to(root).parts) or not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root).as_posix()
        content = path.read_text(encoding='utf-8', errors='replace')
        heading = path.stem
        buffer, start, end, ordinal = [], 1, 1, 0
        size = 0

        def emit():
            nonlocal ordinal, buffer, size
            if not buffer or not ''.join(buffer).strip():
                buffer, size = [], 0
                return None
            raw = ''.join(buffer)
            # Omit a potential secret-containing passage rather than transmitting it.
            if SENSITIVE.search(raw):
                print(f'SKIP suspected credential: {rel} chunk {ordinal}', flush=True)
                ordinal += 1
                buffer, size = [], 0
                return None
            value = {
                'origin': 'ops', 'source': rel, 'heading': heading,
                'line_start': start, 'line_end': end,
                'text': raw,
                'content_sha256': hashlib.sha256((heading + '\n' + str(start) + '\n' + raw).encode()).hexdigest(),
                'kind': 'original_markdown'
            }
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f'ops:{rel}:{ordinal}'))
            ordinal += 1
            buffer, size = [], 0
            return point_id, value

        for lineno, line in enumerate(content.splitlines(keepends=True), 1):
            m = re.match(r'^#{1,6}\s+(.+)', line)
            if m:
                record = emit()
                if record:
                    yield record
                heading = m.group(1).strip()
            while line:
                if not buffer:
                    start = lineno
                remaining = MAX_CHARS - size
                part, line = line[:remaining], line[remaining:]
                buffer.append(part)
                size += len(part)
                end = lineno
                if size >= MAX_CHARS:
                    record = emit()
                    if record:
                        yield record
        record = emit()
        if record:
            yield record


def chunks(root):
    yield from merge_heading_only_chunks(_original_chunks(root), MAX_CHARS)


def existing_points():
    output, offset = {}, None
    while True:
        payload = {'limit': 256, 'with_payload': True, 'with_vector': False,
                   'filter': {'must': [{'key': 'origin', 'match': {'value': 'ops'}}]}}
        if offset is not None:
            payload['offset'] = offset
        result = request(f'{QDRANT}/collections/{COLLECTION}/points/scroll', payload)['result']
        for point in result['points']:
            output[str(point['id'])] = point.get('payload', {}).get('content_sha256')
        offset = result.get('next_page_offset')
        if offset is None:
            return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='/home/iragonforce/ops')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = Path(args.root)
    if not (root / 'AGENTS.md').is_file():
        raise SystemExit(f'STOP: not an ops checkout: {root}')
    documents = list(chunks(root))
    counts = Counter(item['source'].split('/')[0] for _, item in documents)
    print(f'Chunks: {len(documents)}; max chars: {MAX_CHARS}; files: {len(set(p["source"] for _,p in documents))}', flush=True)
    print('Distribution:', dict(sorted(counts.items())), flush=True)
    print(f'Collection: {COLLECTION}; model: {MODEL}', flush=True)
    if args.dry_run:
        print('DRY RUN: no embeddings generated, no Qdrant writes', flush=True)
        return

    try:
        info = request(f'{QDRANT}/collections/{COLLECTION}')
    except HTTPError as e:
        if e.code != 404:
            raise
        result = request(f'{QDRANT}/collections/{COLLECTION}',
                         {'vectors': {'size': 4096, 'distance': 'Cosine'}}, method='PUT')
        if result.get('status') != 'ok':
            raise SystemExit('STOP: failed to create collection')
        print('Created isolated collection', flush=True)
        info = request(f'{QDRANT}/collections/{COLLECTION}')
    conf = info['result']['config']['params']['vectors']
    if conf.get('size') != 4096 or conf.get('distance') != 'Cosine':
        raise SystemExit(f'STOP: unexpected collection vector configuration: {conf}')
    previous = existing_points()
    desired = {point_id for point_id, _ in documents}
    todo = [(point_id, p) for point_id, p in documents
            if previous.get(point_id) != p['content_sha256']]
    print(f'Existing: {len(previous)}; changed/new: {len(todo)}; stale: {len(set(previous)-desired)}', flush=True)
    for index in range(0, len(todo), BATCH):
        batch = todo[index:index+BATCH]
        texts = [f'Source: {p["source"]}\nHeading: {p["heading"]}\n{p["text"]}' for _, p in batch]
        embed = request(f'{OLLAMA}/api/embed', {'model': MODEL, 'input': texts, 'keep_alive': '10m'})
        vectors = embed['embeddings']
        if len(vectors) != len(batch) or any(len(v) != 4096 for v in vectors):
            raise SystemExit('STOP: embedding count or dimensions mismatch')
        result = request(f'{QDRANT}/collections/{COLLECTION}/points?wait=true',
                         {'points': [{'id': pid, 'vector': v, 'payload': p}
                                     for (pid, p), v in zip(batch, vectors)]}, method='PUT')
        if result.get('status') != 'ok':
            raise SystemExit(f'STOP: Qdrant upsert rejected at {index}')
        print(f'Upserted: {index+len(batch)}/{len(todo)}', flush=True)
    stale = sorted(set(previous) - desired)
    for i in range(0, len(stale), 100):
        result = request(f'{QDRANT}/collections/{COLLECTION}/points/delete?wait=true',
                         {'points': stale[i:i+100]})
        if result.get('status') != 'ok':
            raise SystemExit('STOP: stale-point deletion failed')
    after = existing_points()
    if set(after) != desired:
        raise SystemExit(f'STOP: expected {len(desired)} ops points, got {len(after)}')
    print(f'PASS: indexed {len(after)} ops passages; removed {len(stale)} stale points', flush=True)


if __name__ == '__main__':
    main()
