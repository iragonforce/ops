#!/usr/bin/env python3
"""Synthetic-only tests for Tensor GPU queue Stage 1. No GPU/systemd access."""

import importlib.util
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


if __name__=='__main__':
    unittest.main(verbosity=2)
