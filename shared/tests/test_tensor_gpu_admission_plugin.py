"""Bounded offline checks for the actual Tensor Hermes policy callback; no GPU or service calls."""
import contextlib
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

SOURCE = (Path(__file__).resolve().parents[2] / 'hosts/tensor/files/.hermes/plugins'
          / 'tensor-gpu-admission/__init__.py')
spec = importlib.util.spec_from_file_location('tensor_gpu_admission_plugin', SOURCE)
assert spec is not None and spec.loader is not None
plugin = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = plugin
spec.loader.exec_module(plugin)


class PolicyTest(unittest.TestCase):
    def test_registration_and_other_route(self):
        calls = []
        tools = []
        plugin.register(types.SimpleNamespace(
            register_middleware=lambda kind, cb: calls.append((kind, cb)),
            register_tool=lambda **kw: tools.append(kw)))
        self.assertEqual(calls, [('llm_execution', plugin.llm_execution)])
        self.assertTrue(getattr(calls[0][1], 'tensor_gpu_admission_policy'))
        self.assertEqual([x['name'] for x in tools], ['tensor_gpu_status', 'tensor_local_models'])
        self.assertTrue(all(x['toolset'] == 'tensor_readonly' for x in tools))
        request = {'model': 'unrelated'}
        self.assertIs(plugin.llm_execution(request=request, next_call=lambda r: r,
                                           provider='custom', base_url='http://127.0.0.1:9999/v1'), request)

    def test_protected_route_uses_policy(self):
        marker = object()
        with patch.object(plugin, '_admitted_call', return_value=marker) as admitted:
            self.assertIs(plugin.llm_execution(request={}, next_call=lambda r: None,
                                               provider='custom', platform='cli',
                                               base_url='http://localhost:8080/v1?x=1'), marker)
        admitted.assert_called_once()

    def test_local_ollama_catalog_and_policy(self):
        marker = object()
        catalog = {'models': [{'name': 'qwen3.5:27b'}]}
        with (patch.object(plugin, '_ollama_metadata', return_value=catalog),
              patch.object(plugin, '_admitted_call', return_value=marker) as admitted):
            self.assertIs(plugin.llm_execution(request={'model': 'qwen3.5:27b'},
                                               next_call=lambda _: None, provider='ollama',
                                               base_url='http://localhost:11434/v1', platform='cli'), marker)
            admitted.assert_called_once()
            self.assertEqual(admitted.call_args.kwargs['ollama_model'], 'qwen3.5:27b')
            with self.assertRaises(ValueError):
                plugin.llm_execution(request={}, next_call=lambda _: None, model='missing:1',
                                     provider='custom', base_url='http://localhost:11434/v1')

    def test_start_provider_stop_release_in_order(self):
        events = []
        class Resource:
            def __enter__(self): return self
            def __exit__(self, *_): pass
        class FakeManager(Resource):
            def __init__(self, *_, **__): pass
            def acquire(self, *_, **__): events.append('acquire'); return 'lease-token'
            def enforce(self): events.append('enforce')
            def release(self, token): events.append(('release', token))
        fake_queue = types.SimpleNamespace(Queue=lambda *_: Resource(),
                                           worker_lock=lambda *_, **__: contextlib.nullcontext())
        fake_lease = types.SimpleNamespace(LeaseManager=FakeManager)
        fake_backend = types.SimpleNamespace(TensorSleepAwareBackend=lambda: object())
        components = {'tensor_gpu_queue_runtime': fake_queue,
                      'tensor_gpu_lease_runtime': fake_lease,
                      'tensor_gpu_systemd_runtime': fake_backend}
        def systemctl(*args):
            events.append(args[0]); return 'inactive' if args[0] == 'show' else ''
        with (patch.object(plugin, '_module', side_effect=lambda name, _: components[name]),
              patch.object(plugin, '_identity', return_value=object()),
              patch.object(plugin, '_systemctl', side_effect=systemctl),
              patch.object(plugin, '_wait_health', side_effect=lambda: events.append('healthy'))):
            result = plugin._admitted_call({}, lambda _: events.append('provider') or 'result',
                                           platform='cli')
        self.assertEqual(result, 'result')
        self.assertEqual(events, ['acquire', 'show', 'start', 'healthy', 'enforce',
                                  'provider', 'stop', ('release', 'lease-token')])


if __name__ == '__main__': unittest.main()
