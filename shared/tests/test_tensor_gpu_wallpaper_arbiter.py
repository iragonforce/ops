"""Stage 2D atomic wallpaper-start policy: no real systemd or GPU calls."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import fcntl
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'scripts/tensor-gpu-wallpaper-arbiter.py'
spec = importlib.util.spec_from_file_location('tensor_gpu_wallpaper_arbiter', SOURCE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def make_db(path, *, mode='normal', leases=0, resource=None, restore=0):
    path.parent.mkdir(mode=0o700, exist_ok=True)
    db = sqlite3.connect(path)
    try:
        db.execute('CREATE TABLE gpu_lease_state (id INTEGER, mode TEXT, resource TEXT, restore_wallpaper INTEGER)')
        db.execute('CREATE TABLE gpu_leases (token TEXT)')
        db.execute('INSERT INTO gpu_lease_state VALUES (1, ?, ?, ?)', (mode, resource, restore))
        db.executemany('INSERT INTO gpu_leases VALUES (?)', [(str(i),) for i in range(leases)])
        db.commit()
    finally:
        db.close()
    path.chmod(0o600)


class ArbiterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'private' / 'queue.sqlite3'
        self.calls = []

    def run_start(self):
        return mod.try_start(self.db,
                             lambda: self.calls.append('launch'),
                             lambda: self.calls.append('ready') or True,
                             lambda: self.calls.append('abort'), gpu_safe=lambda: True)


    def test_gpu_residency_veto(self):
        make_db(self.db)
        result = mod.try_start(self.db, lambda: self.calls.append('launch'),
                               lambda: True, lambda: None, gpu_safe=lambda: False)
        self.assertEqual(result.reason, 'gpu_residency_veto')
        self.assertEqual(self.calls, [])

    def test_gpu_probe_failure_refuses_without_launch(self):
        make_db(self.db)
        def broken_gpu():
            raise OSError('NVML unavailable')
        result = mod.try_start(self.db, lambda: self.calls.append('launch'),
                               lambda: True, lambda: None, gpu_safe=broken_gpu)
        self.assertEqual(result.reason, 'unverified_gpu_residency')
        self.assertEqual(self.calls, [])

    def test_gpu_check_occurs_inside_lock(self):
        make_db(self.db)
        def check_gpu():
            fd = os.open(self.db.parent/'gpu-lease.lock', os.O_RDWR)
            try:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    self.calls.append('gpu_check_under_lock')
                    return True
                raise AssertionError('GPU check was outside lease lock')
            finally:
                os.close(fd)
        result = mod.try_start(self.db, lambda: self.calls.append('launch'),
                               lambda: True, lambda: None, gpu_safe=check_gpu)
        self.assertTrue(result.started)
        self.assertEqual(self.calls, ['gpu_check_under_lock', 'launch'])

    def test_normal_state_starts_and_readies_under_lock(self):
        make_db(self.db)
        decision = self.run_start()
        self.assertTrue(decision.started)
        self.assertEqual(self.calls, ['launch', 'ready'])

    def test_preparing_denies_without_callback(self):
        make_db(self.db, mode='preparing', resource='model', restore=1)
        self.assertFalse(self.run_start().started)
        self.assertEqual(self.calls, [])

    def test_reserved_denies_without_callback(self):
        make_db(self.db, mode='reserved', resource='model', leases=1, restore=1)
        self.assertFalse(self.run_start().started)
        self.assertEqual(self.calls, [])

    def test_restore_pending_denies_without_two_phase_grant(self):
        make_db(self.db, mode='restore_pending', resource='model', restore=1)
        self.assertFalse(self.run_start().started)
        self.assertEqual(self.calls, [])

    def test_normal_but_lease_exists_denies(self):
        make_db(self.db, mode='normal', leases=1)
        self.assertFalse(self.run_start().started)

    def test_missing_db_denies(self):
        self.db.parent.mkdir(mode=0o700)
        self.assertFalse(self.run_start().started)

    def test_corrupt_database_denies(self):
        self.db.parent.mkdir(mode=0o700)
        self.db.write_bytes(b'not an sqlite database')
        self.db.chmod(0o600)
        self.assertFalse(self.run_start().started)

    def test_insecure_db_denies(self):
        make_db(self.db)
        self.db.chmod(0o644)
        self.assertFalse(self.run_start().started)

    def test_symlink_lock_denied(self):
        make_db(self.db)
        (self.db.parent / 'gpu-lease.lock').symlink_to(self.db)
        with self.assertRaises(OSError):
            self.run_start()
        self.assertEqual(self.calls, [])

    def test_insecure_lock_denied(self):
        make_db(self.db)
        (self.db.parent / 'gpu-lease.lock').write_text('')
        (self.db.parent / 'gpu-lease.lock').chmod(0o644)
        with self.assertRaises(mod.ArbitrationError):
            self.run_start()

    def test_lock_already_held_denies_without_waiting(self):
        make_db(self.db)
        fd = os.open(self.db.parent / 'gpu-lease.lock', os.O_RDWR | os.O_CREAT, 0o600)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.assertEqual(self.run_start().reason, 'lease_lock_busy')
        self.assertEqual(self.calls, [])

    def test_launch_failure_propagates_and_retains_db(self):
        make_db(self.db)
        def fail():
            raise RuntimeError('simulated launch failed')
        with self.assertRaisesRegex(RuntimeError, 'launch failed'):
            mod.try_start(self.db, fail, lambda: True, lambda: self.calls.append('abort'), gpu_safe=lambda: True)
        self.assertEqual(self.calls, ['abort'])
        self.assertTrue(self.run_start().started)

    def test_ready_failure_fails_closed(self):
        make_db(self.db)
        with self.assertRaises(mod.ArbitrationError):
            mod.try_start(self.db, lambda: self.calls.append('launch'), lambda: False,
                          lambda: self.calls.append('abort'), gpu_safe=lambda: True)
        self.assertEqual(self.calls, ['launch', 'abort'])

    def test_launch_and_ready_hold_lock_against_other_thread(self):
        make_db(self.db)
        observed = []
        def launch():
            fd = os.open(self.db.parent/'gpu-lease.lock', os.O_RDWR)
            try:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    observed.append('exclusive_lock_unavailable_during_launch')
                else:
                    observed.append('ERROR_lock_unexpectedly_available')
            finally:
                os.close(fd)
        def ready():
            observed.append('ready')
            return True
        self.assertTrue(mod.try_start(self.db, launch, ready, lambda: None, gpu_safe=lambda: True).started)
        self.assertEqual(observed, ['exclusive_lock_unavailable_during_launch','ready'])

    def test_retry_after_contention(self):
        make_db(self.db)
        fd = os.open(self.db.parent/'gpu-lease.lock', os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertFalse(self.run_start().started)
            fcntl.flock(fd, fcntl.LOCK_UN)
            self.assertTrue(self.run_start().started)
        finally:
            os.close(fd)


    def test_abort_failure_is_explicit(self):
        make_db(self.db)
        def failed_cleanup():
            raise OSError('candidate still alive')
        with self.assertRaisesRegex(mod.ArbitrationError, 'cleanup failed'):
            mod.try_start(self.db, lambda: None, lambda: False, failed_cleanup, gpu_safe=lambda: True)

    def test_acquire_waits_for_startup_critical_section(self):
        # Real LeaseManager and arbiter use the same flock file. Even if GPU
        # admission overlaps a wallpaper startup, it runs only after readiness.
        lease_path = ROOT / 'scripts/tensor-gpu-lease.py'
        sp = importlib.util.spec_from_file_location('tensor_gpu_lease_arbiter_test', lease_path)
        lease_mod = importlib.util.module_from_spec(sp)
        sys.modules[sp.name] = lease_mod
        sp.loader.exec_module(lease_mod)
        class Desktop:
            wallpaper = False
            stops = 0
            def wallpaper_active(self): return self.wallpaper
            def stop_wallpaper(self):
                self.wallpaper = False
                self.stops += 1
            def start_wallpaper(self): self.wallpaper = True
            def safe_to_acquire(self): return True
            def inference_memory_released(self): return True
        desktop = Desktop()
        with lease_mod.LeaseManager(self.db, desktop) as lease:
            launched = threading.Event()
            permit_ready = threading.Event()
            results = {}
            def launch():
                desktop.wallpaper = True
                launched.set()
            def ready():
                if not permit_ready.wait(3):
                    raise TimeoutError('synthetic ready gate timed out')
                return True
            def start_thread():
                results['start'] = mod.try_start(self.db, launch, ready, lambda: None, gpu_safe=lambda: True)
            def acquire_thread():
                with lease_mod.LeaseManager(self.db, desktop) as other:
                    results['lease'] = other.acquire('test', 'gpu', activity='idle')
            one = threading.Thread(target=start_thread)
            two = threading.Thread(target=acquire_thread)
            one.start()
            self.assertTrue(launched.wait(2))
            two.start()
            self.assertFalse('lease' in results)
            permit_ready.set()
            one.join(3)
            two.join(3)
            self.assertFalse(one.is_alive() or two.is_alive())
            self.assertTrue(results['start'].started)
            self.assertEqual(desktop.stops, 1)
            self.assertFalse(desktop.wallpaper)
            self.assertEqual(lease.release(results['lease']), 'normal')

    def test_existing_lease_blocks_wallpaper_start(self):
        lease_path = ROOT / 'scripts/tensor-gpu-lease.py'
        sp = importlib.util.spec_from_file_location('tensor_gpu_lease_arbiter_reserved', lease_path)
        lease_mod = importlib.util.module_from_spec(sp)
        sys.modules[sp.name] = lease_mod
        sp.loader.exec_module(lease_mod)
        class Desktop:
            def wallpaper_active(self): return False
            def stop_wallpaper(self): raise AssertionError('unnecessary')
            def start_wallpaper(self): pass
            def safe_to_acquire(self): return True
            def inference_memory_released(self): return True
        with lease_mod.LeaseManager(self.db, Desktop()) as lease:
            token = lease.acquire('test', 'gpu', activity='idle')
            self.assertFalse(self.run_start().started)
            self.assertEqual(self.calls, [])
            lease.release(token)

    def test_source_only_cli(self):
        proc = subprocess.run([sys.executable, str(SOURCE)], text=True, capture_output=True, check=True)
        self.assertIn('"live_control_enabled": false', proc.stdout)
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
