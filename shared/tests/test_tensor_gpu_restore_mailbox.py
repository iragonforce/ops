"""Stage 2F one-consumer private grant transport; no systemd or GPU calls."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts/tensor-gpu-restore-mailbox.py'
spec = importlib.util.spec_from_file_location('tensor_gpu_restore_mailbox_test', SOURCE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

A = 'a' * 32
B = 'b' * 32


class MailboxTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name) / 'private'
        self.parent.mkdir(mode=0o700)
        self.db = self.parent / 'queue.sqlite3'
        self.db.write_bytes(b'fixture database metadata')
        self.db.chmod(0o600)
        self.target = self.parent / mod.MAILBOX_NAME

    def test_publish_consumed_once(self):
        mod.publish(self.db, A)
        self.assertEqual(mod.consume(self.db), A)
        self.assertIsNone(mod.consume(self.db))
        self.assertFalse(self.target.exists())

    def test_private_permissions(self):
        mod.publish(self.db, A)
        info = self.target.stat()
        self.assertEqual(stat.S_IMODE(info.st_mode), 0o600)
        self.assertEqual(info.st_uid, os.geteuid())

    def test_replace_rotates_previous_token(self):
        mod.publish(self.db, A)
        mod.publish(self.db, B)
        self.assertEqual(mod.consume(self.db), B)
        self.assertIsNone(mod.consume(self.db))

    def test_missing_grant_does_not_create_file(self):
        self.assertIsNone(mod.consume(self.db))
        self.assertFalse(self.target.exists())

    def test_bad_grant_rejected_without_file(self):
        for bad in ('', 'a' * 31, 'A' * 32, 'z' * 32, 'a' * 32 + '\n', 123):
            with self.subTest(bad=bad), self.assertRaises(mod.MailboxError):
                mod.publish(self.db, bad)
            self.assertFalse(self.target.exists())

    def test_bad_permissions_veto(self):
        self.parent.chmod(0o755)
        with self.assertRaises(mod.MailboxError): mod.publish(self.db, A)
        with self.assertRaises(mod.MailboxError): mod.consume(self.db)

    def test_symlink_db_veto(self):
        alias = self.parent / 'alias.sqlite3'
        alias.symlink_to(self.db)
        with self.assertRaises(mod.MailboxError): mod.publish(alias, A)

    def test_symlink_mailbox_veto_on_publish(self):
        self.target.symlink_to(self.db)
        with self.assertRaises(mod.MailboxError): mod.publish(self.db, A)
        self.assertEqual(self.db.read_bytes(), b'fixture database metadata')

    def test_invalid_mode_mailbox_veto_on_publish(self):
        self.target.write_text(A + '\n')
        self.target.chmod(0o644)
        with self.assertRaises(mod.MailboxError): mod.publish(self.db, B)

    def test_invalid_mailbox_consumption_fails_and_cleans(self):
        self.target.write_text('not a token')
        self.target.chmod(0o600)
        with self.assertRaises(mod.MailboxError): mod.consume(self.db)
        self.assertFalse(self.target.exists())
        self.assertEqual(list(self.parent.glob('.wallpaper-consumed-*')), [])

    def test_symlink_mailbox_consumption_no_traversal(self):
        self.target.symlink_to(self.db)
        with self.assertRaises(OSError): mod.consume(self.db)
        self.assertEqual(self.db.read_bytes(), b'fixture database metadata')
        self.assertFalse(self.target.exists())

    def test_two_concurrent_consumers_only_one_grant(self):
        mod.publish(self.db, A)
        results = []
        errors = []
        def take():
            try: results.append(mod.consume(self.db))
            except BaseException as exc: errors.append(exc)
        threads = [threading.Thread(target=take) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(errors, [])
        self.assertEqual(sorted(results, key=lambda x: x or ''), [None, A])

    def test_insecure_database_veto(self):
        self.db.chmod(0o644)
        with self.assertRaises(mod.MailboxError): mod.publish(self.db, A)
        with self.assertRaises(mod.MailboxError): mod.consume(self.db)

    def test_no_grant_exposed_by_cli(self):
        cp = subprocess.run([sys.executable, str(SOURCE)], capture_output=True, text=True, check=True)
        self.assertFalse(json.loads(cp.stdout)['production_control_enabled'])
        self.assertNotIn(A, cp.stdout)
        cp = subprocess.run([sys.executable, str(SOURCE), '--help'], capture_output=True, text=True, check=True)
        self.assertIn('--version', cp.stdout)


if __name__ == '__main__':
    unittest.main()
