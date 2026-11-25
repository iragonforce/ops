"""Stage 2C adapter contract tests: all systemd and NVIDIA evidence are fake."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'tensor-gpu-systemd-adapter.py'
spec = importlib.util.spec_from_file_location('tensor_gpu_systemd_adapter', SCRIPT)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class FakeState:
    def __init__(self, *, wallpaper='active', children=None, qwen=False,
                 ollama=0, cuda=None, free=10596, broken=False):
        self.wallpaper = wallpaper
        self.children = [101,102] if children is None and wallpaper=='active' else (children or [])
        self.qwen = qwen
        self.ollama = ollama
        self.cuda = cuda or ([1010] if qwen else [])
        self.free = free
        self.broken = broken
        self.calls = []
        self.fail_stop = False
        self.fail_start = False
        self.restart_external = False

    def observe(self):
        if self.broken:
            return {'mode':'read-only', 'reasons': ['unverified:gpu_memory'],
                    'evidence':{'wallpaper_service':self.wallpaper}}
        reasons = []
        if self.wallpaper != 'inactive': reasons.append('wallpaper_supervisor_not_inactive')
        if self.children: reasons.append('wallpaper_children_running')
        if self.qwen: reasons.append('hermes_llama_not_inactive')
        if self.cuda: reasons.append('cuda_compute_processes_present')
        if self.ollama: reasons.append('ollama_models_loaded')
        if self.free < 10200: reasons.append('insufficient_free_vram')
        return {'mode':'read-only','admission_candidate':not reasons, 'reasons':reasons,
                'evidence':{
                    'wallpaper_service':self.wallpaper,
                    'wallpaper_child_pids':list(self.children),
                    'hermes_llama_service':'active' if self.qwen else 'inactive',
                    'cuda_compute_pids':list(self.cuda),
                    'gpu_memory':{'total_mib':12227,'used_mib':12227-self.free,'free_mib':self.free},
                    'ollama_loaded_models':self.ollama}}

    def run(self, argv):
        self.calls.append(argv)
        self_test = ['/usr/bin/systemctl','--user']
        if argv[:2] != self_test or len(argv)!=4 or argv[3]!=mod.WALLPAPER_UNIT:
            raise AssertionError('Unexpected service request')
        if argv[2]=='stop':
            if self.fail_stop: raise RuntimeError('fake stop failure')
            self.wallpaper='inactive'; self.children=[]
        elif argv[2]=='start':
            if self.fail_start: raise RuntimeError('fake start failure')
            self.wallpaper='active'; self.children=[201,202]
        else: raise AssertionError('Unexpected action')
        return ''

    def backend(self):
        return mod.TensorDesktopBackend(run=self.run,observe=self.observe)


class AdapterTest(unittest.TestCase):
    def test_read_only_snapshot_no_systemd_calls(self):
        f=FakeState(qwen=True,free=1242)
        result=f.backend().snapshot()
        self.assertIn('cuda_compute_processes_present',result['reasons'])
        self.assertEqual(f.calls,[])

    def test_stop_scoped_and_verifies_children(self):
        f=FakeState(); b=f.backend()
        b.stop_wallpaper()
        self.assertEqual(f.wallpaper,'inactive')
        self.assertEqual(f.children,[])
        self.assertEqual(f.calls,[['/usr/bin/systemctl','--user','stop',mod.WALLPAPER_UNIT]])

    def test_stop_when_already_inactive_is_noop(self):
        f=FakeState(wallpaper='inactive'); f.backend().stop_wallpaper()
        self.assertEqual(f.calls,[])

    def test_start_scoped(self):
        f=FakeState(wallpaper='inactive'); f.backend().start_wallpaper()
        self.assertEqual(f.wallpaper,'active')
        self.assertEqual(f.calls,[['/usr/bin/systemctl','--user','start',mod.WALLPAPER_UNIT]])

    def test_start_when_active_is_noop(self):
        f=FakeState();f.backend().start_wallpaper()
        self.assertEqual(f.calls,[])

    def test_stop_failure_propagates(self):
        f=FakeState(); f.fail_stop=True
        with self.assertRaises(RuntimeError): f.backend().stop_wallpaper()
        self.assertEqual(f.wallpaper,'active')

    def test_start_failure_propagates(self):
        f=FakeState(wallpaper='inactive');f.fail_start=True
        with self.assertRaises(RuntimeError): f.backend().start_wallpaper()
        self.assertEqual(f.wallpaper,'inactive')

    def test_orphan_wallpaper_refused(self):
        f=FakeState(wallpaper='inactive',children=[99])
        with self.assertRaises(mod.AdapterError): f.backend().wallpaper_active()
        self.assertEqual(f.calls,[])

    def test_unstable_wallpaper_refused(self):
        f=FakeState(wallpaper='activating')
        with self.assertRaises(mod.AdapterError): f.backend().stop_wallpaper()
        self.assertEqual(f.calls,[])

    def test_unknown_inventory_fails_closed(self):
        f=FakeState(broken=True)
        with self.assertRaises(mod.AdapterError): f.backend().snapshot()

    def test_gpu_blocked_by_existing_qwen(self):
        f=FakeState(wallpaper='inactive',qwen=True,free=1242)
        b=f.backend()
        self.assertFalse(b.safe_to_acquire())
        self.assertFalse(b.inference_memory_released())

    def test_gpu_blocked_by_ollama(self):
        f=FakeState(wallpaper='inactive',ollama=1)
        self.assertFalse(f.backend().safe_to_acquire())

    def test_gpu_blocked_by_uncoordinated_cuda(self):
        f=FakeState(wallpaper='inactive',cuda=[299])
        self.assertFalse(f.backend().safe_to_acquire())

    def test_gpu_blocked_by_low_memory(self):
        f=FakeState(wallpaper='inactive',free=999)
        self.assertFalse(f.backend().safe_to_acquire())

    def test_gpu_can_be_candidate_only_after_scoped_stop(self):
        f=FakeState(); b=f.backend()
        self.assertFalse(b.safe_to_acquire())
        b.stop_wallpaper()
        self.assertTrue(b.safe_to_acquire())
        self.assertTrue(b.inference_memory_released())

    def test_restart_during_lease_detected_in_new_snapshot(self):
        f=FakeState(wallpaper='inactive'); b=f.backend()
        self.assertTrue(b.inference_memory_released())
        f.wallpaper='active';f.children=[10]
        self.assertFalse(b.inference_memory_released())

    def test_no_real_process_commands_in_test(self):
        f=FakeState(); b=f.backend()
        b.stop_wallpaper();b.start_wallpaper()
        self.assertEqual(len(f.calls),2)
        self.assertTrue(all(c[:3] in (["/usr/bin/systemctl","--user","stop"],
                                      ["/usr/bin/systemctl","--user","start"]) for c in f.calls))


if __name__ == '__main__':
    unittest.main()
