#!/usr/bin/env python3
"""Scoped Tensor GPU/systemd backend, with read-only CLI (Stage 2C).

The command-line interface only prints evidence. The DesktopBackend methods
are available for injected, test-only calls; there is intentionally no live
acquire, release, stop, start, or unattended worker entrypoint at this stage.

Source of truth: iragonforce/ops. Usage: tensor-gpu-systemd-adapter.py --help
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable

SCRIPT_DIR = Path(__file__).resolve().parent
PROBE_FILE = SCRIPT_DIR / 'tensor-gpu-probe.py'
WALLPAPER_UNIT = 'wallpaper-engine-sync.service'
REQUIRED_FREE_MIB = 10200
MAX_SLEEPING_LLAMA_MIB = 256  # Observed native sleep ~184 MiB; conservative veto above this.
RESTORE_DB = Path.home() / '.local/state/tensor-gpu-lease/queue.sqlite3'


class AdapterError(RuntimeError):
    """A safety or state verification failure; do not change lease state to normal."""


def load_probe():
    spec = importlib.util.spec_from_file_location('tensor_gpu_probe_stage2c', PROBE_FILE)
    if not spec or not spec.loader:
        raise AdapterError('Cannot load existing read-only GPU probe')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_restore_mailbox():
    path = SCRIPT_DIR / 'tensor-gpu-restore-mailbox.py'
    spec = importlib.util.spec_from_file_location('tensor_gpu_restore_mailbox_adapter', path)
    if not spec or not spec.loader:
        raise AdapterError('Restoration transport component unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def systemctl_command(argv: list[str]) -> str:
    """Only the caller-selected, exact systemctl argv; never a shell command."""
    cp = subprocess.run(argv, check=True, capture_output=True, text=True, timeout=30)
    return cp.stdout.strip()

def gpu_client_pids(output: str) -> set[int]:
    """Parse one NVIDIA pmon sample; malformed/empty evidence is never admission."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if len(lines) < 2 or not all(line.startswith('#') for line in lines[:2]):
        raise AdapterError('GPU client inventory unavailable')
    pids: set[int] = set()
    for line in lines[2:]:
        cells = line.split()
        if len(cells) < 10 or cells[0] != '0' or not cells[1].isdecimal():
            raise AdapterError('Malformed NVIDIA GPU client')
        pids.add(int(cells[1]))
    return pids

def gpu_compute_memory(output: str) -> dict[int, int]:
    allocations: dict[int, int] = {}
    for line in output.splitlines():
        cells = [value.strip() for value in line.split(',')]
        if len(cells) != 2 or not all(value.isdecimal() for value in cells):
            raise AdapterError('Malformed NVIDIA compute allocation')
        pid, mib = map(int, cells)
        if pid <= 0 or pid in allocations:
            raise AdapterError('Ambiguous NVIDIA compute allocation')
        allocations[pid] = mib
    return allocations

def owned_gpu_executable(pid: int, proc_root: Path = Path('/proc')) -> str:
    """Identify only caller-owned regular processes; do not trust pmon names."""
    directory = proc_root / str(pid)
    if pid <= 0 or directory.stat().st_uid != os.geteuid():
        raise AdapterError('Unknown GPU process owner')
    value = os.readlink(directory / 'exe')
    return value.removesuffix(' (deleted)')


class TensorDesktopBackend:
    """Implements the Stage 2 lease backend protocol; NOT CLI-activated.

    A future caller must hold the LeaseManager lock, establish real owner
    lifecycle/recovery, and guard independent wallpaper restarts first.
    """

    def __init__(self, *, run: Callable[[list[str]], str] = systemctl_command,
                 observe: Callable[[], dict] | None = None,
                 required_free_mib: int = REQUIRED_FREE_MIB):
        if not 1 <= required_free_mib <= 12227:
            raise ValueError('Unreasonable single-GPU free-VRAM threshold')
        self.run = run
        self.required_free_mib = required_free_mib
        if observe is None:
            probe_module = load_probe()
            self.observe = lambda: probe_module.probe(required_free_mib=required_free_mib)
        else:
            self.observe = observe

    def snapshot(self) -> dict:
        report = self.observe()
        if not isinstance(report, dict) or report.get('mode') != 'read-only':
            raise AdapterError('Missing trusted read-only probe result')
        evidence = report.get('evidence')
        if not isinstance(evidence, dict) or not isinstance(report.get('reasons'), list):
            raise AdapterError('Malformed probe result')
        required = {
            'wallpaper_service', 'wallpaper_child_pids', 'hermes_llama_service',
            'cuda_compute_pids', 'gpu_memory', 'ollama_loaded_models',
        }
        if not required.issubset(evidence):
            raise AdapterError('Incomplete GPU evidence')
        return report

    def _wallpaper_state(self) -> tuple[str, list[int]]:
        evidence = self.snapshot()['evidence']
        state = evidence['wallpaper_service']
        children = evidence['wallpaper_child_pids']
        if state not in ('active', 'inactive'):
            raise AdapterError(f'Wallpaper unit state not stable: {state!r}')
        if not isinstance(children, list) or any(not isinstance(p, int) or p <= 0 for p in children):
            raise AdapterError('Cannot verify wallpaper children')
        if state == 'inactive' and children:
            raise AdapterError('Orphan wallpaper GPU processes exist')
        return state, children

    def wallpaper_active(self) -> bool:
        state, _ = self._wallpaper_state()
        return state == 'active'

    def stop_wallpaper(self) -> None:
        state, _ = self._wallpaper_state()
        if state == 'active':
            self.run(['/usr/bin/systemctl', '--user', 'stop', WALLPAPER_UNIT])
        after, children = self._wallpaper_state()
        if after != 'inactive' or children:
            raise AdapterError('Wallpaper supervisor/children did not stop')

    def start_wallpaper(self, *, restoration_grant: str | None = None) -> None:
        """Start only the guarded unit; no grant appears in systemctl argv.

        The two-phase lease manager must hold gpu-restore.lock while calling
        this method. The service consumes the private mailbox delivery, and
        the arbiter independently verifies the durable SQLite capability.
        """
        state, _ = self._wallpaper_state()
        if restoration_grant is not None and state != 'inactive':
            raise AdapterError('Refusing grant when wallpaper is already active')
        if state == 'inactive':
            transport = load_restore_mailbox() if restoration_grant is not None else None
            if transport is not None:
                transport.publish(RESTORE_DB, restoration_grant)
            try:
                self.run(['/usr/bin/systemctl', '--user', 'start', WALLPAPER_UNIT])
            finally:
                # Remove an unconsumed capability even after a failed start.
                # A successful service startup has already consumed it.
                if transport is not None:
                    transport.revoke(RESTORE_DB, restoration_grant)
        after, _ = self._wallpaper_state()
        if after != 'active':
            raise AdapterError('Wallpaper supervisor did not start')

    def preflight(self) -> bool:
        """Veto known incompatible owners before touching the desktop.

        This is only a negative precheck. Full ownership/free-memory evidence
        is still required by safe_to_acquire() after a scoped wallpaper stop.
        An active Hermes service needs a separate sleep-aware verified backend.
        """
        e = self.snapshot()['evidence']
        return (e['wallpaper_service'] in ('active', 'inactive')
                and isinstance(e['wallpaper_child_pids'], list)
                and e['hermes_llama_service'] in ('inactive', 'failed')
                and e['cuda_compute_pids'] == []
                and type(e['ollama_loaded_models']) is int
                and e['ollama_loaded_models'] == 0
                and isinstance(e['gpu_memory'], dict))

    def safe_to_acquire(self) -> bool:
        # Called by the lease state machine AFTER a verified scoped wallpaper stop.
        # A positive candidate remains insufficient until request admission,
        # idle authorization, and uncoordinated-client containment are installed.
        report = self.snapshot()
        return report.get('admission_candidate') is True and not report['reasons']

    def inference_memory_released(self) -> bool:
        # Never infer memory release from HTTP /health or process termination alone.
        # Candidate requires all NVIDIA/process/model evidence to pass.
        report = self.snapshot()
        return report.get('admission_candidate') is True and not report['reasons']


class TensorSleepAwareBackend(TensorDesktopBackend):
    """Conservative ownership veto for a natively sleeping, active llama.

    Positive evidence alone is not a lease, verified user-idle signal, or
    containment of loopback clients; do not enable live acquire on this alone.
    """

    def __init__(self, *, identify: Callable[[int], str] = owned_gpu_executable,
                 **kwargs):
        super().__init__(**kwargs)
        self.identify = identify

    def _owner_safe(self, *, before_stop: bool) -> bool:
        try:
            e = self.snapshot()['evidence']
            state = e['wallpaper_service']
            children = e['wallpaper_child_pids']
            gpu = e['gpu_memory']
            if (state not in (('active', 'inactive') if before_stop else ('inactive',))
                    or not isinstance(children, list)
                    or any(type(pid) is not int or pid <= 0 for pid in children)
                    or (not before_stop and children)
                    or type(e['ollama_loaded_models']) is not int
                    or e['ollama_loaded_models'] != 0
                    or not isinstance(gpu, dict)
                    or (not before_stop and gpu['free_mib'] < self.required_free_mib)):
                return False
            main_argv = ['/usr/bin/systemctl', '--user', 'show',
                         'hermes-llama.service', '--property=MainPID', '--value']
            main = self.run(main_argv)
            if not main.isdecimal():
                return False
            main_pid = int(main)
            memory = gpu_compute_memory(self.run([
                '/usr/bin/nvidia-smi', '--query-compute-apps=pid,used_gpu_memory',
                '--format=csv,noheader,nounits']))
            observed = gpu_client_pids(self.run(['/usr/bin/nvidia-smi', 'pmon', '-c', '1']))
            if set(memory) != set(e['cuda_compute_pids']) or not set(memory).issubset(observed):
                return False
            wallpaper_pids = set(children) if state == 'active' and before_stop else set()
            remaining = {pid: mib for pid, mib in memory.items() if pid not in wallpaper_pids}
            service = e['hermes_llama_service']
            if service == 'active':
                if (main_pid <= 0 or set(remaining) != {main_pid}
                        or not 0 < remaining[main_pid] <= MAX_SLEEPING_LLAMA_MIB
                        or self.identify(main_pid) != '/usr/bin/llama-server'):
                    return False
            elif service in ('inactive', 'failed'):
                if main_pid != 0 or remaining:
                    return False
            else:
                return False
            allowed = {'/usr/bin/Hyprland', '/usr/bin/Xwayland'}
            if state == 'active' and before_stop:
                for pid in children:
                    if self.identify(pid) != '/opt/linux-wallpaperengine/linux-wallpaperengine':
                        return False
                allowed.add('/opt/linux-wallpaperengine/linux-wallpaperengine')
            if any(pid != main_pid and self.identify(pid) not in allowed for pid in observed):
                return False
            # A swapped systemd PID between probes invalidates the snapshot.
            return main == self.run(main_argv)
        except (AdapterError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            return False

    def preflight(self) -> bool:
        return self._owner_safe(before_stop=True)

    def safe_to_acquire(self) -> bool:
        return self._owner_safe(before_stop=False)

    def inference_memory_released(self) -> bool:
        return self._owner_safe(before_stop=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--required-free-mib', type=int, default=REQUIRED_FREE_MIB)
    parser.add_argument('--version', action='version', version='tensor-gpu-systemd-adapter stage2c-read-only')
    args = parser.parse_args()
    try:
        adapter = TensorDesktopBackend(required_free_mib=args.required_free_mib)
        result = adapter.snapshot()
    except (AdapterError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'mode': 'read-only', 'verified': False, 'error': str(exc),
                          'warning': 'No service changes performed.'}, indent=2))
        return 1
    result = dict(result)
    result['adapter'] = 'systemd-nvidia-stage2c'
    result['live_control_enabled'] = False
    result['blocking_requirements'] = [
        'hermes ExecStopPost currently restarts wallpaper independently',
        'Hyprland session-start restarts wallpaper independently',
        'persistent leases require dead-owner recovery before activation',
        'uncoordinated direct Ollama clients are not admitted through this adapter',
    ]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
