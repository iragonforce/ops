#!/usr/bin/env python3
"""Read-only Tensor systemd/NVIDIA GPU admission evidence (Stage 2).

This probe never acquires leases, unloads models, stops wallpaper services,
starts services, launches a GPU job, or calls vram-purge. Its positive result
is *only* a candidate for future admission, not a permit to execute work.

Source: iragonforce/ops. Usage: tensor-gpu-probe.py --help
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable
from urllib.request import ProxyHandler, Request, build_opener

WALLPAPER_UNIT = 'wallpaper-engine-sync.service'
HERMES_UNIT = 'hermes-llama.service'
GPU_FIELDS = ['memory.total', 'memory.used', 'memory.free']
COMPUTE_FIELDS = ['pid', 'used_gpu_memory']
DEFAULT_REQUIRED_FREE_MIB = 10200  # Candidate threshold only; NOT automatic admission.


def command(args: list[str]) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True, timeout=5)
    return result.stdout.strip()


def ollama_models() -> int:
    # Explicit loopback and no inherited HTTP proxy; read-only Ollama endpoint.
    opener = build_opener(ProxyHandler({}))
    req = Request('http://127.0.0.1:11434/api/ps', method='GET')
    with opener.open(req, timeout=3) as response:
        data = json.load(response)
    if not isinstance(data, dict) or not isinstance(data.get('models'), list):
        raise ValueError('Unexpected Ollama model inventory')
    return len(data['models'])


def wallpaper_pids(proc_root: Path) -> list[int]:
    pids: list[int] = []
    for entry in proc_root.iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            if entry.stat().st_uid != os.geteuid():
                continue
            data = (entry / 'cmdline').read_bytes()
            if not data:
                continue
            binary = os.path.basename(data.split(b'\0', 1)[0].decode('utf-8', 'replace'))
            if binary == 'linux-wallpaperengine':
                pids.append(int(entry.name))
        except (FileNotFoundError, ProcessLookupError):
            # Processes can exit during enumeration; that's not an error.
            continue
        except (PermissionError, OSError) as exc:
            raise RuntimeError('Cannot verify user GPU wallpaper processes') from exc
    return sorted(pids)


def service_state(unit: str, run: Callable[[list[str]], str]) -> str:
    status = run(['/usr/bin/systemctl', '--user', 'show', unit, '--property=ActiveState', '--value']).strip()
    if status not in ('active', 'inactive', 'failed', 'activating', 'deactivating', 'reloading'):
        raise ValueError('Unrecognized systemd unit state')
    return status


def gpu_memory(run: Callable[[list[str]], str]) -> dict[str, int]:
    output = run(['/usr/bin/nvidia-smi', '--query-gpu=' + ','.join(GPU_FIELDS),
                  '--format=csv,noheader,nounits'])
    rows = [line.strip() for line in output.splitlines() if line.strip()]
    if len(rows) != 1:  # Refuse ambiguous multi-GPU setups until adapter supports them.
        raise ValueError('Expected exactly one GPU')
    items = [item.strip() for item in rows[0].split(',')]
    if len(items) != 3 or not all(item.isdecimal() for item in items):
        raise ValueError('Malformed NVIDIA memory fields')
    total, used, free = map(int, items)
    # NVIDIA may reserve some VRAM outside the used/free accounting. On
    # Tensor the observed difference was ~395 MiB; never treat it as free.
    reserve = total - used - free
    if min(total, used, free) < 0 or used > total or free > total or not (-32 <= reserve <= max(1024, total // 10)):
        raise ValueError('Inconsistent NVIDIA memory counters')
    return {'total_mib': total, 'used_mib': used, 'free_mib': free}


def compute_pids(run: Callable[[list[str]], str]) -> list[int]:
    output = run(['/usr/bin/nvidia-smi', '--query-compute-apps=' + ','.join(COMPUTE_FIELDS),
                  '--format=csv,noheader,nounits'])
    if not output.strip():
        return []
    pids: list[int] = []
    for line in output.splitlines():
        cells = [x.strip() for x in line.split(',')]
        if len(cells) != 2 or not cells[0].isdecimal() or not cells[1].isdecimal():
            raise ValueError('Malformed NVIDIA compute-process inventory')
        pids.append(int(cells[0]))
    return sorted(set(pids))


def probe(*, run: Callable[[list[str]], str] = command,
          models: Callable[[], int] = ollama_models,
          proc_root: Path = Path('/proc'), required_free_mib: int = DEFAULT_REQUIRED_FREE_MIB) -> dict:
    if required_free_mib < 1:
        raise ValueError('Required free MiB must be positive')
    evidence: dict = {}
    failed: list[str] = []
    for key, fn in (
        ('wallpaper_service', lambda: service_state(WALLPAPER_UNIT, run)),
        ('hermes_llama_service', lambda: service_state(HERMES_UNIT, run)),
        ('wallpaper_child_pids', lambda: wallpaper_pids(proc_root)),
        ('gpu_memory', lambda: gpu_memory(run)),
        ('cuda_compute_pids', lambda: compute_pids(run)),
        ('ollama_loaded_models', models),
    ):
        try:
            evidence[key] = fn()
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            evidence[key] = None
            failed.append(key)
    reasons = [f'unverified:{item}' for item in failed]
    wallpaper = evidence['wallpaper_service']
    if wallpaper is not None and wallpaper != 'inactive':
        reasons.append('wallpaper_supervisor_not_inactive')
    hermes = evidence['hermes_llama_service']
    if hermes is not None and hermes != 'inactive':
        reasons.append('hermes_llama_not_inactive')
    child = evidence['wallpaper_child_pids']
    if child:
        reasons.append('wallpaper_children_running')
    cuda = evidence['cuda_compute_pids']
    if cuda:
        reasons.append('cuda_compute_processes_present')
    model_count = evidence['ollama_loaded_models']
    if model_count is not None and (not isinstance(model_count, int) or model_count != 0):
        reasons.append('ollama_models_loaded')
    gpu = evidence['gpu_memory']
    if gpu is not None and gpu['free_mib'] < required_free_mib:
        reasons.append('insufficient_free_vram')
    return {'mode': 'read-only', 'required_free_mib': required_free_mib,
            'admission_candidate': not reasons, 'reasons': reasons, 'evidence': evidence,
            'warning': 'Not a GPU lease or authorization; no workloads or services were changed.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--required-free-mib', type=int, default=DEFAULT_REQUIRED_FREE_MIB,
                        help='Candidate free-VRAM threshold, never executes GPU work (default: 10200)')
    args = parser.parse_args()
    try:
        result = probe(required_free_mib=args.required_free_mib)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0  # A veto is normal diagnostic evidence, not a command failure.


if __name__ == '__main__':
    sys.exit(main())
