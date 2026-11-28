"""Fail-closed Stage 2 lease tests. Never call real systemd/NVIDIA services."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'tensor-gpu-lease.py'
spec = importlib.util.spec_from_file_location('tensor_gpu_lease', SCRIPT)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class Fake:
    def __init__(self, active=True, gpu_idle=True, may_acquire=True):
        self.wallpaper = active
        self.gpu_idle = gpu_idle
        self.may_acquire = may_acquire
        self.stops = 0
        self.starts = 0
        self.fail_stop = False
        self.fail_start = False
        self.preflight_ok = True

    def wallpaper_active(self): return self.wallpaper
    def stop_wallpaper(self):
        if self.fail_stop: raise RuntimeError('synthetic stop failure')
        self.wallpaper = False
        self.stops += 1
    def start_wallpaper(self):
        if self.fail_start: raise RuntimeError('synthetic restart failure')
        self.wallpaper = True
        self.starts += 1
    def safe_to_acquire(self): return self.may_acquire
    def inference_memory_released(self): return self.gpu_idle
    def preflight(self): return self.preflight_ok


class LeaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'private'/'queue.sqlite3'
        self.backend = Fake()
        self.lease = mod.LeaseManager(self.path, self.backend)
        self.addCleanup(self.lease.close)

    def acquire(self, owner='hermes', resource='qwen', **kw):
        return self.lease.acquire(owner,resource,activity='idle',**kw)

    def test_initial_acquire_and_last_release(self):
        token=self.acquire()
        self.assertEqual(self.backend.stops,1)
        self.assertFalse(self.backend.wallpaper)
        self.assertEqual(self.lease.release(token),'normal')
        self.assertTrue(self.backend.wallpaper)
        self.assertEqual(self.backend.starts,1)

    def test_two_consumers_same_resource(self):
        a=self.acquire('cli')
        b=self.acquire('gateway')
        self.assertEqual(self.backend.stops,1)
        self.assertEqual(self.lease.release(a),'reserved')
        self.assertEqual(self.backend.starts,0)
        self.assertEqual(self.lease.release(b),'normal')
        self.assertEqual(self.backend.starts,1)

    def test_incompatible_gpu_resource_refused(self):
        token=self.acquire()
        with self.assertRaises(mod.LeaseError):
            self.acquire('embedding','embedding-8b')
        self.assertEqual(self.lease.status()['leases'],1)
        self.assertEqual(self.lease.release(token),'normal')

    def test_active_background_refused_without_desktop_change(self):
        with self.assertRaises(mod.LeaseError):
            self.lease.acquire('batch','qwen',activity='active')
        self.assertEqual(self.backend.stops,0)
        self.assertEqual(self.lease.status()['mode'],'normal')

    def test_unknown_idle_signal_refuses_background(self):
        with self.assertRaises(mod.LeaseError):
            self.lease.acquire('batch','qwen',activity='unknown')
        self.assertEqual(self.backend.stops,0)

    def test_preflight_veto_keeps_wallpaper_and_normal_state(self):
        self.backend.preflight_ok = False
        with self.assertRaises(mod.LeaseError):
            self.acquire()
        self.assertTrue(self.backend.wallpaper)
        self.assertEqual(self.backend.stops, 0)
        self.assertEqual(self.lease.status()['mode'], 'normal')
        self.assertEqual(self.lease.status()['leases'], 0)

    def test_existing_holder_does_not_authorize_new_owner_after_veto(self):
        token = self.acquire('cli')
        self.backend.preflight_ok = False
        with self.assertRaises(mod.LeaseError):
            self.acquire('gateway')
        self.assertEqual(self.lease.status()['leases'], 1)
        self.backend.preflight_ok = True
        self.assertEqual(self.lease.release(token), 'normal')

    def test_explicit_foreground_does_not_bypass_resource_conflict(self):
        a=self.acquire()
        with self.assertRaises(mod.LeaseError):
            self.lease.acquire('interactive','other-model',activity='active',foreground=True)
        self.assertEqual(self.lease.release(a),'normal')
        b=self.lease.acquire('interactive','qwen',activity='active',foreground=True)
        self.assertEqual(self.lease.release(b),'normal')

    def test_stop_failure_leaves_recoverable_intent(self):
        self.backend.fail_stop=True
        with self.assertRaises(RuntimeError): self.acquire()
        self.assertEqual(self.lease.status()['mode'],'preparing')
        self.backend.fail_stop=False
        self.assertEqual(self.lease.reconcile(),'normal')
        self.assertTrue(self.backend.wallpaper)

    def test_uncoordinated_gpu_allocation_denies_acquire(self):
        self.backend.may_acquire=False
        with self.assertRaises(mod.LeaseError): self.acquire()
        self.assertEqual(self.lease.status()['leases'],0)
        self.assertFalse(self.backend.wallpaper)
        self.assertEqual(self.lease.reconcile(),'normal')
        self.assertTrue(self.backend.wallpaper)

    def test_idle_desktop_preparing_recovers_only_after_gpu_release(self):
        self.backend.wallpaper=False
        self.backend.may_acquire=False
        with self.assertRaises(mod.LeaseError): self.acquire()
        self.assertEqual(self.lease.status()['mode'], 'preparing')
        self.backend.may_acquire=True
        self.backend.gpu_idle=False
        with self.assertRaises(mod.LeaseError): self.acquire()
        self.assertEqual(self.lease.status()['mode'], 'preparing')
        self.backend.gpu_idle=True
        token=self.acquire()
        self.assertEqual(self.lease.status()['mode'], 'reserved')
        self.assertEqual(self.lease.release(token), 'normal')
        self.assertEqual(self.backend.starts, 0)

    def test_model_still_loaded_blocks_restoration(self):
        token=self.acquire()
        self.backend.gpu_idle=False
        self.assertEqual(self.lease.release(token),'restore_pending')
        self.assertFalse(self.backend.wallpaper)
        self.assertEqual(self.lease.reconcile(),'restore_pending')
        self.backend.gpu_idle=True
        self.assertEqual(self.lease.reconcile(),'normal')
        self.assertTrue(self.backend.wallpaper)

    def test_no_new_admission_during_restore_pending(self):
        token=self.acquire()
        self.backend.gpu_idle=False
        self.lease.release(token)
        with self.assertRaises(mod.LeaseError): self.acquire()
        self.backend.gpu_idle=True
        self.assertEqual(self.lease.reconcile(),'normal')

    def test_external_wallpaper_restart_is_recontained(self):
        token=self.acquire()
        self.backend.wallpaper=True  # Session bootstrap restarted it.
        self.assertEqual(self.lease.enforce(),'reserved')
        self.assertFalse(self.backend.wallpaper)
        self.assertEqual(self.backend.stops,2)
        self.lease.release(token)

    def test_wallpaper_originally_inactive_not_restarted(self):
        self.backend.wallpaper=False
        token=self.acquire()
        self.assertEqual(self.backend.stops,0)
        self.assertEqual(self.lease.release(token),'normal')
        self.assertEqual(self.backend.starts,0)

    def test_persistence_survives_manager_restart(self):
        token=self.acquire()
        self.lease.close()
        with mod.LeaseManager(self.path,self.backend) as reopened:
            self.assertEqual(reopened.status()['leases'],1)
            self.assertEqual(reopened.release(token),'normal')

    def test_reconcile_with_live_lease_never_restores(self):
        token=self.acquire()
        self.assertEqual(self.lease.reconcile(),'reserved')
        self.assertEqual(self.backend.starts,0)
        self.lease.release(token)

    def test_failed_wallpaper_restore_is_retriable(self):
        token=self.acquire()
        self.backend.fail_start=True
        with self.assertRaises(RuntimeError): self.lease.release(token)
        self.assertEqual(self.lease.status()['mode'],'restore_pending')
        self.backend.fail_start=False
        self.assertEqual(self.lease.reconcile(),'normal')

    def test_unknown_token_cannot_release(self):
        token=self.acquire()
        with self.assertRaises(mod.LeaseError): self.lease.release('bogus')
        self.assertEqual(self.lease.status()['leases'],1)
        self.lease.release(token)

    def test_lock_and_db_are_private(self):
        token=self.acquire()
        self.assertEqual(self.path.parent.stat().st_mode & 0o777,0o700)
        self.assertEqual(self.path.stat().st_mode & 0o777,0o600)
        self.assertEqual((self.path.parent/'gpu-lease.lock').stat().st_mode & 0o777,0o600)
        self.lease.release(token)


if __name__=='__main__':
    unittest.main()
