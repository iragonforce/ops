"""Negative contract tests against a pinned Hermes source checkout; no GPU or model calls.

Run: HERMES_SOURCE=/path/to/hermes-agent python3 -m unittest discover -s shared/tests -p test_tensor_hermes_middleware_admission.py -v
The provider stand-in ALWAYS raises ProviderReached: reaching it is the failure this
suite proves, never a fabricated successful model response. These tests are
expected to pass only as a demonstration of the unsafe upstream behavior.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import ast
from contextlib import nullcontext
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch


LEASE = Path(__file__).resolve().parents[1] / 'scripts' / 'tensor-gpu-lease.py'


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {name: module}):
        spec.loader.exec_module(module)
    return module


class ProviderReached(Exception):
    """The blocked request crossed the admission boundary."""


class Backend:
    def __init__(self, *, safe=True):
        self.safe = safe
        self.wallpaper = False

    def wallpaper_active(self): return self.wallpaper
    def stop_wallpaper(self): self.wallpaper = False
    def start_wallpaper(self): self.wallpaper = True
    def safe_to_acquire(self): return self.safe
    def inference_memory_released(self): return True


class MiddlewareAdmissionFailure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = os.environ.get('HERMES_SOURCE')
        if not source:
            raise RuntimeError('Set HERMES_SOURCE to the pinned Hermes source checkout')
        source = Path(source)
        cls.middleware = load_file('tensor_test_hermes_middleware', source / 'hermes_cli/middleware.py')
        cls.lease_module = load_file('tensor_test_lease', LEASE)
        # Execute the actual upstream request-boundary function, not a copied
        # approximation; isolate its imports so no agent or service starts.
        tree = ast.parse((source / 'agent/turn_api_call.py').read_text())
        function = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == 'perform_api_call')
        namespace = {'__name__': 'tensor_test_turn_api_call',
                     'nullcontext': nullcontext, '_should_stream': lambda agent: agent.streaming,
                     'ApiCallVerdict': lambda **kwargs: kwargs}
        exec(compile(ast.Module(body=[function], type_ignores=[]),
                     str(source / 'agent/turn_api_call.py'), 'exec'), namespace)
        cls.perform_api_call = staticmethod(namespace['perform_api_call'])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lease = self.lease_module.LeaseManager(
            Path(self.tmp.name) / 'private' / 'lease.db', Backend())
        self.addCleanup(self.lease.close)
        self.callbacks = []
        manager = types.SimpleNamespace(
            _middleware={'llm_execution': self.callbacks},
            _report_hook_failure=lambda *a, **kw: None,
        )
        plugins = types.ModuleType('hermes_cli.plugins')
        setattr(plugins, '_delivery_manager', lambda: manager)
        relay = types.ModuleType('agent.relay_llm')
        setattr(relay, 'execute', lambda payload, provider, **kwargs: provider(payload))
        agent_pkg = types.ModuleType('agent')
        setattr(agent_pkg, 'relay_llm', relay)
        self.modules = patch.dict(sys.modules, {
            'hermes_cli': types.ModuleType('hermes_cli'),
            'hermes_cli.plugins': plugins,
            'hermes_cli.middleware': self.middleware,
            'agent': agent_pkg,
            'agent.relay_llm': relay,
        })
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.reached = []

    def attempt(self, request, *, streaming=False):
        def provider(payload):
            self.reached.append((payload['id'], streaming))
            raise ProviderReached(payload['id'])
        agent = types.SimpleNamespace(
            streaming=streaming, api_mode='chat_completions',
            _interruptible_streaming_api_call=lambda payload, **kwargs: provider(payload),
            _interruptible_api_call=provider,
            _model_request_active=None, _pending_redirect_lock=None,
            _has_pending_redirect=lambda: False,
            session_id='synthetic', platform='test', model='qwen',
            is_subagent=False, _fallback_index=0,
            provider='custom', base_url='http://127.0.0.1:8080/v1',
        )
        return self.perform_api_call(
            agent, api_kwargs=request, _original_api_kwargs=request,
            _llm_middleware_trace=[], _moa_prepared_request=None,
            _retry=None, thinking_spinner=None, retry_count=0,
            api_call_count=1, api_request_id=request['id'], effective_task_id=None,
            turn_id=None, interrupted=False)

    def test_incompatible_resource_denial_is_skipped_in_both_modes(self):
        token = self.lease.acquire('existing', 'embedding-8b', activity='active', foreground=True)
        def admit(*, request, next_call, **context):
            held = self.lease.acquire('hermes', 'qwen', activity='active', foreground=True)
            try:
                return next_call(request)
            finally:
                self.lease.release(held)
        self.callbacks.append(admit)
        for stream in (False, True):
            with self.subTest(stream=stream), self.assertRaises(ProviderReached):
                self.attempt({'id': f'incompatible-{stream}'}, streaming=stream)
        self.assertEqual(self.lease.status()['leases'], 1)
        self.assertEqual(len(self.reached), 2)
        self.lease.release(token)

    def test_unknown_owner_denial_is_skipped(self):
        # The existing lease's live path requires a trusted Linux identity.
        self.lease.require_identity = True
        def admit(*, request, next_call, **context):
            held = self.lease.acquire('hermes', 'qwen', activity='active', foreground=True,
                                      identity=None)
            try:
                return next_call(request)
            finally:
                self.lease.release(held)
        self.callbacks.append(admit)
        with self.assertRaises(ProviderReached):
            self.attempt({'id': 'unknown-owner'})
        self.assertEqual(self.lease.status()['leases'], 0)
        self.assertEqual(self.reached, [('unknown-owner', False)])

    def test_concurrent_denials_both_cross_boundary(self):
        token = self.lease.acquire('existing', 'embedding-8b', activity='active', foreground=True)
        barrier = threading.Barrier(2)
        def admit(*, request, next_call, **context):
            barrier.wait(timeout=3)
            held = self.lease.acquire('hermes', 'qwen', activity='active', foreground=True)
            try:
                return next_call(request)
            finally:
                self.lease.release(held)
        self.callbacks.append(admit)
        def attempt(n):
            with self.assertRaises(ProviderReached):
                self.attempt({'id': f'concurrent-{n}'}, streaming=bool(n))
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(attempt, n) for n in range(2)]
            for future in futures:
                future.result(timeout=5)
        self.assertEqual(self.lease.status()['leases'], 1)
        self.assertEqual({name for name, _ in self.reached}, {'concurrent-0', 'concurrent-1'})
        self.lease.release(token)

    def test_unidentified_gpu_backend_denial_is_skipped(self):
        self.lease.backend.safe = False
        def admit(*, request, next_call, **context):
            self.lease.acquire('hermes', 'qwen', activity='active', foreground=True)
            return next_call(request)
        self.callbacks.append(admit)
        with self.assertRaises(ProviderReached):
            self.attempt({'id': 'unknown-gpu'})
        self.assertEqual(self.lease.status()['mode'], 'preparing')
        self.assertEqual(self.reached, [('unknown-gpu', False)])


if __name__ == '__main__':
    unittest.main()
