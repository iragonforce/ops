"""Stage 2F synthetic source integration: no systemd/GPU or real grants."""
from __future__ import annotations
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

service = load('tensor_gpu_wallpaper_systemd_restore_integration', 'tensor-gpu-wallpaper-systemd.py')
adapter = load('tensor_gpu_systemd_adapter_restore_integration', 'tensor-gpu-systemd-adapter.py')
GRANT = 'c' * 32


class FakeProcess:
    pid = 200000
    def poll(self): return None
    def wait(self, timeout=None): return 0


class GrantArbiter:
    def __init__(self):
        self.grants = []
    def try_start(self, db, launch, ready, abort, *, gpu_safe, restoration_grant=None):
        self.grants.append(restoration_grant)
        if not gpu_safe():
            return type('Decision', (), {'started':False, 'reason':'gpu_veto'})()
        launch()
        if not ready():
            abort()
            raise RuntimeError('not ready')
        return type('Decision', (), {'started':True, 'reason':'synthetic'})()


def evidence():
    return {'mode':'read-only', 'evidence': {
        'wallpaper_service':'activating', 'hermes_llama_service':'inactive',
        'wallpaper_child_pids':[], 'cuda_compute_pids':[],
        'ollama_loaded_models':0,'gpu_memory':{'free_mib':11000}}}


class FakeBackend:
    def __init__(self):
        self.wallpaper = 'inactive'
        self.calls = []
        self.fail = False
    def observe(self):
        active = self.wallpaper=='active'
        return {'mode':'read-only', 'reasons': [], 'admission_candidate': True,
            'evidence':{'wallpaper_service':self.wallpaper,
                        'wallpaper_child_pids':[210] if active else [],
                        'hermes_llama_service':'inactive',
                        'cuda_compute_pids':[],'ollama_loaded_models':0,
                        'gpu_memory':{'free_mib':11000}}}
    def run(self, args):
        self.calls.append(args)
        if self.fail: raise RuntimeError('synthetic systemctl refused startup')
        self.wallpaper='active'
        return ''
    def backend(self):
        return adapter.TensorDesktopBackend(run=self.run, observe=self.observe)


class TransportIntegrationTest(unittest.TestCase):
    def test_guarded_entrypoint_forwards_restoration_grant_only_in_process(self):
        a=GrantArbiter()
        notifications=[]
        decision,proc=service.start_guarded(
            db=Path('/synthetic'), wallpaper=Path('/synthetic/engine'),
            arbiter=a, gpu_report=evidence,
            notify=lambda: notifications.append('ready'),
            spawn=lambda path: FakeProcess(),startup_delay=0,
            restoration_grant=GRANT)
        self.assertTrue(decision.started)
        self.assertEqual(a.grants,[GRANT])
        self.assertEqual(notifications,['ready'])
        self.assertIsNotNone(proc)

    def test_normal_start_does_not_require_grant(self):
        a=GrantArbiter()
        decision,_=service.start_guarded(
            db=Path('/synthetic'), wallpaper=Path('/synthetic/engine'),
            arbiter=a, gpu_report=evidence, notify=lambda: None,
            spawn=lambda path: FakeProcess(),startup_delay=0)
        self.assertTrue(decision.started)
        self.assertEqual(a.grants,[None])

    def test_adapter_publishes_and_revokes_after_systemctl(self):
        b=FakeBackend()
        calls=[]
        class Mailbox:
            def publish(self, db, grant): calls.append(('publish',grant))
            def revoke(self, db, grant): calls.append(('revoke',grant))
        def run(argv):
            calls.append(('systemctl', list(argv)))
            return b.run(argv)
        with patch.object(adapter, 'load_restore_mailbox', return_value=Mailbox()):
            obj=adapter.TensorDesktopBackend(run=run,observe=b.observe)
            obj.start_wallpaper(restoration_grant=GRANT)
        self.assertEqual([x[0] for x in calls],['publish','systemctl','revoke'])
        self.assertNotIn(GRANT, ' '.join(calls[1][1]))
        self.assertEqual(b.wallpaper,'active')

    def test_adapter_revokes_after_failed_start(self):
        b=FakeBackend();b.fail=True
        calls=[]
        class Mailbox:
            def publish(self, db, grant): calls.append('publish')
            def revoke(self, db, grant): calls.append('revoke')
        with patch.object(adapter, 'load_restore_mailbox', return_value=Mailbox()):
            with self.assertRaisesRegex(RuntimeError,'refused'):
                b.backend().start_wallpaper(restoration_grant=GRANT)
        self.assertEqual(calls,['publish','revoke'])
        self.assertEqual(b.wallpaper,'inactive')

    def test_adapter_rejects_grant_if_already_active(self):
        b=FakeBackend();b.wallpaper='active'
        with self.assertRaises(adapter.AdapterError):
            b.backend().start_wallpaper(restoration_grant=GRANT)
        self.assertEqual(b.calls,[])

    def test_no_grant_does_not_publish(self):
        b=FakeBackend()
        with patch.object(adapter,'load_restore_mailbox',side_effect=AssertionError('unexpected transport')):
            b.backend().start_wallpaper()
        self.assertEqual(len(b.calls),1)

    def test_veto_returns_retry_suppressed_exit_code(self):
        class Transport:
            def consume(self, db): return None
        class Probe:
            def probe(self): return evidence()
        class Arbiter:
            def try_start(self,*args,**kwargs):
                return type('Decision',(),{'started':False,'reason':'busy'})()
        modules={'tensor-gpu-wallpaper-arbiter.py':Arbiter(),
                 'tensor-gpu-probe.py':Probe(),
                 'tensor-gpu-restore-mailbox.py':Transport()}
        with patch.dict('os.environ', {'NOTIFY_SOCKET':'/fake-notify'}), \
             patch.object(service,'load_sibling',side_effect=lambda filename,name:modules[filename]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(service.serve(),75)

    def test_missing_database_refuses_without_calling_arbiter(self):
        class Transport:
            class MailboxError(RuntimeError): pass
            def consume(self, db): raise self.MailboxError('missing private db')
        class Arbiter:
            def try_start(self,*args,**kwargs): raise AssertionError('must not reach arbiter')
        class Probe: pass
        modules={'tensor-gpu-wallpaper-arbiter.py':Arbiter(),
                 'tensor-gpu-probe.py':Probe(),
                 'tensor-gpu-restore-mailbox.py':Transport()}
        with patch.dict('os.environ', {'NOTIFY_SOCKET':'/fake-notify'}), \
             patch.object(service,'load_sibling',side_effect=lambda filename,name:modules[filename]):
            with self.assertRaisesRegex(service.SupervisorError,'transport unavailable'):
                service.serve()

if __name__ == '__main__': unittest.main()
