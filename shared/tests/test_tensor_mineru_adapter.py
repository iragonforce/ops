"""Offline per-PDF MinerU queue and artifact checks; no native conversion or GPU."""
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/tensor-mineru-adapter.py'
spec = importlib.util.spec_from_file_location('tensor_mineru_test', SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PDFAdapterTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        state = root / 'state'; state.mkdir(mode=0o700)
        output = root / 'outputs'; (output / 'gradio').mkdir(parents=True)
        self.queue = module.Queue(state / 'queue.sqlite3')
        self.addCleanup(self.queue.close)
        self.adapter = module.PDFAdapter(self.queue, state / 'payloads', output)
        self.root = root
        self.output = output
        self.active = False
        self.calls = []

    @contextmanager
    def admit(self):
        self.assertFalse(self.active)
        self.active = True
        try:
            yield
        finally:
            self.active = False

    def file(self, name, data=b'%PDF-1.7\nsynthetic only'):
        path = self.root / name
        path.write_bytes(data)
        return path

    def convert(self, path):
        self.assertTrue(self.active)
        self.calls.append(path.read_bytes())
        folder = self.output / 'gradio' / f'result-{len(self.calls)}'
        folder.mkdir()
        for name in ('middle_json.json', 'markdown.md', 'structured_content.json'):
            (folder / name).write_text('{}')
        return folder

    def test_two_pdfs_run_sequentially_and_deduplicate(self):
        paths = [self.file('a.pdf'), self.file('b.pdf', b'%PDF-1.7\nsecond synthetic')]
        records = self.adapter.submit_files(paths, 'mineru-config-v1')
        self.assertTrue(all(created for _, created in records))
        self.assertEqual([(job, False) for job, _ in records],
                         self.adapter.submit_files(paths, 'mineru-config-v1'))
        for job_id, _ in records:
            self.assertEqual(job_id, self.adapter.run_one(admit=self.admit, convert=self.convert))
        self.assertIsNone(self.adapter.run_one(admit=self.admit, convert=self.convert))
        self.assertEqual(len(self.calls), 2)
        self.assertFalse(self.active)
        self.assertEqual(self.queue.summary()['counts']['completed'], 2)

    def test_unknown_conversion_outcome_never_replays(self):
        self.adapter.submit_files([self.file('ambiguous.pdf')], 'mineru-config-v1')
        def uncertain(_path):
            self.calls.append('posted')
            raise ConnectionError('POST may have succeeded')
        with self.assertRaises(ConnectionError):
            self.adapter.run_one(admit=self.admit, convert=uncertain)
        self.assertIsNone(self.adapter.run_one(admit=self.admit, convert=self.convert))
        self.assertEqual(self.calls, ['posted'])
        self.assertEqual(self.queue.summary()['counts']['failed'], 1)

    def test_failed_receipt_can_only_be_reconciled_with_existing_artifacts(self):
        job_id, _ = self.adapter.submit_files([self.file('reconcile.pdf')], 'mineru-config-v1')[0]
        def failure(path):
            folder = self.convert(path)
            # Simulate an expired queue lease AFTER the durable output marker.
            self.queue.db.execute("UPDATE jobs SET lease_until=0 WHERE id=?", (job_id,))
            return folder
        with self.assertRaises(module.QueueError):
            self.adapter.run_one(admit=self.admit, convert=failure)
        self.assertEqual(1, self.queue.recover_stale())
        self.assertEqual('result-1', self.adapter.reconcile(job_id))
        self.assertEqual(self.queue.summary()['counts']['completed'], 1)
        with self.assertRaises(module.QueueError):
            self.adapter.reconcile(job_id)

    def test_rejects_symlink_pdf_and_changed_payload(self):
        path = self.file('source.pdf')
        (self.root / 'link.pdf').symlink_to(path)
        with self.assertRaises(module.QueueError):
            self.adapter.submit_files([self.root / 'link.pdf'], 'mineru-config-v1')
        job_id, _ = self.adapter.submit_files([path], 'mineru-config-v1')[0]
        token = self.queue.db.execute('SELECT payload_ref FROM jobs WHERE id=?', (job_id,)).fetchone()['payload_ref']
        (self.adapter.root / token / 'input.pdf').write_bytes(b'changed')
        with self.assertRaises(module.QueueError):
            self.adapter.run_one(admit=self.admit, convert=self.convert)
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
