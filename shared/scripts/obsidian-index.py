#!/usr/bin/env python3
"""Index eligible historical Obsidian Markdown in an existing Qdrant collection.

Input: read-only secondBrain/Homelab Markdown, Ollama embedding endpoint and Qdrant.
Output: origin=obsidian_history passages in qdrant_memory (apply mode only).
Purpose: make non-Paperclip technical notes searchable without modifying the vault,
        authoritative ops points, or Hermes production memory configuration.

Run --dry-run before --apply. Screening is heuristic, not a secret-scanning guarantee.
Paperclip/HOM-related, ambiguous and sensitive documents are deferred for review.
"""
import argparse
import hashlib
import json
import re
import uuid
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path('/home/iragonforce/secondBrain/Homelab')
QDRANT = 'http://127.0.0.1:6333'
OLLAMA = 'http://192.168.1.3:11434'
COLLECTION = 'qdrant_memory'
MODEL = 'qwen3-embedding:8b-fp16'
DIMENSIONS = 4096
MAX_CHARS = 2200
BATCH = 3
EXCLUDED_DIRS = {'.git', '.obsidian', '.trash', '.stfolder', '.true-recall'}
REVIEW_NAMES = {'00-user-preferences.md', '10-private-file-locations.md'}
PAPERCLIP = re.compile(r'\bpaperclip\b', re.I)
AGENT = re.compile(r'\bHOM[- ]\d+\b|\bagent[ -](?:onboard|scope|setup|hire|role)\b', re.I)
SENSITIVE = re.compile(
    r'-----BEGIN [A-Z ]*PRIVATE KEY-----|'
    r'(?i:Authorization\s*:\s*(?:Bearer|Basic)\s+\S+)|'
    r'(?im:^\s*(?:export\s+)?[\w-]*(?:TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY|ACCESS_KEY)[\w-]*\s*[:=]\s*[\"\']?[^\s#\"\']{8,})|'
    r'(?i:\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{24,}|xox[baprs]-[A-Za-z0-9-]{20,}))'
)


def request(url, data=None, method=None):
    payload = json.dumps(data).encode() if data is not None else None
    req = Request(url, data=payload,
                  method=method or ('POST' if payload is not None else 'GET'),
                  headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=150) as response:
        return json.load(response)


def passages(path, root):
    """Create stable, heading-aware records with no source text truncation."""
    rel = path.relative_to(root).as_posix()
    source = f'secondBrain/Homelab/{rel}'
    heading = path.stem
    block, size, start, end, ordinal = [], 0, 1, 1, 0

    def emit():
        nonlocal block, size, ordinal
        if not block or not ''.join(block).strip():
            block, size = [], 0
            return None
        raw = ''.join(block)
        checksum = hashlib.sha256((heading + '\n' + str(start) + '\n' + raw).encode()).hexdigest()
        payload = {
            'origin': 'obsidian_history', 'source': source,
            'heading': heading, 'line_start': start, 'line_end': end,
            'text': raw, 'content_sha256': checksum,
            'kind': 'original_markdown',
            'authority': 'historical_unverified',
            'import_policy': 'non_paperclip_v1'
        }
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f'obsidian_history:{source}:{ordinal}'))
        ordinal += 1
        block, size = [], 0
        return point_id, payload

    for lineno, original_line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(keepends=True), 1):
        match = re.match(r'^#{1,6}\s+(.+)', original_line)
        if match:
            old = emit()
            if old is not None:
                yield old
            heading = match.group(1).strip()
        line = original_line
        while line:
            if not block:
                start = lineno
            take = MAX_CHARS - size
            part, line = line[:take], line[take:]
            block.append(part)
            size += len(part)
            end = lineno
            if size == MAX_CHARS:
                old = emit()
                if old is not None:
                    yield old
    last = emit()
    if last is not None:
        yield last


def classify(root, only):
    counts, selected, review = Counter(), [], []
    for path in sorted(root.rglob('*.md')):
        rel = path.relative_to(root)
        if not path.is_file() or path.is_symlink() or EXCLUDED_DIRS.intersection(rel.parts):
            continue
        counts['total'] += 1
        name = rel.as_posix()
        text = path.read_text(encoding='utf-8', errors='replace')
        if PAPERCLIP.search(name) or PAPERCLIP.search(text):
            category = 'paperclip_review'
        elif AGENT.search(name) or AGENT.search(text):
            category = 'agent_related_review'
        elif path.name in REVIEW_NAMES:
            category = 'private_or_profile_review'
        elif SENSITIVE.search(text):
            category = 'sensitive_review'
        else:
            category = 'eligible'
        counts[category] += 1
        if category != 'eligible':
            review.append((category, name))
        elif not only or name in only:
            selected.append(path)
    return counts, selected, review


def existing_obsidian():
    points, offset = {}, None
    while True:
        arg = {'limit': 256, 'with_payload': True, 'with_vector': False,
               'filter': {'must': [{'key': 'origin', 'match': {'value': 'obsidian_history'}}]}}
        if offset is not None:
            arg['offset'] = offset
        page = request(f'{QDRANT}/collections/{COLLECTION}/points/scroll', arg)['result']
        for item in page['points']:
            points[str(item['id'])] = item.get('payload', {}).get('content_sha256')
        offset = page.get('next_page_offset')
        if offset is None:
            return points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--apply', action='store_true')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--only', action='append', default=[], metavar='RELATIVE_MD_PATH',
                        help='Limit selected files; repeat for multiple paths')
    args = parser.parse_args()
    root = args.root
    if not root.is_dir():
        parser.error(f'Obsidian Homelab directory missing: {root}')
    counts, selected, review = classify(root, set(args.only))
    all_eligible = counts['eligible']
    if args.only and len(selected) != len(set(args.only)):
        missing = sorted(set(args.only) - {p.relative_to(root).as_posix() for p in selected})
        parser.error(f'Requested file not eligible or not present: {missing}')
    records = [item for path in selected for item in passages(path, root)]
    print('=== SOURCE SCREEN ===', flush=True)
    print('Classification:', dict(sorted(counts.items())), flush=True)
    print(f'Eligible files: {all_eligible}; selected: {len(selected)}; passages: {len(records)}', flush=True)
    print(f'Collection: {COLLECTION}; model: {MODEL}; origin: obsidian_history', flush=True)
    print('Deferred for review (first 12 paths):', flush=True)
    for category, path in review[:12]:
        print(f'  {category}: {path}', flush=True)
    if args.dry_run:
        print('DRY RUN: no embeddings generated, no Qdrant writes', flush=True)
        return
    info = request(f'{QDRANT}/collections/{COLLECTION}')['result']
    cfg = info['config']['params']['vectors']
    if cfg.get('size') != DIMENSIONS or cfg.get('distance') != 'Cosine':
        raise SystemExit('STOP: wrong Qdrant collection dimensions/distance')
    prev = existing_obsidian()
    todo = [(pid, p) for pid, p in records if prev.get(pid) != p['content_sha256']]
    print(f'Existing Obsidian: {len(prev)}; changed/new: {len(todo)}', flush=True)
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i+BATCH]
        texts = [f'Source: {p["source"]}\nHeading: {p["heading"]}\n{p["text"]}' for _, p in batch]
        vectors = request(f'{OLLAMA}/api/embed', {'model': MODEL, 'input': texts, 'keep_alive': '10m'})['embeddings']
        if len(vectors) != len(batch) or any(len(v) != DIMENSIONS for v in vectors):
            raise SystemExit('STOP: embedding dimensions/count mismatch')
        result = request(f'{QDRANT}/collections/{COLLECTION}/points?wait=true',
                         {'points': [{'id': pid, 'vector': vector, 'payload': p}
                                     for (pid, p), vector in zip(batch, vectors)]}, method='PUT')
        if result.get('status') != 'ok':
            raise SystemExit(f'STOP: Qdrant refused upsert at batch {i}')
        print(f'Upserted: {i + len(batch)}/{len(todo)}', flush=True)
    print('COMPLETE: Obsidian eligible passages indexed (no deletions)', flush=True)


if __name__ == '__main__':
    main()
