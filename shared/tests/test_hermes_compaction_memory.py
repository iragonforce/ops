"""Regression checks for conservative Hermes compaction export and reconciliation."""
import importlib.util
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).parents[1] / 'scripts'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError('Missing test module')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


export = load('hermes_compaction_test', SCRIPTS / 'hermes-compaction-export.py')
core = load('qdrant_memory_test', SCRIPTS / 'qdrant-memory.py')
mcp = load('qdrant_memory_mcp_test', SCRIPTS / 'qdrant-memory-hermes-mcp.py')


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'ops'
        self.repo.mkdir()
        subprocess.run(['git', '-C', str(self.repo), 'init', '-q'], check=True)
        source = self.repo / 'docs/changes/incident.md'
        source.parent.mkdir(parents=True)
        source.write_text('# Collector incident\nCollector now emits separate metrics.\n')
        subprocess.run(['git', '-C', str(self.repo), 'add', 'docs/changes/incident.md'], check=True)
        self.db = self.root / 'state.db'
        conn = sqlite3.connect(self.db)
        conn.executescript('''
            CREATE TABLE sessions (id TEXT, parent_session_id TEXT, end_reason TEXT,
                                   ended_at REAL, started_at REAL);
            CREATE TABLE messages (id TEXT, session_id TEXT, content TEXT,
                                   _compressed_summary INTEGER);
        ''')
        conn.execute('INSERT INTO sessions VALUES (?,NULL,?,?,?)', ('parent', 'compression', 1792778654, 1))
        conn.execute('INSERT INTO sessions VALUES (?,?,?,?,?)', ('child', 'parent', None, None, 2))
        conn.execute('INSERT INTO sessions VALUES (?,NULL,?,?,?)', ('active', None, None, 3))
        conn.execute('INSERT INTO messages VALUES (?,?,?,?)', ('one', 'child', self.summary(), 1))
        conn.commit()
        conn.close()

    @staticmethod
    def summary():
        return ('## Errors & Fixes\n'
                '- PATCHED docs/changes/incident.md — collector now emits separate metrics; observed successful updates across multiple cycles.\n'
                '- Tablet troubleshooting and unrelated tmux behavior were both discussed, which is not a single finding.\n'
                '- User password=SuperSecret123456 in docs/changes/incident.md was copied from the session.\n')

    def test_snapshot_and_one_finding(self):
        boundaries, candidates = export.fetch_candidates(self.db, strict=False)
        self.assertEqual((boundaries, len(candidates)), (1, 1))
        records, quarantine = export.build_findings(candidates[0], self.repo, (core.SENSITIVE,))
        self.assertEqual(len(records), 1)
        pid, payload = records[0]
        self.assertEqual(payload['origin'], 'hermes_session')
        self.assertEqual(payload['evidence_paths'], ['docs/changes/incident.md'])
        self.assertEqual(payload['parent_session_id'], 'parent')
        self.assertTrue(payload['historical_only'])
        self.assertIn('unverified', payload['authority'])
        self.assertEqual(quarantine['sensitive'], 1)
        self.assertIn('2026', export.observation_dates(self.db)['parent'])
        again, _ = export.build_findings(candidates[0], self.repo, (core.SENSITIVE,))
        self.assertEqual(again[0][0], pid)

    def test_incomplete_compaction_ignored_then_detected(self):
        conn = sqlite3.connect(self.db)
        conn.execute('INSERT INTO sessions VALUES (?,NULL,?,?,?)', ('new', 'compression', 1792778754, 4))
        conn.commit()
        conn.close()
        boundaries, candidates = export.fetch_candidates(self.db, strict=False)
        self.assertEqual((boundaries, len(candidates)), (2, 1))
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            export.fetch_candidates(self.db)
        conn = sqlite3.connect(self.db)
        conn.execute('INSERT INTO sessions VALUES (?,?,?,?,?)', ('newchild', 'new', None, None, 5))
        conn.execute('INSERT INTO messages VALUES (?,?,?,?)', ('two', 'newchild', self.summary(), 1))
        conn.commit()
        conn.close()
        self.assertEqual(len(export.fetch_candidates(self.db, strict=False)[1]), 2)

    def test_restart_and_failures(self):
        store = {}
        with mock.patch.object(core, 'INDEXERS', SCRIPTS), mock.patch.object(core, 'STATE', self.root), \
             mock.patch.dict(os.environ, {'QDRANT_MEMORY_HERMES_DB': str(self.db),
                                       'QDRANT_MEMORY_OPS': str(self.repo)}), \
             mock.patch.object(core, 'verify_collection'), \
             mock.patch.object(core, 'existing_points', side_effect=lambda origin: dict(store)), \
             mock.patch.object(core, 'upsert', side_effect=lambda records: store.update(records)):
            core.sync_hermes()
            self.assertEqual(len(store), 1)
            checkpoint = self.root / 'hermes-compaction-checkpoint.json'
            self.assertEqual(json.loads(checkpoint.read_text())['processed']['parent'], 'one')
            self.assertEqual(json.loads(checkpoint.read_text())['version'], 2)
            self.assertEqual(checkpoint.stat().st_mode & 0o777, 0o600)
            core.sync_hermes()
            self.assertEqual(len(store), 1)
            # Simulate Qdrant data loss after checkpoint: reconcile the same ID.
            store.clear()
            core.sync_hermes()
            self.assertEqual(len(store), 1)
            store.clear()
            checkpoint.unlink()
            with mock.patch.object(core, 'upsert', side_effect=OSError('Ollama unavailable')):
                with self.assertRaisesRegex(OSError, 'Ollama'):
                    core.sync_hermes()
            self.assertFalse(checkpoint.exists())
            with mock.patch.object(core, 'verify_collection', side_effect=OSError('Qdrant unavailable')):
                with self.assertRaisesRegex(OSError, 'Qdrant'):
                    core.sync_hermes()
            self.assertFalse(checkpoint.exists())
            core.sync_hermes()
            self.assertEqual(len(store), 1)
            self.assertTrue(checkpoint.exists())

    def test_checkpoint_integrity_and_interrupted_write(self):
        with mock.patch.object(core, 'STATE', self.root):
            core.checkpoint_write({'version': 1, 'processed': {'parent': 42}})
            checkpoint = self.root / 'hermes-compaction-checkpoint.json'
            self.assertEqual(core.checkpoint_read()['processed']['parent'], 42)
            value = json.loads(checkpoint.read_text())
            value['processed']['parent'] = 'modified'
            checkpoint.write_text(json.dumps(value))
            with self.assertRaisesRegex(RuntimeError, 'integrity mismatch'):
                core.checkpoint_read()
            (self.root / 'hermes-compaction-checkpoint.tmp').write_text('partial')
            os.chmod(self.root / 'hermes-compaction-checkpoint.tmp', 0o600)
            core.checkpoint_write({'version': 2, 'processed': {'parent': 'recovered'}})
            self.assertEqual(core.checkpoint_read()['processed']['parent'], 'recovered')

    def test_mcp_search_and_read_support_new_origin(self):
        payload = {'origin': 'hermes_session', 'source': 'hermes-compaction/a/b/c',
                   'text': 'Collector emitted separate metrics in a historical test.',
                   'authority': 'agent_summary_historical_unverified',
                   'observed_at': '2026-11-13', 'verification': 'git_path_referenced_not_content_verified'}
        point = {'id': '7467a4e7-9e66-4d97-a96a-225a63678c90', 'score': 0.85, 'payload': payload}
        def response(url, data, **kw):
            if url.endswith('/api/embed'):
                return {'embeddings': [[0.0] * 4096]}
            if url.endswith('/points/query'):
                self.assertEqual(data['filter']['must'][0]['match']['any'], ['hermes_session'])
                return {'result': {'points': [point]}}
            return {'result': [point]}
        with mock.patch.object(mcp, 'post', side_effect=response):
            result = mcp.search({'query': 'collector', 'origins': ['hermes_session']})
            self.assertIn('origin=hermes_session', result)
            self.assertIn('observed_at=2026-11-13', result)
            self.assertIn('verification=git_path_referenced_not_content_verified', result)
            self.assertIn('origin=hermes_session', mcp.read({'point_id': point['id']}))

    def test_concurrent_lock_rejects_second_run(self):
        state = self.root / 'private-state'
        with mock.patch.object(core, 'STATE', state):
            fd = core.lock()
            try:
                with self.assertRaisesRegex(RuntimeError, 'another qdrant-memory'):
                    core.lock()
                self.assertEqual(state.stat().st_mode & 0o777, 0o700)
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)


if __name__ == '__main__':
    unittest.main()
