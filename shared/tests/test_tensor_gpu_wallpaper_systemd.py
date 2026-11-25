"""Stage 2E source-only service-entrypoint contract; no real services/GPU."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'scripts/tensor-gpu-wallpaper-systemd.py'
spec = importlib.util.spec_from_file_location('tensor_gpu_wallpaper_systemd_test', SOURCE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class FakeProc:
    def __init__(self, exit_code=None):
        self.exit_code = exit_code
        self.pid = 214748
    def poll(self): return self.exit_code
    def wait(self, timeout=None): return self.exit_code


class FakeArbiter:
    def __init__(self, *, allow=True):
        self.allow = allow
        self.calls = []
    def try_start(self, db, launch, ready, abort, *, gpu_safe):
        self.calls.append('check_gpu')
        if not gpu_safe():
            return type('Decision', (), {'started': False, 'reason': 'gpu_veto'})()
        if not self.allow:
            return type('Decision', (), {'started': False, 'reason': 'lease_veto'})()
        self.calls.append('launch')
        launch()
        self.calls.append('ready')
        if not ready():
            self.calls.append('abort')
            abort()
            raise mod.SupervisorError('not ready')
        return type('Decision', (), {'started': True, 'reason': 'admitted'})()


def evidence(**overrides):
    e = dict(wallpaper_service='activating', hermes_llama_service='inactive',
             wallpaper_child_pids=[], cuda_compute_pids=[],
             ollama_loaded_models=0, gpu_memory={'free_mib':11000})
    e.update(overrides)
    return {'mode': 'read-only', 'evidence': e,
            'admission_candidate': False, 'reasons': ['wallpaper_supervisor_not_inactive']}


class EntryTest(unittest.TestCase):
    def test_activation_not_rejected_for_normal_probe_veto(self):
        self.assertTrue(mod.wallpaper_gpu_safe(evidence()))

    def test_active_hermes_veto(self):
        self.assertFalse(mod.wallpaper_gpu_safe(evidence(hermes_llama_service='active')))

    def test_compute_pid_veto(self):
        self.assertFalse(mod.wallpaper_gpu_safe(evidence(cuda_compute_pids=[100])))

    def test_wallpaper_child_veto(self):
        self.assertFalse(mod.wallpaper_gpu_safe(evidence(wallpaper_child_pids=[100])))

    def test_ollama_model_veto(self):
        self.assertFalse(mod.wallpaper_gpu_safe(evidence(ollama_loaded_models=1)))

    def test_low_memory_veto(self):
        self.assertFalse(mod.wallpaper_gpu_safe(evidence(gpu_memory={'free_mib':8000})))

    def test_unknown_or_missing_evidence_veto(self):
        self.assertFalse(mod.wallpaper_gpu_safe({}))
        self.assertFalse(mod.wallpaper_gpu_safe(evidence(gpu_memory=None)))
        self.assertFalse(mod.wallpaper_gpu_safe(evidence(hermes_llama_service='failed')))
        self.assertFalse(mod.wallpaper_gpu_safe(evidence(wallpaper_service='active')))

    def test_valid_launch_order_and_owned_process(self):
        a = FakeArbiter()
        calls = []
        d, p = mod.start_guarded(db=Path('/fake'), wallpaper=Path('/fake/sync'),
                                 arbiter=a, gpu_report=evidence,
                                 notify=lambda: calls.append('ready_sent'),
                                 spawn=lambda path: calls.append('spawn') or FakeProc(),
                                 startup_delay=0)
        self.assertTrue(d.started)
        self.assertEqual(a.calls, ['check_gpu', 'launch', 'ready'])
        self.assertEqual(calls, ['spawn', 'ready_sent'])
        self.assertIsNotNone(p)

    def test_gpu_veto_does_not_launch(self):
        a = FakeArbiter()
        d, p = mod.start_guarded(db=Path('/fake'), wallpaper=Path('/fake/sync'),
                                 arbiter=a, gpu_report=lambda: evidence(hermes_llama_service='active'),
                                 notify=lambda: self.fail('notify after veto'),
                                 spawn=lambda path: self.fail('spawn after veto'), startup_delay=0)
        self.assertFalse(d.started)
        self.assertIsNone(p)

    def test_lease_veto_does_not_launch(self):
        a = FakeArbiter(allow=False)
        d, p = mod.start_guarded(db=Path('/fake'), wallpaper=Path('/fake/sync'),
                                 arbiter=a, gpu_report=evidence,
                                 notify=lambda: self.fail('notify after veto'),
                                 spawn=lambda path: self.fail('spawn after veto'), startup_delay=0)
        self.assertFalse(d.started)
        self.assertIsNone(p)

    def test_child_early_exit_refuses_ready(self):
        a = FakeArbiter()
        with self.assertRaisesRegex(mod.SupervisorError, 'not ready'):
            mod.start_guarded(db=Path('/fake'), wallpaper=Path('/fake/sync'),
                              arbiter=a, gpu_report=evidence,
                              notify=lambda: self.fail('notify dead child'),
                              spawn=lambda path: FakeProc(exit_code=1), startup_delay=0)
        self.assertEqual(a.calls[-1], 'abort')

    def test_probe_exception_bubbles_to_arbiter_caller(self):
        a = FakeArbiter()
        with self.assertRaises(OSError):
            mod.start_guarded(db=Path('/fake'), wallpaper=Path('/fake/sync'),
                              arbiter=a, gpu_report=lambda: (_ for _ in ()).throw(OSError('gpu missing')),
                              notify=lambda: None, spawn=lambda path: FakeProc(), startup_delay=0)

    def test_missing_notify_socket_refused(self):
        with self.assertRaises(mod.SupervisorError):
            mod.send_ready('')

    def test_notification_datagram(self):
        with tempfile.TemporaryDirectory() as temp:
            name = str(Path(temp)/'notify.sock')
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as listener:
                listener.bind(name)
                listener.settimeout(2)
                mod.send_ready(name)
                msg = listener.recv(1024)
            self.assertIn(b'READY=1', msg)

    def test_read_only_default_and_help(self):
        cp = subprocess.run([sys.executable, str(SOURCE)], capture_output=True, text=True, check=True)
        self.assertFalse(json.loads(cp.stdout)['production_control_enabled'])
        cp = subprocess.run([sys.executable, str(SOURCE), '--help'], capture_output=True, text=True, check=True)
        self.assertIn('--serve', cp.stdout)

    def test_service_requires_notify_socket_before_import_or_spawn(self):
        with patch.dict(os.environ, {'NOTIFY_SOCKET': ''}):
            with self.assertRaises(mod.SupervisorError):
                mod.serve()


if __name__ == '__main__':
    unittest.main()
