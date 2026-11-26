#!/usr/bin/env python3
"""Synthetic queue and typed-record tests; no GPU/systemd access."""

import importlib.util
import hashlib
from contextlib import closing
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/tensor-gpu-queue.py'
spec = importlib.util.spec_from_file_location('tensor_gpu_queue', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class QueueTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'private'
        self.root.mkdir(mode=0o700)
        self.path = self.root / 'queue.sqlite3'
        self.q = mod.Queue(self.path)
        self.addCleanup(lambda: self.q.close())

    def test_batch_30_survives_restart_and_completes_in_order(self):
        names = [f'fixture-{i:04d}' for i in range(1,31)]
        result = self.q.submit_batch(names, now=100)
        self.assertEqual(30, sum(created for _,created in result))
        self.q.close()
        self.q = mod.Queue(self.path)
        seen = []
        for i in range(30):
            row = self.q.claim('idle', 'worker-a', now=101+i)
            self.assertEqual(names[i], row['source'])
            self.assertEqual('completed', self.q.finish(row['id'], 'worker-a', now=101+i))
            seen.append(row['id'])
        self.assertEqual([r[0] for r in result], seen)
        self.assertEqual(30, self.q.summary()['counts']['completed'])
        self.assertIsNone(self.q.claim('idle','worker-b',now=200))
        self.assertEqual(0, sum(created for _, created in self.q.submit_batch(names,now=201)))

    def test_priority_desc_fifo_within_priority(self):
        self.q.submit('low-a', priority=-1, now=10)
        self.q.submit('high-a', priority=3, now=10)
        self.q.submit('high-b', priority=3, now=10)
        self.q.submit('low-b', priority=-1, now=10)
        self.assertEqual(['high-a','high-b','low-a','low-b'],
            [self.q.claim('idle','w',now=11)['source'] for _ in range(4)])

    def test_unknown_and_active_activity_veto_all_claims(self):
        self.q.submit('one', now=10)
        self.assertIsNone(self.q.claim('unknown','w',now=11))
        self.assertIsNone(self.q.claim('active','w',now=11))
        self.assertEqual(self.q.summary()['counts']['pending'], 1)
        self.assertEqual('one', self.q.claim('idle','w',now=11)['source'])

    def test_pause_prevents_new_jobs_and_does_not_abort_running(self):
        self.q.submit('one', now=10)
        self.q.submit('two', now=10)
        first = self.q.claim('idle','worker',now=11)
        self.q.set_paused(True)
        self.assertTrue(self.q.paused())
        self.assertIsNone(self.q.claim('idle','worker',now=12))
        self.assertEqual('completed', self.q.finish(first['id'], 'worker', now=12))
        self.q.close()
        self.q = mod.Queue(self.path)
        self.assertTrue(self.q.paused())
        self.q.set_paused(False)
        self.assertEqual('two', self.q.claim('idle','worker',now=13)['source'])

    def test_backoff_bounded_retries_and_manual_retry(self):
        job_id, _ = self.q.submit('retries', max_attempts=3, now=100)
        for attempt, now in enumerate((100,160,280),1):
            task = self.q.claim('idle','w',now=now)
            self.assertEqual(job_id, task['id'])
            state = self.q.finish(job_id,'w',error='synthetic failure',now=now)
            self.assertEqual('failed' if attempt==3 else 'retry', state)
            if attempt==1:
                self.assertIsNone(self.q.claim('idle','w',now=159))
            if attempt==2:
                self.assertIsNone(self.q.claim('idle','w',now=279))
        self.assertIsNone(self.q.claim('idle','w',now=999))
        self.assertEqual('pending', self.q.transition(job_id,'retry',now=1000))
        self.assertEqual('retries',self.q.claim('idle','w',now=1000)['source'])

    def test_stale_lease_recovery_not_assumed_successful(self):
        job_id, _ = self.q.submit('crash', now=100)
        self.q.claim('idle','dead-worker',now=100,lease_seconds=10)
        self.q.close()
        self.q = mod.Queue(self.path)
        self.assertEqual(0,self.q.recover_stale(now=109))
        self.assertEqual(1,self.q.recover_stale(now=110))
        self.assertEqual(1,self.q.summary()['counts']['retry'])
        self.assertIsNone(self.q.claim('idle','live-worker',now=169))
        self.assertEqual(job_id,self.q.claim('idle','live-worker',now=170)['id'])
        with self.assertRaises(mod.QueueError):
            self.q.finish(job_id,'dead-worker',now=171)
        self.assertEqual('completed',self.q.finish(job_id,'live-worker',now=171))

    def test_stale_last_attempt_is_failed(self):
        job_id, _ = self.q.submit('last-crash',max_attempts=1,now=100)
        self.q.claim('idle','w',now=100,lease_seconds=10)
        self.assertEqual(1,self.q.recover_stale(now=110))
        self.assertEqual('failed',self.q.db.execute('SELECT state FROM jobs WHERE id=?',(job_id,)).fetchone()[0])

    def test_cancel_protects_running_or_completed_jobs(self):
        job_id, _=self.q.submit('one',now=100)
        self.assertEqual('cancelled',self.q.transition(job_id,'cancel',now=101))
        with self.assertRaises(mod.QueueError):
            self.q.transition(job_id,'retry',now=102)
        second,_=self.q.submit('two',now=100)
        self.q.claim('idle','w',now=101)
        with self.assertRaises(mod.QueueError):
            self.q.transition(second,'cancel',now=102)
        self.q.finish(second,'w',now=103)
        with self.assertRaises(mod.QueueError):
            self.q.transition(second,'cancel',now=104)

    def test_transaction_rolls_back_entire_invalid_batch(self):
        with self.assertRaises(mod.QueueError):
            self.q.submit_batch(['good','bad\x00name'],now=10)
        self.assertEqual(self.q.summary()['total'],0)

    def test_two_sqlite_connections_claim_one_job_once(self):
        self.q.submit('shared',now=10)
        results=[]
        failures=[]
        def grab(worker):
            try:
                with mod.Queue(self.path) as connection:
                    row=connection.claim('idle',worker,now=11)
                    results.append(row)
            except Exception as exc:
                failures.append(exc)
        a=threading.Thread(target=grab,args=('a',))
        b=threading.Thread(target=grab,args=('b',))
        a.start(); b.start(); a.join(); b.join()
        self.assertEqual(failures, [])
        self.assertEqual(sum(r is not None for r in results),1)

    def test_worker_lock_rejects_second_holder(self):
        with mod.worker_lock(self.root):
            with self.assertRaises(mod.QueueError):
                with mod.worker_lock(self.root):
                    pass

    def test_private_file_permissions_and_symlink_rejection(self):
        self.assertEqual(self.root.stat().st_mode & 0o777,0o700)
        self.assertEqual(self.path.stat().st_mode & 0o777,0o600)
        link=self.root/'link.sqlite3'
        link.symlink_to(self.path)
        with self.assertRaises(mod.QueueError):
            mod.Queue(link)

    def test_cli_can_submit_and_defer_without_gpu_access(self):
        proc=subprocess.run([sys.executable,str(SCRIPT),'--db',str(self.path),
                             'submit-batch','--count','30'],text=True,capture_output=True,check=True)
        self.assertIn('"created": 30',proc.stdout)
        proc=subprocess.run([sys.executable,str(SCRIPT),'--db',str(self.path),
                             'run-synthetic','--activity','active'],text=True,capture_output=True,check=True)
        self.assertIn('"synthetic_completed": 0',proc.stdout)
        proc=subprocess.run([sys.executable,str(SCRIPT),'--db',str(self.path),
                             'run-synthetic','--activity','idle'],text=True,capture_output=True,check=True)
        self.assertIn('"synthetic_completed": 30',proc.stdout)


class TypedQueueTest(unittest.TestCase):
    setUp = QueueTest.setUp

    def digest(self, value):
        return hashlib.sha256(value.encode()).hexdigest()

    def test_typed_dedup_revision_digest_and_kind(self):
        d = self.digest('batch one')
        first = self.q.submit_typed('embedding_batch', 'embed-config-v1', d, 'request:one', now=10)
        self.assertTrue(first[1])
        self.assertEqual((first[0], False), self.q.submit_typed(
            'embedding_batch', 'embed-config-v1', d, 'request:replacement', now=11))
        self.assertNotEqual(first[0], self.q.submit_typed(
            'embedding_batch', 'embed-config-v2', d, 'request:two', now=11)[0])
        self.assertNotEqual(first[0], self.q.submit_typed(
            'mineru_pdf', 'embed-config-v1', d, 'request:three', now=11)[0])
        self.assertNotEqual(first[0], self.q.submit_typed(
            'embedding_batch', 'embed-config-v1', self.digest('batch two'), 'request:four', now=11)[0])
        row = self.q.db.execute('SELECT * FROM jobs WHERE id=?', (first[0],)).fetchone()
        self.assertEqual(row['payload_ref'], 'request:one')
        self.assertEqual(row['source'], 'embedding_batch')

    def test_typed_fields_reject_paths_content_and_bad_digest(self):
        for kind, revision, digest, ref in (
            ('other', 'v1', self.digest('a'), 'ref:one'),
            ('mineru_pdf', '../private', self.digest('a'), 'ref:one'),
            ('mineru_pdf', 'v1', 'bad', 'ref:one'),
            ('mineru_pdf', 'v1', self.digest('a'), '/private/file.pdf'),
            ('mineru_pdf', 'v1', self.digest('a'), 'text with spaces'),
        ):
            with self.assertRaises(mod.QueueError):
                self.q.submit_typed(kind, revision, digest, ref)
        self.assertEqual(self.q.summary()['total'], 0)

    def test_default_synthetic_claim_does_not_execute_typed(self):
        job, _ = self.q.submit_typed('mineru_pdf', 'extract-v1', self.digest('pdf'), 'request:pdf', now=10)
        self.assertIsNone(self.q.claim('idle', 'w', now=11))
        self.assertIsNone(self.q.claim('active', 'w', now=11, kinds=('mineru_pdf',)))
        self.assertEqual(job, self.q.claim('idle', 'w', now=11, kinds=('mineru_pdf',))['id'])

    def test_fenced_finish_same_worker_reclaim_and_manual_retry(self):
        job, _ = self.q.submit_typed('embedding_batch', 'embed-v1', self.digest('one'), 'request:one', now=100)
        first = self.q.claim('idle', 'same', now=100, lease_seconds=10, kinds=('embedding_batch',))
        with self.assertRaises(mod.QueueError):
            self.q.finish(job, 'same', now=110, attempt=first['attempt'],
                          lease_token=first['lease_token'], result_ref='receipt:one')
        self.assertEqual(1, self.q.recover_stale(now=110))
        second = self.q.claim('idle', 'same', now=170, kinds=('embedding_batch',))
        with self.assertRaises(mod.QueueError):
            self.q.finish(job, 'same', now=171, attempt=first['attempt'],
                          lease_token=first['lease_token'], result_ref='receipt:one')
        with self.assertRaises(mod.QueueError):
            self.q.finish(job, 'same', now=171, result_ref='receipt:one')
        with self.assertRaises(mod.QueueError):
            self.q.finish(job, 'same', now=171, attempt=second['attempt'],
                          lease_token=second['lease_token'], result_ref='/private/result')
        self.assertEqual('retry', self.q.finish(job, 'same', now=171, attempt=second['attempt'],
                         lease_token=second['lease_token'], error='INFERENCE_FAILED'))

    def test_typed_failure_retry_and_completed_dedup(self):
        job, _ = self.q.submit_typed('mineru_pdf', 'extract-v1', self.digest('pdf'), 'request:pdf',
                                     max_attempts=1, now=100)
        claim = self.q.claim('idle', 'w', now=100, kinds=('mineru_pdf',))
        with self.assertRaises(mod.QueueError):
            self.q.finish(job, 'w', now=101, attempt=claim['attempt'],
                          lease_token=claim['lease_token'], error='private path /tmp/file.pdf')
        self.assertEqual('failed', self.q.finish(job, 'w', now=101, attempt=claim['attempt'],
                         lease_token=claim['lease_token'], error='CONVERSION_FAILED'))
        self.assertEqual('pending', self.q.transition(job, 'retry', now=102))
        again = self.q.claim('idle', 'w', now=102, kinds=('mineru_pdf',))
        self.assertNotEqual(claim['lease_token'], again['lease_token'])
        with self.assertRaises(mod.QueueError):
            self.q.finish(job, 'w', now=103, attempt=claim['attempt'],
                          lease_token=claim['lease_token'], result_ref='receipt:pdf')
        self.assertEqual('completed', self.q.finish(job, 'w', now=103, attempt=again['attempt'],
                         lease_token=again['lease_token'], result_ref='receipt:pdf'))
        self.assertEqual((job, False), self.q.submit_typed('mineru_pdf', 'extract-v1',
                         self.digest('pdf'), 'request:pdf-new', now=104))

    def test_migrate_v1_preserves_existing_synthetic_rows(self):
        legacy, _ = self.q.submit('legacy', now=10)
        self.q.set_paused(True)
        self.q.close()
        import sqlite3
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('ALTER TABLE jobs RENAME TO old_jobs')
            db.execute('''CREATE TABLE jobs (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL CHECK(kind = 'synthetic'),
                source TEXT NOT NULL,
                dedup_key TEXT NOT NULL UNIQUE,
                priority INTEGER NOT NULL,
                state TEXT NOT NULL CHECK(state IN
                    ('pending','retry','running','completed','failed','cancelled')),
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                available_at REAL NOT NULL,
                lease_owner TEXT,
                lease_until REAL,
                last_error TEXT,
                result_ref TEXT
            )''')
            db.execute('''INSERT INTO jobs (seq,id,kind,source,dedup_key,priority,state,attempts,
                max_attempts,created_at,updated_at,available_at,lease_owner,lease_until,last_error,result_ref)
                SELECT seq,id,kind,source,dedup_key,priority,state,attempts,max_attempts,
                created_at,updated_at,available_at,lease_owner,lease_until,last_error,result_ref FROM old_jobs''')
            db.execute('DROP TABLE old_jobs')
            db.execute('PRAGMA user_version=1')
        self.q = mod.Queue(self.path)
        self.assertEqual(2, self.q.db.execute('PRAGMA user_version').fetchone()[0])
        self.assertTrue(self.q.paused())
        self.assertEqual((legacy, False), self.q.submit('legacy', now=11))
        self.q.set_paused(False)
        self.assertEqual('legacy', self.q.claim('idle', 'w', now=11)['source'])
        self.q.close()
        self.q = mod.Queue(self.path)
        self.assertEqual(1, self.q.summary()['total'])


if __name__=='__main__':
    unittest.main(verbosity=2)
