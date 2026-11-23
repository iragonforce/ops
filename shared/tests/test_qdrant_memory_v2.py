import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from unittest import mock
import unittest

FRONT = Path(__file__).parents[1] / 'scripts/qdrant-memory'
BACK = Path(__file__).parents[1] / 'scripts/qdrant-memory-remote.py'
WATCH = Path(__file__).parents[1] / 'scripts/qdrant-memory-watch-setup.py'

def get_module(name, filepath):
    loader = importlib.machinery.SourceFileLoader(name, str(filepath))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod

f = get_module('frontend', FRONT)
b = get_module('backend', BACK)
w = get_module('watcher', WATCH)

class TestClient(unittest.TestCase):
    def test_stable_names_and_no_network_dryrun(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = root / 'Sample notes.md'
            p.write_text('# Sample\nhello world', encoding='utf-8')
            with mock.patch.object(f,'host_id', return_value='qubit'), mock.patch.object(f,'command') as command:
                a = f.send_file(p, scope='inbox', dry_run=True)
                c = f.send_file(p, scope='inbox', dry_run=True)
                d = f.send_file(p, scope='direct', dry_run=True)
                self.assertEqual(a,c)
                self.assertNotEqual(a,d)
                self.assertRegex(a, '^qubit--')
                self.assertRegex(a, '[a-f0-9]{12}\\.md$')
                command.assert_not_called()
    def test_bad_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'binary.txt').write_bytes(b'ab\0cd')
            (root/'bad.exe').write_text('hi')
            (root/'link.md').symlink_to(root/'bad.exe')
            with mock.patch.object(f,'host_id',return_value='tensor'):
                for name in ['binary.txt','bad.exe','link.md']:
                    with self.assertRaises(RuntimeError):
                        f.send_file(root/name,scope='inbox',dry_run=False)
    def test_file_upload_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'hello.md'
            p.write_text('hello')
            with mock.patch.object(f,'host_id',return_value='tensor'), mock.patch.object(f,'role',return_value='client'), mock.patch.object(f,'command') as command:
                out=f.send_file(p,scope='inbox',dry_run=False)
                self.assertEqual(command.call_args.args[0][0], 'receive')
                self.assertIn(out, command.call_args.args[0])
                self.assertEqual(command.call_args.kwargs['input_bytes'], b'hello')

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inbox = self.root/'qdrant-inbox'; self.inbox.mkdir(mode=0o700)
        self.state = self.root/'state'; self.state.mkdir(mode=0o700)
        (self.inbox/'.qdrant-memory-inbox-v1').write_text('marker')
        patch_inbox=mock.patch.object(b, 'INBOX', self.inbox); patch_inbox.start(); self.addCleanup(patch_inbox.stop)
        patch_state=mock.patch.object(b, 'STATE', self.state); patch_state.start(); self.addCleanup(patch_state.stop)
    def test_namespaced_file_validation(self):
        name='tensor--file-0123456789ab.md'
        self.assertEqual(b.check_name('tensor',name), self.inbox/name)
        for bad in ('qubit--file-0123456789ab.md','tensor--../x.md','../../unsafe.md'):
            with self.assertRaises(RuntimeError): b.check_name('tensor',bad)
    def test_receive_writes_and_dispatches(self):
        args=type('Args',(),{'host':'qubit','scope':'inbox','name':'qubit--notes-0123456789ab.md','original':'notes.md'})()
        class FakeCore:
            SENSITIVE_NAME=__import__('re').compile(r'(?i)secret')
            SENSITIVE=__import__('re').compile(r'(?i)password\\s*=')
            MAX_FILE_BYTES=256*1024
        with mock.patch.object(b,'load',return_value=FakeCore), mock.patch.object(b,'core_cmd') as core, mock.patch.object(b.sys,'stdin',type('S',(),{'buffer':io.BytesIO(b'# Documentation\nhello')})()):
            b.receive(args)
            self.assertEqual((self.inbox/args.name).read_text(), '# Documentation\nhello')
            core.assert_called_once_with('update',args.name)
    def test_manifest_does_not_delete_ad_hoc(self):
        names=['qubit--a-0123456789ab.md', 'qubit--b-0123456789ab.md']
        for name in names:
            (self.inbox/name).write_text('X')
        (self.inbox/'qubit--adhoc-0123456789ab.md').write_text('Y')
        (self.state/'client-manifest-qubit.json').write_text(json.dumps(names))
        args=type('Args',(),{'host':'qubit','allow_empty':False})()
        with mock.patch.object(b,'core_cmd') as core, mock.patch.object(b.sys,'stdin',io.StringIO(json.dumps({'names':[names[0]]}))):
            b.manifest(args)
            self.assertFalse((self.inbox/names[1]).exists())
            self.assertTrue((self.inbox/names[0]).exists())
            self.assertTrue((self.inbox/'qubit--adhoc-0123456789ab.md').exists())
            core.assert_called_once_with('update', names[1])
    def test_empty_manifest_requires_explicit_optin(self):
        name='tensor--a-0123456789ab.md'
        (self.inbox/name).write_text('X')
        (self.state/'client-manifest-tensor.json').write_text(json.dumps([name]))
        args=type('Args',(),{'host':'tensor','allow_empty':False})()
        with mock.patch.object(b.sys,'stdin',io.StringIO(json.dumps({'names':[]}))):
            with self.assertRaisesRegex(RuntimeError,'Refusing'):
                b.manifest(args)
        self.assertTrue((self.inbox/name).exists())
    def test_no_cross_host_manifest_deletion(self):
        owned='qubit--a-0123456789ab.md'
        foreign='tensor--b-0123456789ab.md'
        for n in [owned,foreign]: (self.inbox/n).write_text('X')
        (self.state/'client-manifest-qubit.json').write_text(json.dumps([owned]))
        args=type('Args',(),{'host':'qubit','allow_empty':True})()
        with mock.patch.object(b,'core_cmd'),mock.patch.object(b.sys,'stdin',io.StringIO(json.dumps({'names':[]}))):
            b.manifest(args)
        self.assertTrue((self.inbox/foreign).exists())
    def test_wrapped_code(self):
        out=b.text_to_markdown(b'print("hi")\n','hello.py')
        self.assertIn(b'```py',out)
        self.assertIn(b'print("hi")',out)
    def test_no_arbitrary_repos(self):
        for slug in ['../x','owner/../../x','https://evil.com/o/r','o/r;rm']:
            with self.assertRaises(RuntimeError):b.clone_repo(slug,True)

class TestWatch(unittest.TestCase):
    def test_systemd_names(self):
        self.assertEqual(set(w.systemd_files()),{'qdrant-memory.service','qdrant-memory.path','qdrant-memory.timer'})
        self.assertIn(b'ExecStart=%h/.local/bin/qdrant-memory sync-inbox',w.systemd_files()['qdrant-memory.service'])
    def test_plist(self):
        raw=w.launchd_file();data=__import__('plistlib').loads(raw)
        self.assertEqual(data['Label'],'com.blinkwired.qdrant-memory')
        self.assertEqual(data['StartInterval'],900)

if __name__=='__main__':
    unittest.main(verbosity=2)
