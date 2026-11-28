"""Offline Tensor embedding handoff tests; no GPU, Qdrant, SSH or Ollama calls."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'tensor_gpu_embedding.py'
SPEC = importlib.util.spec_from_file_location('tensor_gpu_embedding_test', SOURCE)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class EmbeddingHandoffTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db = Path(temp.name) / 'private' / 'queue.sqlite3'
        self.db.parent.mkdir(mode=0o700)
        self.inputs = ['Source: test\nHeading: sample\nA screened passage']
        self.vectors = [[0.5] * module.DIMENSIONS]

    def test_private_idempotent_payload_and_admitted_result(self):
        job = module.submit(self.db, self.inputs)
        self.assertEqual(job, module.submit(self.db, self.inputs))
        with module.Queue(self.db) as queue:
            self.assertEqual(1, queue.summary()['total'])
            claim = queue.claim('idle', 'worker', kinds=('embedding_batch',))
            payload_ref = queue.db.execute('SELECT payload_ref FROM jobs WHERE id=?',
                                           (job,)).fetchone()['payload_ref']
            self.assertEqual(stat.S_IMODE((self.db.parent / payload_ref).stat().st_mode), 0o600)
        called = []
        module.run_admitted(self.db, claim, lambda inputs, model: (
            called.append((inputs, model)) or self.vectors))
        self.assertEqual(called, [(self.inputs, module.MODEL)])
        data = module.result(self.db, job)
        self.assertEqual((data['digest'], data['vectors']), (module.digest(self.inputs), self.vectors))
        # The real CLI returns only protected-state references before admitted execution.
        self.assertEqual(self.inputs, json.loads(module.canonical(self.inputs))['inputs'])

    def test_failed_embedding_stays_retryable_without_result(self):
        job = module.submit(self.db, self.inputs)
        with module.Queue(self.db) as queue:
            claim = queue.claim('idle', 'worker', kinds=('embedding_batch',))
        with self.assertRaises(module.HandoffError):
            module.run_admitted(self.db, claim, lambda inputs, model: [[float('nan')] * module.DIMENSIONS])
        with module.Queue(self.db) as queue:
            state = queue.db.execute('SELECT state FROM jobs WHERE id=?', (job,)).fetchone()['state']
        self.assertEqual(state, 'retry')
        with self.assertRaises(module.HandoffError):
            module.result(self.db, job)

    def test_remote_submit_result_is_bounded_and_has_no_direct_fallback(self):
        job = module.submit(self.db, self.inputs)
        with module.Queue(self.db) as queue:
            claim = queue.claim('idle', 'worker', kinds=('embedding_batch',))
        module.run_admitted(self.db, claim, lambda inputs, model: self.vectors)
        cmd = [sys.executable, str(SOURCE), '--db', str(self.db)]
        with patch.dict(os.environ, {'QDRANT_MEMORY_EMBED_COMMAND': json.dumps(cmd)}):
            value = module.writer_embed(self.inputs, lambda _inputs: self.fail('unguarded direct embed'))
        self.assertEqual(value, self.vectors)
        with patch.dict(os.environ, {'QDRANT_MEMORY_EMBED_COMMAND': '["/missing/command"]'}):
            with self.assertRaises(module.HandoffError):
                module.writer_embed(self.inputs, lambda _inputs: self.fail('unguarded direct embed'))
        with patch.dict(os.environ, {'QDRANT_MEMORY_EMBED_COMMAND': ''}):
            with self.assertRaises(module.HandoffError):
                module.writer_embed(self.inputs, lambda _inputs: self.fail('unguarded direct embed'))

    def test_dedup_revision_and_payload_integrity(self):
        job = module.submit(self.db, self.inputs)
        with module.Queue(self.db) as queue:
            ref = queue.db.execute('SELECT payload_ref FROM jobs WHERE id=?', (job,)).fetchone()['payload_ref']
            claim = queue.claim('idle', 'worker', kinds=('embedding_batch',))
        path = self.db.parent / ref
        path.write_bytes(module.canonical(['changed']))
        with self.assertRaises(module.HandoffError):
            module.run_admitted(self.db, claim, lambda *_: self.fail('corrupt input executed'))

    def test_configured_writer_wait_is_bounded_and_never_direct(self):
        with patch.dict(os.environ, {'QDRANT_MEMORY_EMBED_COMMAND': '["ssh", "tensor"]',
                                     'TENSOR_GPU_EMBED_WAIT_SECONDS': '900'}):
            with patch.object(module, 'remote_embed', return_value=self.vectors) as remote:
                self.assertEqual(module.writer_embed(self.inputs, self.fail), self.vectors)
                remote.assert_called_once_with(self.inputs, ['ssh', 'tensor'], timeout=900)
        with patch.dict(os.environ, {'QDRANT_MEMORY_EMBED_COMMAND': '["ssh", "tensor"]',
                                     'TENSOR_GPU_EMBED_WAIT_SECONDS': '3601'}):
            with self.assertRaises(module.HandoffError):
                module.writer_embed(self.inputs, self.fail)

    def test_expired_claim_cannot_start_gpu_callback(self):
        job = module.submit(self.db, self.inputs)
        with module.Queue(self.db) as queue:
            claim = queue.claim('idle', 'worker', kinds=('embedding_batch',))
            queue.db.execute('UPDATE jobs SET lease_until=0 WHERE id=?', (job,))
        with self.assertRaises(module.HandoffError):
            module.run_admitted(self.db, claim, lambda *_: self.fail('expired claim executed'))


if __name__ == '__main__':
    unittest.main()
