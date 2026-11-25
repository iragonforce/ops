"""Stage 2D read-only policy tests; no real services or GPU accessed."""
import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'tensor-gpu-lifecycle-guard.py'
spec = importlib.util.spec_from_file_location('tensor_gpu_lifecycle_guard', SOURCE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def stat_line(state='S', ticks=400):
    # Proc stat: pid (comm) state then fields 4..22 (19 values).
    return f'123 (python with spaces) {state} ' + ' '.join(['0'] * 18 + [str(ticks)])


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name) / 'private'
        self.base.mkdir(mode=0o700)
        self.db = self.base / 'lease.sqlite3'

    def build(self, mode='normal', count=0, *, resource=None, restore=0):
        with sqlite3.connect(self.db) as conn:
            conn.execute('CREATE TABLE gpu_lease_state(id INTEGER,mode TEXT,resource TEXT,restore_wallpaper INTEGER)')
            conn.execute('CREATE TABLE gpu_leases(token TEXT)')
            conn.execute('INSERT INTO gpu_lease_state VALUES (1,?,?,?)', (mode, resource, restore))
            conn.executemany('INSERT INTO gpu_leases VALUES (?)', [(f't{i}',) for i in range(count)])
        self.db.chmod(0o600)

    def test_missing_state_deny(self):
        with self.assertRaises(mod.GuardError): mod.read_state(self.db)

    def test_normal_without_leases_allow_candidate(self):
        self.build()
        self.assertEqual(mod.wallpaper_start_policy(mod.read_state(self.db)), (True, 'no_active_reservation'))

    def test_reserved_deny(self):
        self.build('reserved', 1, resource='qwen', restore=1)
        self.assertFalse(mod.wallpaper_start_policy(mod.read_state(self.db))[0])

    def test_preparing_deny(self):
        self.build('preparing', 0, resource='qwen')
        self.assertFalse(mod.wallpaper_start_policy(mod.read_state(self.db))[0])

    def test_restore_pending_deny(self):
        self.build('restore_pending', 0, resource='qwen', restore=1)
        self.assertFalse(mod.wallpaper_start_policy(mod.read_state(self.db))[0])

    def test_inconsistent_normal_with_lease_denied(self):
        self.build('normal', 1)
        self.assertFalse(mod.wallpaper_start_policy(mod.read_state(self.db))[0])

    def test_symlink_db_denied(self):
        self.build()
        link = self.base / 'linked.sqlite3'
        link.symlink_to(self.db)
        with self.assertRaises(mod.GuardError): mod.read_state(link)

    def test_insecure_database_denied(self):
        self.build()
        self.db.chmod(0o644)
        with self.assertRaises(mod.GuardError): mod.read_state(self.db)

    def test_pid_reuse_is_dead(self):
        proc = Path(self.temp.name) / 'proc'
        (proc / '123').mkdir(parents=True)
        (proc / '123/stat').write_text(stat_line(ticks=500))
        old = mod.OwnerIdentity('boot-a', 123, 400)
        self.assertEqual('dead', mod.inspect_process(old, proc=proc, boot_id='boot-a'))

    def test_same_pid_start_is_live(self):
        proc = Path(self.temp.name) / 'proc'
        (proc / '123').mkdir(parents=True)
        (proc / '123/stat').write_text(stat_line(ticks=400))
        owner = mod.OwnerIdentity('boot-a', 123, 400)
        self.assertEqual('live', mod.inspect_process(owner, proc=proc, boot_id='boot-a'))

    def test_missing_pid_is_dead(self):
        owner = mod.OwnerIdentity('boot-a', 123, 400)
        self.assertEqual('dead', mod.inspect_process(owner, proc=Path(self.temp.name), boot_id='boot-a'))

    def test_boot_change_is_dead(self):
        owner = mod.OwnerIdentity('boot-a', 123, 400)
        self.assertEqual('dead', mod.inspect_process(owner, proc=Path(self.temp.name), boot_id='boot-b'))

    def test_permission_or_malformed_is_unknown(self):
        proc = Path(self.temp.name) / 'proc'
        (proc / '123').mkdir(parents=True)
        (proc / '123/stat').write_text('broken data')
        owner = mod.OwnerIdentity('boot-a', 123, 400)
        self.assertEqual('unknown', mod.inspect_process(owner, proc=proc, boot_id='boot-a'))

    def test_zombie_is_dead_but_does_not_clear_gpu(self):
        proc = Path(self.temp.name) / 'proc'
        (proc / '123').mkdir(parents=True)
        (proc / '123/stat').write_text(stat_line(state='Z', ticks=400))
        owner = mod.OwnerIdentity('boot-a', 123, 400)
        self.assertEqual('dead', mod.inspect_process(owner, proc=proc, boot_id='boot-a'))


if __name__ == '__main__':
    unittest.main()
