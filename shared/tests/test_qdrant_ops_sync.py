"""Regressions for committed Markdown reconciliation in the existing Nexus writer."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).parents[1] / 'scripts/qdrant-memory.py'
spec = importlib.util.spec_from_file_location('qdrant_ops_sync_test', SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError('missing Qdrant writer')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class OpsSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.repo = self.home / 'ops'
        (self.repo / 'docs/current').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.doc = self.repo / 'docs/current/project.md'
        self.doc.write_text('# Verified project\n')
        (self.repo / 'host.conf').write_text('original\n')
        self.git('add', 'docs/current/project.md', 'host.conf')
        self.git('commit', '-qm', 'initial verified record')
        patch_home = mock.patch.object(core, 'HOME', self.home)
        patch_home.start()
        self.addCleanup(patch_home.stop)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args],
                              capture_output=True, check=True)

    def test_committed_docs_index_despite_unrelated_dirty_config(self):
        (self.repo / 'host.conf').write_text('locally edited, never indexed\n')
        with mock.patch.object(core, 'update_ops') as update:
            core.sync_ops()
        update.assert_called_once_with(False)

    def test_untracked_ignored_modified_and_staged_docs_are_skipped(self):
        for kind in ('untracked', 'ignored', 'modified', 'staged'):
            with self.subTest(kind=kind):
                if kind in ('untracked', 'ignored'):
                    path = self.repo / 'docs/current/draft.md'
                    if kind == 'ignored':
                        (self.repo / '.gitignore').write_text('draft.md\n')
                    path.write_text('private unfinished notes\n')
                else:
                    path = self.doc
                    path.write_text('unfinished edit\n')
                    if kind == 'staged':
                        self.git('add', 'docs/current/project.md')
                with mock.patch.object(core, 'update_ops') as update:
                    core.sync_ops()
                update.assert_not_called()
                if kind in ('untracked', 'ignored'):
                    path.unlink()
                    if kind == 'ignored':
                        (self.repo / '.gitignore').unlink()
                else:
                    self.git('reset', '-q', 'HEAD', '--', 'docs/current/project.md')
                    self.git('checkout', '--', 'docs/current/project.md')

    def test_changed_markdown_during_index_requires_retry(self):
        def concurrent_edit(_dry_run):
            self.doc.write_text('# Concurrent draft\n')
        with mock.patch.object(core, 'update_ops', side_effect=concurrent_edit):
            with self.assertRaisesRegex(RuntimeError, 'changed during indexing'):
                core.sync_ops()

    def test_missing_git_checkout_fails_closed(self):
        (self.repo / '.git').rename(self.home / 'not-a-checkout')
        with mock.patch.object(core, 'update_ops') as update:
            with self.assertRaisesRegex(RuntimeError, 'Git preflight failed'):
                core.sync_ops()
        update.assert_not_called()

    def test_dry_run_never_calls_apply(self):
        with mock.patch.object(core, 'update_ops') as update:
            core.sync_ops(dry_run=True)
        update.assert_called_once_with(True)


if __name__ == '__main__':
    unittest.main()
