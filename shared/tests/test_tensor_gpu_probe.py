"""Offline, fail-closed tests; fake services/NVIDIA/Ollama only."""
import importlib.util
from pathlib import Path
import tempfile
import os
import sys
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'tensor-gpu-probe.py'
spec = importlib.util.spec_from_file_location('tensor_gpu_probe', SCRIPT)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class Fake:
    def __init__(self):
        self.wallpaper = 'inactive'
        self.llama = 'inactive'
        self.gpu = '12227, 1631, 10596'
        self.compute = ''
        self.loaded = 0
        self.raise_cuda = False

    def run(self, argv):
        arg = ' '.join(argv)
        if 'wallpaper-engine-sync.service' in arg:
            return self.wallpaper
        if 'hermes-llama.service' in arg:
            return self.llama
        if '--query-gpu=' in arg:
            return self.gpu
        if '--query-compute-apps=' in arg:
            if self.raise_cuda:
                raise OSError('NVIDIA query unsupported')
            return self.compute
        raise AssertionError('Unexpected command ' + repr(argv))

    def models(self):
        return self.loaded


class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.proc = Path(self.temp.name)
        self.f = Fake()

    def check(self, **kwargs):
        return mod.probe(run=self.f.run, models=self.f.models, proc_root=self.proc, **kwargs)

    def test_clear_candidate_never_invokes_mutating_command(self):
        result = self.check()
        self.assertTrue(result['admission_candidate'])
        self.assertEqual(result['mode'], 'read-only')
        self.assertEqual(result['reasons'], [])

    def test_loaded_qwen_denied(self):
        self.f.llama = 'active'
        self.f.gpu = '12227, 10590, 1242'
        result = self.check()
        self.assertFalse(result['admission_candidate'])
        self.assertIn('hermes_llama_not_inactive', result['reasons'])
        self.assertIn('insufficient_free_vram', result['reasons'])

    def test_running_wallpaper_denied(self):
        self.f.wallpaper = 'active'
        self.assertIn('wallpaper_supervisor_not_inactive', self.check()['reasons'])

    def test_visible_wallpaper_child_denied(self):
        pid_dir = self.proc / '12345'
        pid_dir.mkdir()
        (pid_dir / 'cmdline').write_bytes(b'./linux-wallpaperengine\x00--bg\x00assets\x00')
        self.assertEqual(self.check()['evidence']['wallpaper_child_pids'], [12345])
        self.assertIn('wallpaper_children_running', self.check()['reasons'])

    def test_ollama_residency_denied(self):
        self.f.loaded = 1
        self.assertIn('ollama_models_loaded', self.check()['reasons'])

    def test_cuda_compute_denied(self):
        self.f.compute = '1234, 9711\n5678, 99'
        result = self.check()
        self.assertIn('cuda_compute_processes_present', result['reasons'])
        self.assertEqual(result['evidence']['cuda_compute_pids'], [1234, 5678])

    def test_unavailable_cuda_inventory_fails_closed(self):
        self.f.raise_cuda = True
        result = self.check()
        self.assertFalse(result['admission_candidate'])
        self.assertIn('unverified:cuda_compute_pids', result['reasons'])

    def test_malformed_gpu_data_fails_closed(self):
        self.f.gpu = 'N/A, N/A, N/A'
        result = self.check()
        self.assertFalse(result['admission_candidate'])
        self.assertIn('unverified:gpu_memory', result['reasons'])

    def test_unsupported_multi_gpu_fails_closed(self):
        self.f.gpu = '12227, 1631, 10596\n24464, 1000, 23464'
        self.assertFalse(self.check()['admission_candidate'])

    def test_threshold_is_not_authority_to_execute(self):
        self.assertTrue(self.check(required_free_mib=10000)['admission_candidate'])
        self.assertFalse(self.check(required_free_mib=11000)['admission_candidate'])

    def test_query_failure_does_not_hide_other_evidence(self):
        self.f.llama = 'active'
        self.f.raise_cuda = True
        result = self.check()
        self.assertFalse(result['admission_candidate'])
        self.assertIn('hermes_llama_not_inactive', result['reasons'])
        self.assertIn('unverified:cuda_compute_pids', result['reasons'])


if __name__ == '__main__':
    unittest.main()
