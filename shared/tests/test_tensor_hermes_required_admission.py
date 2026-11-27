"""Source-only contract for the pinned Tensor Hermes fail-closed middleware patch.

Run: HERMES_SOURCE=/path/to/patched/hermes-agent python3 -m unittest discover
     -s shared/tests -p test_tensor_hermes_required_admission.py -v
Provider stand-ins always raise; no GPU, model request or fake completion occurs.
"""
from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
import importlib.util
import os
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import patch


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {name: module}):
        spec.loader.exec_module(module)
    return module


class ProviderReached(Exception):
    """A denied request reached the provider (test failure)."""


class RequiredAdmissionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = os.environ.get('HERMES_SOURCE')
        if not source:
            raise RuntimeError('HERMES_SOURCE must point at patched pinned Hermes source')
        source = Path(source)
        cls.middleware = load_module('test_required_middleware', source / 'hermes_cli/middleware.py')
        tree = ast.parse((source / 'agent/turn_api_call.py').read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == 'perform_api_call')
        namespace = {'__name__': 'test_required_turn', 'nullcontext': nullcontext,
                     '_should_stream': lambda agent: agent.streaming,
                     'ApiCallVerdict': lambda **kw: kw}
        exec(compile(ast.Module(body=[function], type_ignores=[]),
                     str(source / 'agent/turn_api_call.py'), 'exec'), namespace)
        cls.perform = staticmethod(namespace['perform_api_call'])

    def setUp(self):
        self.callbacks = []
        manager = types.SimpleNamespace(_middleware={'llm_execution': self.callbacks},
                                        _report_hook_failure=lambda *a, **kw: None)
        plugins = types.ModuleType('hermes_cli.plugins')
        setattr(plugins, '_delivery_manager', lambda: manager)
        relay = types.ModuleType('agent.relay_llm')
        setattr(relay, 'execute', lambda payload, provider, **kwargs: provider(payload))
        agent_pkg = types.ModuleType('agent')
        setattr(agent_pkg, 'relay_llm', relay)
        modules = patch.dict(sys.modules, {
            'hermes_cli': types.ModuleType('hermes_cli'),
            'hermes_cli.plugins': plugins,
            'hermes_cli.middleware': self.middleware,
            'agent': agent_pkg, 'agent.relay_llm': relay,
        })
        modules.start()
        self.addCleanup(modules.stop)
        self.reached = []

    def attempt(self, name, *, streaming=False, base_url='http://127.0.0.1:8080/v1', provider_name='custom'):
        def provider(request):
            self.reached.append(name)
            raise ProviderReached(name)
        agent = types.SimpleNamespace(
            streaming=streaming, api_mode='chat_completions',
            _interruptible_streaming_api_call=lambda request, **kw: provider(request),
            _interruptible_api_call=provider, _model_request_active=None,
            _pending_redirect_lock=None, _has_pending_redirect=lambda: False,
            session_id='synthetic', platform='test', model='qwen',
            is_subagent=False, _fallback_index=0, provider=provider_name, base_url=base_url)
        return self.perform(agent, api_kwargs={'id': name}, _original_api_kwargs={'id': name},
                            _llm_middleware_trace=[], _moa_prepared_request=None,
                            _retry=None, thinking_spinner=None, retry_count=0,
                            api_call_count=1, api_request_id=name, effective_task_id=None,
                            turn_id=None, interrupted=False)

    def policy(self, behavior):
        def callback(*, request, next_call, **context):
            if behavior == 'deny':
                raise RuntimeError('GPU unavailable')
            if behavior == 'return':
                return {'fabricated': True}
            if behavior == 'catch':
                try:
                    next_call(request)
                except Exception:
                    return {'fabricated': True}
            return next_call(request)
        setattr(callback, 'tensor_gpu_admission_policy', True)
        return callback

    def test_missing_policy_denies_both_transport_modes(self):
        for streaming in (False, True):
            with self.subTest(streaming=streaming), self.assertRaises(self.middleware.GpuAdmissionRequired):
                self.attempt(f'missing-{streaming}', streaming=streaming)
        self.assertEqual(self.reached, [])

    def test_local_ollama_route_requires_policy(self):
        for provider in ('ollama', 'custom'):
            with self.subTest(provider=provider), self.assertRaises(self.middleware.GpuAdmissionRequired):
                self.attempt('ollama-' + provider, provider_name=provider,
                             base_url='http://127.0.0.1:11434/v1')
        self.assertEqual(self.reached, [])

    def test_denial_never_reaches_provider(self):
        self.callbacks.append(self.policy('deny'))
        for streaming in (False, True):
            with self.subTest(streaming=streaming), self.assertRaises(self.middleware.GpuAdmissionRequired):
                self.attempt(f'denied-{streaming}', streaming=streaming)
        self.assertEqual(self.reached, [])

    def test_fake_result_and_bad_order_fail_closed(self):
        self.callbacks.append(self.policy('return'))
        with self.assertRaises(self.middleware.GpuAdmissionRequired):
            self.attempt('fake')
        self.assertEqual(self.reached, [])
        self.callbacks.insert(0, lambda **kw: kw['next_call'](kw['request']))
        with self.assertRaises(self.middleware.GpuAdmissionRequired):
            self.attempt('out-of-order')
        self.assertEqual(self.reached, [])

    def test_admitted_call_reaches_provider_once_in_both_modes(self):
        self.callbacks.append(self.policy('allow'))
        for streaming in (False, True):
            with self.subTest(streaming=streaming), self.assertRaises(ProviderReached):
                self.attempt(f'allowed-{streaming}', streaming=streaming)
        self.assertEqual(self.reached, ['allowed-False', 'allowed-True'])

    def test_policy_cannot_hide_downstream_failure_as_success(self):
        self.callbacks.append(self.policy('catch'))
        with self.assertRaises(self.middleware.GpuAdmissionRequired):
            self.attempt('hidden-provider-error')
        self.assertEqual(self.reached, ['hidden-provider-error'])

    def test_concurrent_denials_are_fenced(self):
        barrier = threading.Barrier(2)
        def callback(*, request, next_call, **context):
            barrier.wait(timeout=3)
            raise RuntimeError('GPU unavailable')
        setattr(callback, 'tensor_gpu_admission_policy', True)
        self.callbacks.append(callback)
        def attempt(i):
            with self.assertRaises(self.middleware.GpuAdmissionRequired):
                self.attempt(f'concurrent-{i}', streaming=bool(i))
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(attempt, i) for i in range(2)]
            for future in futures:
                future.result(timeout=5)
        self.assertEqual(self.reached, [])


if __name__ == '__main__':
    unittest.main()
