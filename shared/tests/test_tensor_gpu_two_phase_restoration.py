"""Stage 2D two-phase restoration contract. Synthetic backend; no real systemd/GPU."""
from __future__ import annotations
import fcntl
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts'


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, SCRIPT / file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lease_mod = load('tensor_gpu_lease_two_phase_test', 'tensor-gpu-lease.py')
arb_mod = load('tensor_gpu_wallpaper_arbiter_two_phase_test', 'tensor-gpu-wallpaper-arbiter.py')


class Desktop:
    def __init__(self, db):
        self.db = db
        self.wallpaper = True
        self.gpu_busy = False
        self.starts = 0
        self.stops = 0
        self.fail_launch = False
        self.fail_ready = False
        self.refuse_ack = False
        self.crash_after_ack = False
        self.without_lock = False
        self.decision = None
        self.last_grant = None

    def wallpaper_active(self):
        return self.wallpaper

    def stop_wallpaper(self):
        self.stops += 1
        self.wallpaper = False

    def safe_to_acquire(self):
        return not self.gpu_busy

    def inference_memory_released(self):
        return not self.gpu_busy

    def start_wallpaper(self, *, restoration_grant=None):
        self.last_grant = restoration_grant
        self.starts += 1
        fd = os.open(self.db.parent / 'gpu-lease.lock', os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.without_lock = True
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
        def launch():
            if self.fail_launch:
                raise RuntimeError('synthetic unit launch failed')
            self.wallpaper = True
        def ready():
            return not self.fail_ready
        def abort():
            self.wallpaper = False
        if self.refuse_ack:
            # A service start with no guarded READY acknowledgement is invalid.
            self.wallpaper = True
            return
        self.decision = arb_mod.try_start(self.db, launch, ready, abort,
                                           gpu_safe=lambda: not self.gpu_busy,
                                           restoration_grant=restoration_grant)
        if not self.decision.started:
            raise RuntimeError('synthetic startup admission denied')
        if self.crash_after_ack:
            raise RuntimeError('launcher died after systemd acknowledged READY')


class TwoPhaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'private' / 'lease.sqlite3'
        self.backend = Desktop(self.db)
        self.lease = lease_mod.LeaseManager(self.db, self.backend,
                                             require_identity=False,
                                             two_phase_restore=True)
        self.addCleanup(lambda: self.lease.close())

    def pending(self):
        token = self.lease.acquire('synthetic', 'qwen', activity='idle')
        self.assertEqual(self.lease.release(token), 'restore_pending')
        self.assertEqual(self.lease.status()['mode'], 'restore_pending')
        return token

    def test_release_never_starts_wallpaper_while_locked(self):
        self.pending()
        self.assertEqual(self.backend.starts, 0)
        self.assertEqual(self.backend.stops, 1)

    def test_end_to_end_handoff_acknowledged_and_idempotent(self):
        self.pending()
        self.assertEqual(self.lease.complete_restoration(), 'normal')
        self.assertTrue(self.backend.without_lock)
        self.assertEqual(self.backend.decision.reason, 'launched_under_lease_lock')
        self.assertTrue(self.backend.wallpaper)
        self.assertEqual(self.lease.status()['mode'], 'normal')
        self.assertEqual(self.lease.complete_restoration(), 'normal')
        self.assertEqual(self.backend.starts, 1)

    def test_retry_after_launch_failure(self):
        self.pending()
        self.backend.fail_launch = True
        with self.assertRaises(RuntimeError):
            self.lease.complete_restoration()
        self.assertEqual(self.lease.status()['mode'], 'restore_pending')
        self.assertFalse(self.backend.wallpaper)
        self.backend.fail_launch = False
        self.assertEqual(self.lease.complete_restoration(), 'normal')

    def test_ready_failure_does_not_clear_restore_intent(self):
        self.pending()
        self.backend.fail_ready = True
        with self.assertRaises(arb_mod.ArbitrationError):
            self.lease.complete_restoration()
        self.assertEqual(self.lease.status()['mode'], 'restore_pending')
        self.assertFalse(self.backend.wallpaper)
        self.backend.fail_ready = False
        self.assertEqual(self.lease.complete_restoration(), 'normal')

    def test_missing_guard_ack_does_not_accept_startup(self):
        self.pending()
        self.backend.refuse_ack = True
        with self.assertRaises(lease_mod.LeaseError):
            self.lease.complete_restoration()
        self.assertEqual(self.lease.status()['mode'], 'restore_pending')

    def test_model_busy_blocks_completion(self):
        self.pending()
        self.backend.gpu_busy = True
        self.assertEqual(self.lease.complete_restoration(), 'restore_pending')
        self.assertEqual(self.backend.starts, 0)
        self.backend.gpu_busy = False
        self.assertEqual(self.lease.complete_restoration(), 'normal')

    def test_uncoordinated_wallpaper_restart_blocks(self):
        self.pending()
        self.backend.wallpaper = True
        with self.assertRaises(lease_mod.LeaseError):
            self.lease.complete_restoration()
        self.assertEqual(self.backend.starts, 0)

    def test_no_restore_when_wallpaper_initially_inactive(self):
        self.backend.wallpaper = False
        t = self.lease.acquire('synthetic','qwen',activity='idle')
        self.assertEqual(self.lease.release(t), 'normal')
        self.assertEqual(self.backend.starts, 0)

    def test_new_lease_denied_during_pending(self):
        self.pending()
        with self.assertRaises(lease_mod.LeaseError):
            self.lease.acquire('other','qwen',activity='idle')
        self.assertEqual(self.lease.complete_restoration(), 'normal')

    def test_restore_lock_contended(self):
        self.pending()
        restore_file = self.db.parent / 'gpu-restore.lock'
        fd = os.open(restore_file, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(lease_mod.LeaseError, 'already in progress'):
                self.lease.complete_restoration()
        finally:
            os.close(fd)
        self.assertEqual(self.backend.starts, 0)
        self.assertEqual(self.lease.complete_restoration(), 'normal')

    def test_complete_disabled_by_default(self):
        with lease_mod.LeaseManager(self.db, self.backend) as legacy:
            with self.assertRaisesRegex(lease_mod.LeaseError, 'not enabled'):
                legacy.complete_restoration()

    def test_arbiter_does_not_restore_without_prior_wallpaper_intent(self):
        # A normal GPU lease which started without wallpaper never grants start.
        self.backend.wallpaper = False
        t = self.lease.acquire('synthetic','qwen',activity='idle')
        self.assertFalse(arb_mod.try_start(self.db, lambda: None, lambda: True,
                          lambda: None, gpu_safe=lambda: True).started)
        self.lease.release(t)

    def test_acknowledged_state_survives_caller_failure(self):
        self.pending()
        self.backend.crash_after_ack = True
        with self.assertRaisesRegex(RuntimeError, 'after systemd acknowledged'):
            self.lease.complete_restoration()
        self.assertEqual(self.lease.status()['mode'], 'normal')
        self.assertTrue(self.backend.wallpaper)

    def test_wrong_grant_refuses_pending_restoration(self):
        self.pending()
        calls=[]
        refused = arb_mod.try_start(self.db, lambda: calls.append('start'),
                                    lambda: True, lambda: calls.append('abort'),
                                    gpu_safe=lambda: True,
                                    restoration_grant='0' * 32)
        self.assertFalse(refused.started)
        self.assertEqual(refused.reason, 'restoration_grant_invalid')
        self.assertEqual(calls, [])
        self.assertEqual(self.lease.status()['mode'], 'restore_pending')

    def test_replayed_grant_refused_after_success(self):
        self.pending()
        self.assertEqual(self.lease.complete_restoration(), 'normal')
        grant = self.backend.last_grant
        self.assertEqual(len(grant), 32)
        result = arb_mod.try_start(self.db, lambda: self.fail('replay started wallpaper'),
                                   lambda: True, lambda: None, gpu_safe=lambda: True,
                                   restoration_grant=grant)
        self.assertFalse(result.started)
        self.assertEqual(result.reason, 'restoration_grant_invalid')

    def test_grant_rotates_on_retry(self):
        self.pending()
        self.backend.fail_launch = True
        with self.assertRaises(RuntimeError):
            self.lease.complete_restoration()
        stale = self.backend.last_grant
        self.backend.fail_launch = False
        self.assertEqual(self.lease.complete_restoration(), 'normal')
        self.assertNotEqual(stale, self.backend.last_grant)
        self.assertEqual(self.lease.status()['mode'], 'normal')

    def test_no_service_start_without_restoration_need(self):
        # Already-normal is an idempotent no-op, even on a new manager.
        self.assertEqual(self.lease.complete_restoration(), 'normal')
        self.assertEqual(self.backend.starts, 0)


if __name__ == '__main__':
    unittest.main()
