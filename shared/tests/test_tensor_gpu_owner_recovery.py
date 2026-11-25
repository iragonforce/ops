"""Stage 2D owner-binding/recovery regression tests; fake GPU backend only."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from contextlib import closing
import sqlite3
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'tensor-gpu-lease.py'
spec = importlib.util.spec_from_file_location('tensor_gpu_lease_owner_test', SOURCE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class Fake:
    def __init__(self):
        self.wallpaper = True
        self.gpu_busy = False
        self.stops = 0
        self.starts = 0
    def wallpaper_active(self): return self.wallpaper
    def stop_wallpaper(self):
        self.stops += 1
        self.wallpaper = False
    def start_wallpaper(self):
        self.starts += 1
        self.wallpaper = True
    def safe_to_acquire(self): return not self.gpu_busy
    def inference_memory_released(self): return not self.gpu_busy


class OwnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'secure' / 'lease.sqlite3'
        self.b = Fake()
        self.q = mod.LeaseManager(self.path, self.b, require_identity=True)
        self.addCleanup(lambda: self.q.close())
        self.a = mod.OwnerIdentity('boot-a', 100, 1000)
        self.second = mod.OwnerIdentity('boot-a', 200, 2000)

    def acquire(self, owner='first', identity=None):
        return self.q.acquire(owner, 'qwen', activity='idle', identity=identity or self.a)

    def row(self, token):
        return self.q._conn.execute('SELECT * FROM gpu_leases WHERE token=?', (token,)).fetchone()

    def test_requires_owner_before_any_desktop_change(self):
        with self.assertRaises(mod.LeaseError):
            self.q.acquire('first', 'qwen', activity='idle')
        self.assertEqual(self.b.stops, 0)
        self.assertEqual(self.q.status()['mode'], 'normal')

    def test_owner_fields_durable_and_reopening(self):
        token = self.acquire()
        row = self.row(token)
        self.assertEqual((row['owner_boot_id'], row['owner_pid'], row['owner_start_ticks']),
                         ('boot-a', 100, 1000))
        self.q.close()
        self.q = mod.LeaseManager(self.path, self.b, require_identity=True)
        self.assertEqual(self.row(token)['owner_start_ticks'], 1000)
        self.assertEqual(self.q.status()['leases'], 1)
        self.q.release(token)
        self.assertEqual(self.b.starts, 1)

    def test_dead_last_owner_restores_only_when_memory_released(self):
        token = self.acquire()
        self.b.gpu_busy = True
        result = self.q.recover_dead_owners(lambda _: 'dead')
        self.assertEqual(result, {'result':'restore_pending','recovered':1,'unverified':0})
        self.assertEqual(self.b.starts, 0)
        self.assertEqual(self.q.status()['mode'], 'restore_pending')
        with self.assertRaises(mod.LeaseError):
            self.q.release(token)
        self.b.gpu_busy = False
        self.assertEqual(self.q.reconcile(), 'normal')
        self.assertEqual(self.b.starts, 1)

    def test_live_owner_untouched_and_dead_removed(self):
        first = self.acquire()
        second = self.acquire('second', self.second)
        result = self.q.recover_dead_owners(lambda i: 'dead' if i.pid == 100 else 'live')
        self.assertEqual(result['result'], 'reserved')
        self.assertEqual(result['recovered'], 1)
        self.assertIsNone(self.row(first))
        self.assertIsNotNone(self.row(second))
        self.assertEqual(self.b.starts, 0)
        self.q.release(second)
        self.assertEqual(self.b.starts, 1)

    def test_unknown_owner_blocks_all_deletions(self):
        first = self.acquire()
        second = self.acquire('second', self.second)
        result = self.q.recover_dead_owners(lambda i: 'unknown' if i.pid == 200 else 'dead')
        self.assertEqual(result['unverified'], 1)
        self.assertEqual(result['recovered'], 0)
        self.assertIsNotNone(self.row(first))
        self.assertIsNotNone(self.row(second))
        self.assertEqual(self.b.starts, 0)

    def test_invalid_verifier_result_denies_recovery(self):
        self.acquire()
        result = self.q.recover_dead_owners(lambda _: 'probably dead')
        self.assertEqual(result['recovered'], 0)
        self.assertEqual(result['unverified'], 1)
        self.assertEqual(self.q.status()['leases'], 1)

    def test_missing_proc_permission_does_not_delete(self):
        self.acquire()
        def bad(_): raise OSError('fake permission issue')
        self.assertEqual(self.q.recover_dead_owners(bad)['unverified'], 1)
        self.assertEqual(self.q.status()['leases'], 1)

    def test_legacy_lease_cannot_be_assumed_dead(self):
        self.q.close()
        with mod.LeaseManager(self.path, self.b) as legacy:
            token = legacy.acquire('legacy', 'qwen', activity='idle')
        self.q = mod.LeaseManager(self.path, self.b, require_identity=True)
        result = self.q.recover_dead_owners(lambda _: 'dead')
        self.assertEqual(result['unverified'], 1)
        self.assertIsNotNone(self.row(token))
        self.assertEqual(self.b.starts, 0)

    def test_additive_schema_migration_keeps_old_rows(self):
        self.q.close()
        self.path.unlink()
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript('''
                CREATE TABLE gpu_lease_state(id INTEGER PRIMARY KEY,mode TEXT,resource TEXT,restore_wallpaper INTEGER,modified_at INTEGER);
                INSERT INTO gpu_lease_state VALUES(1,'reserved','qwen',1,100);
                CREATE TABLE gpu_leases(token TEXT PRIMARY KEY,owner TEXT,resource TEXT,created_at INTEGER);
                INSERT INTO gpu_leases VALUES('legacy-token','old','qwen',100);
            ''')
        self.path.chmod(0o600)
        self.q = mod.LeaseManager(self.path, self.b, require_identity=True)
        self.assertEqual(self.q.status()['leases'], 1)
        self.assertIsNone(self.row('legacy-token')['owner_boot_id'])
        self.assertEqual(self.q.recover_dead_owners(lambda _: 'dead')['unverified'], 1)

    def test_bad_identity_rejected_before_stop(self):
        for ident in (mod.OwnerIdentity('', 100, 1000), mod.OwnerIdentity('boot', 0, 1000),
                      mod.OwnerIdentity('boot', 1, 0), mod.OwnerIdentity('bad boot', 1, 10)):
            with self.subTest(ident=ident), self.assertRaises(mod.LeaseError):
                self.q.acquire('bad', 'qwen', activity='idle', identity=ident)
        self.assertEqual(self.b.stops, 0)

    def test_recovery_idempotent(self):
        self.acquire()
        self.assertEqual(self.q.recover_dead_owners(lambda _: 'dead')['recovered'], 1)
        self.assertEqual(self.q.recover_dead_owners(lambda _: 'dead')['recovered'], 0)
        self.assertEqual(self.q.status()['mode'], 'normal')
        self.assertEqual(self.b.starts, 1)

    def test_uncoordinated_gpu_blocks_restoration_after_death(self):
        self.acquire()
        self.b.gpu_busy = True
        self.q.recover_dead_owners(lambda _: 'dead')
        self.assertEqual(self.b.starts, 0)
        self.assertEqual(self.q.status()['mode'], 'restore_pending')
        with self.assertRaises(mod.LeaseError):
            self.q.acquire('third', 'qwen', activity='idle', identity=self.second)

    def test_failed_atomic_registration_never_creates_unowned_token(self):
        original = self.q._set_state
        def fail(mode, resource, restore):
            if mode == 'reserved': raise RuntimeError('synthetic transaction failure')
            return original(mode,resource,restore)
        self.q._set_state = fail
        with self.assertRaises(RuntimeError): self.acquire()
        self.assertEqual(self.q.status()['leases'], 0)
        self.assertEqual(self.q.status()['mode'], 'preparing')

    def test_failed_atomic_release_keeps_original_token(self):
        token = self.acquire()
        original = self.q._set_state
        def fail(mode, resource, restore):
            if mode == 'restore_pending': raise RuntimeError('synthetic transaction failure')
            return original(mode,resource,restore)
        self.q._set_state = fail
        with self.assertRaises(RuntimeError): self.q.release(token)
        self.assertIsNotNone(self.row(token))
        self.assertEqual(self.q.status()['mode'], 'reserved')
        self.assertEqual(self.b.starts, 0)

    def test_mixed_legacy_and_bound_leases_blocks_everything(self):
        first = self.acquire()
        self.q.require_identity = False
        second = self.q.acquire('legacy','qwen',activity='idle')
        result = self.q.recover_dead_owners(lambda _: 'dead')
        self.assertEqual(result['unverified'], 1)
        self.assertIsNotNone(self.row(first))
        self.assertIsNotNone(self.row(second))

    def test_no_live_service_control_exposed(self):
        self.assertTrue('synthetic' in SOURCE.read_text()[:100])
        self.assertFalse(hasattr(mod, 'systemctl_command'))
        self.assertFalse(hasattr(mod, 'stop_gpu_model'))


if __name__ == '__main__':
    unittest.main()
