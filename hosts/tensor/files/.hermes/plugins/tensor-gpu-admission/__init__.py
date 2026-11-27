"""Tensor local llama admission; no direct model or desktop bypass.

Source: iragonforce/ops. Dependencies: sibling Git-owned tensor-gpu-queue.py,
tensor-gpu-lease.py, tensor-gpu-systemd-adapter.py and tensor-gpu-probe.py
installed under ~/.local/share/tensor-gpu. The existing systemd units remain
the only model/wallpaper supervisors. Missing or uncertain evidence denies.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener
from contextlib import contextmanager

SCRIPTS = Path.home() / '.local/share/tensor-gpu'
STATE = Path.home() / '.local/state/tensor-gpu-queue'
LEASE_DB = Path.home() / '.local/state/tensor-gpu-lease/queue.sqlite3'
LOG = logging.getLogger('tensor_gpu_admission')


@contextmanager
def _stage(name):
    try:
        yield
    except Exception as exc:
        # Do not log prompts, provider exceptions, tokens, or subprocess output.
        LOG.warning('Tensor admission %s failed (%s)', name, type(exc).__name__)
        raise


def _module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Tensor GPU component unavailable: {filename}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _systemctl(*args: str) -> str:
    done = subprocess.run(['/usr/bin/systemctl', '--user', *args],
                          capture_output=True, text=True, timeout=90, check=True)
    return done.stdout.strip()


def _identity(lease):
    pid = os.getpid()
    stat = (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()
    return lease.OwnerIdentity(Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                               pid, int(stat[19]))


def _wait_health():
    opener = build_opener(ProxyHandler({}))
    until = time.monotonic() + 90
    while time.monotonic() < until:
        try:
            with opener.open(Request('http://127.0.0.1:8080/health', method='GET'),
                             timeout=2) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        time.sleep(1)
    raise RuntimeError('Admitted llama failed to become healthy')


def _stop_ollama_model(model):
    # OpenAI-compatible completions cannot set Ollama keep_alive. Never force
    # stop a model that an unguarded direct client might also be using. Wait
    # through Ollama's normal idle unload, retaining the lease if it persists.
    for _ in range(120):
        if model not in [x.get('name') for x in _ollama_metadata('/api/ps').get('models', [])]:
            return
        time.sleep(3)
    raise RuntimeError('Admitted Ollama model remains resident; GPU lease retained')


def _admitted_call(request, next_call, *, platform: str, ollama_model: str | None = None):
    queue = _module('tensor_gpu_queue_runtime', 'tensor-gpu-queue.py')
    lease = _module('tensor_gpu_lease_runtime', 'tensor-gpu-lease.py')
    desktop = _module('tensor_gpu_systemd_runtime', 'tensor-gpu-systemd-adapter.py')
    # Opening the existing queue creates its protected directory. The existing
    # worker.lock serializes interactive calls with admitted embedding/PDF work.
    with queue.Queue(STATE / 'queue.sqlite3'):
        with queue.worker_lock(STATE, wait=True):
            with lease.LeaseManager(LEASE_DB, desktop.TensorSleepAwareBackend(),
                                    require_identity=True) as manager:
                # A CLI request is explicit foreground use. Remote/background
                # work needs the existing visual-standby marker; not a guess
                # from a systemd active state or absence of Ollama models.
                foreground = platform == 'cli'
                activity = ('idle' if Path('/run/user/1000/tensor-visual-standby.json').exists()
                            else 'active')
                with _stage('acquire'):
                    token = manager.acquire('hermes-local',
                                            'ollama:' + ollama_model if ollama_model else 'qwen3.8-27b-iq3',
                                            activity=activity, foreground=foreground,
                                            identity=_identity(lease))
                try:
                    with _stage('startup'):
                        if not ollama_model:
                            state = _systemctl('show', 'hermes-llama.service',
                                               '--property=ActiveState', '--value')
                            if state not in ('active', 'inactive', 'failed'):
                                raise RuntimeError('Unverified llama service state')
                            if state != 'active':
                                _systemctl('start', 'hermes-llama.service')
                            _wait_health()
                        manager.enforce()
                    with _stage('provider'):
                        return next_call(request)
                finally:
                    # Do not restore wallpaper until systemd has actually
                    # released GPU model memory. On a failed stop the durable
                    # lease remains reserved for explicit recovery.
                    with _stage('cleanup'):
                        if ollama_model:
                            _stop_ollama_model(ollama_model)
                        else:
                            _systemctl('stop', 'hermes-llama.service')
                        manager.release(token)


def llm_execution(*, request, next_call, provider='', base_url='', platform='', model='', **_):
    url = urlsplit(str(base_url or ''))
    local = (url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost')
             and url.path.rstrip('/') == '/v1')
    if not local or provider not in ('custom', 'ollama') or url.port not in (8080, 11434):
        return next_call(request)
    if url.port == 8080:
        return _admitted_call(request, next_call, platform=platform)
    name = str(model or (request.get('model') if isinstance(request, dict) else '')).removeprefix('ollama/')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}', name):
        raise ValueError('Invalid local Ollama model')
    if name not in [x.get('name') for x in _ollama_metadata('/api/tags').get('models', [])]:
        raise ValueError('Model is not installed on Tensor')
    return _admitted_call(request, next_call, platform=platform, ollama_model=name)


setattr(llm_execution, 'tensor_gpu_admission_policy', True)


def _ollama_metadata(endpoint):
    opener = build_opener(ProxyHandler({}))
    with opener.open(f'http://127.0.0.1:11434{endpoint}', timeout=3) as response:
        return json.loads(response.read(65537))


def tensor_gpu_status(_args, **_):
    """Read fixed local status commands only; never probe llama /slots."""
    try:
        gpu = subprocess.run(['/usr/bin/nvidia-smi', '--query-gpu=memory.used,memory.free,utilization.gpu',
                              '--format=csv,noheader,nounits'], capture_output=True, text=True,
                             timeout=4, check=True).stdout.strip()
        models = [x.get('name', '') for x in _ollama_metadata('/api/ps').get('models', [])]
        return json.dumps({'gpu_used_free_utilization': gpu[:100],
                           'llama': _systemctl('show', 'hermes-llama.service',
                                               '--property=ActiveState', '--value'),
                           'wallpaper': _systemctl('show', 'wallpaper-engine-sync.service',
                                                   '--property=ActiveState', '--value'),
                           'visual_standby': Path('/run/user/1000/tensor-visual-standby.json').exists(),
                           'ollama_resident': models[:16]})
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return f'Tensor status unavailable ({type(exc).__name__})'


def tensor_local_models(_args, **_):
    """List only the local Ollama catalog; no hosted model/API probe."""
    try:
        return json.dumps([x.get('name', '') for x in _ollama_metadata('/api/tags').get('models', [])][:100])
    except (OSError, ValueError) as exc:
        return f'Local model catalog unavailable ({type(exc).__name__})'


def register(ctx):
    ctx.register_middleware('llm_execution', llm_execution)
    params = {'type': 'object', 'properties': {}, 'additionalProperties': False}
    for name, description, handler in (
        ('tensor_gpu_status', 'Read-only local GPU, llama, wallpaper and visual-standby status.', tensor_gpu_status),
        ('tensor_local_models', 'List model names from this Tensor host\'s Ollama only.', tensor_local_models),
    ):
        ctx.register_tool(name=name, toolset='tensor_readonly', handler=handler,
                          schema={'name': name, 'description': description, 'parameters': params})
