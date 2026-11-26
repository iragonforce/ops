"""The session-close hook only wakes the existing Nexus path watcher."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

PLUGIN = Path(__file__).parents[1] / 'hermes/qdrant-session-close/__init__.py'
PATH_UNIT = Path(__file__).parents[2] / 'hosts/nexus/files/etc/systemd/system/qdrant-memory.path'


class SessionCloseHookTests(unittest.TestCase):
    def test_default_profile_marker_only(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / 'trigger'
            marker.touch()
            os.utime(marker, ns=(1_000_000_000, 1_000_000_000))
            fake = types.SimpleNamespace(get_hermes_home=lambda: '/opt/data')
            with mock.patch.dict(sys.modules, {'hermes_constants': fake}):
                spec = importlib.util.spec_from_file_location('qdrant_close_test', PLUGIN)
                if spec is None or spec.loader is None:
                    raise RuntimeError('missing hook module')
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            with mock.patch.object(module, 'MARKER', marker):
                module.on_session_finalize(session_id='')
                self.assertEqual(marker.stat().st_mtime_ns, 1_000_000_000)
                with mock.patch.object(module, 'get_hermes_home', return_value='/opt/data/profiles/other'):
                    module.on_session_finalize(session_id='closed')
                self.assertEqual(marker.stat().st_mtime_ns, 1_000_000_000)
                module.on_session_finalize(session_id='closed')
                self.assertGreater(marker.stat().st_mtime_ns, 1_000_000_000)
                module.on_session_finalize(session_id='closed')
                self.assertEqual(marker.read_bytes(), b'1')
                marker.unlink()
                module.on_session_finalize(session_id='closed')
                marker.symlink_to(Path(temp) / 'target')
                module.on_session_finalize(session_id='closed')
                self.assertFalse((Path(temp) / 'target').exists())

    def test_existing_path_unit_watches_only_inbox_and_marker(self):
        text = PATH_UNIT.read_text()
        self.assertIn('PathModified=/home/iragonforce/qdrant-inbox', text)
        self.assertIn('PathChanged=/srv/containers/data/hermes/data/state/qdrant-memory/session-close-trigger', text)
        self.assertIn('Unit=qdrant-memory.service', text)


if __name__ == '__main__':
    unittest.main()
