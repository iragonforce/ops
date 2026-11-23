#!/usr/bin/env python3
"""Check or explicitly deploy Git-owned files at their established paths.

Deployment refuses drift, preserves ownership and mode, follows existing file
links, and never restarts a service. Requires Python 3.9+; see install.py(1).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.home() / 'ops', help='ops checkout')
    parser.add_argument('--target', action='append', help='exact manifest target; repeatable')
    parser.add_argument('--group', help='explicit manifest deployment group')
    parser.add_argument('--apply', action='store_true', help='write selected files; default is read-only')
    args = parser.parse_args()
    root = args.repo.resolve()
    manifest = json.loads((root / 'inventory/deployments.json').read_text())
    host = socket.gethostname().split('.')[0].lower()
    rows = [r for r in manifest['assets'] if r['host'] == host]
    if args.target:
        unknown = set(args.target) - {r['target'] for r in rows}
        if unknown:
            parser.error('targets are not in this host manifest: ' + ', '.join(sorted(unknown)))
        rows = [r for r in rows if r['target'] in args.target]
    if args.group:
        rows = [r for r in rows if r.get('group') == args.group]
    if not rows:
        parser.error('no files selected for this host')
    if args.apply and not (args.target or args.group):
        parser.error('--apply requires explicit --target or --group selection')
    pending, problems = [], []
    resolved_sources = {}
    counts = {'unchanged': 0, 'pending': 0, 'conflicts': 0}
    for row in rows:
        src = (root / row['source']).resolve()
        if root not in src.parents:
            raise ValueError('source escapes checkout')
        target = Path(row['target'])
        if not target.is_absolute():
            raise ValueError('target must be absolute')
        try:
            actual, desired = digest(target), digest(src)
            if desired is None:
                raise ValueError('source missing')
            resolved = target.resolve()
            if resolved in resolved_sources and resolved_sources[resolved] != desired:
                raise ValueError('two selected sources disagree for the same resolved target')
            resolved_sources[resolved] = desired
            if actual == desired:
                counts['unchanged'] += 1
                continue
            if actual not in (row.get('baseline_sha256'), row.get('deployed_sha256')) or (
                actual is None and not row.get('allow_create', False)
            ):
                raise ValueError('live file changed since recorded baseline')
            if target.is_symlink() and not target.exists():
                raise ValueError('broken deployment symlink')
            if root == resolved or root in resolved.parents:
                raise ValueError('refusing to overwrite source through deployment link')
            pending.append((row, src, resolved, actual))
            counts['pending'] += 1
        except (OSError, ValueError) as exc:
            problems.append({'target': str(target), 'error': str(exc)})
    counts['conflicts'] = len(problems)
    if problems:
        print(json.dumps({'host': host, 'counts': counts, 'conflicts': problems}, indent=2))
        return 2
    receipts = []
    if args.apply:
        # Validate all selected baselines before writing; no force mode.
        for row, src, target, expected in pending:
            if digest(target) == digest(src):
                receipts.append({'target': row['target'], 'sha256': digest(src)})
                continue
            if digest(target) != expected:
                raise RuntimeError('target changed during deployment: ' + str(target))
            previous = target.stat() if target.exists() else None
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix='.ops-deploy-', dir=target.parent)
            try:
                with os.fdopen(fd, 'wb') as out:
                    out.write(src.read_bytes())
                    out.flush()
                    os.fsync(out.fileno())
                os.chmod(name, previous.st_mode & 0o777 if previous else row.get('mode', 0o644))
                if previous and os.geteuid() == 0:
                    os.chown(name, previous.st_uid, previous.st_gid)
                elif os.geteuid() == 0 and 'uid' in row:
                    os.chown(name, row['uid'], row.get('gid', row['uid']))
                os.replace(name, target)
            finally:
                if os.path.exists(name):
                    os.unlink(name)
            result = digest(target)
            if result != digest(src):
                raise RuntimeError('deployment readback mismatch: ' + str(target))
            receipts.append({'target': row['target'], 'sha256': result})
    print(json.dumps({'host': host, 'applied': args.apply, 'counts': counts, 'receipts': receipts}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print('Deployment stopped: ' + str(exc), file=sys.stderr)
        sys.exit(2)
