#!/usr/bin/env python3
"""Source-only guarded entrypoint for Tensor's existing Wallpaper Engine supervisor.

Requires an existing, verified GPU lease database and a Type=notify systemd user
unit. Not installed by this patch. Deliberately DOES NOT accept restoration
grants: two-phase restoration requires a separately tested backend handoff.

Usage: tensor-gpu-wallpaper-systemd.py [--serve | --help]
Source: iragonforce/ops, Stage 2E integration candidate.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from typing import Callable

SCRIPTS = Path(__file__).resolve().parent
STATE_DB = Path.home() / '.local/state/tensor-gpu-lease/queue.sqlite3'
WALLPAPER = Path.home() / '.local/bin/wallpaper-engine-sync'
REQUIRED_FREE_MIB = 10200


class SupervisorError(RuntimeError):
    """Fail closed: GPU safety or service readiness cannot be established."""


def load_sibling(filename: str, name: str):
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SupervisorError('Required GPU component missing: ' + filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def wallpaper_gpu_safe(report: dict) -> bool:
    """Use verified evidence, not probe.admission_candidate during activation.

    In a Type=notify unit, ActiveState is *activating*, so the general-purpose
    lease admission flag is false even when the GPU is actually safe.
    """
    if not isinstance(report, dict) or report.get('mode') != 'read-only':
        return False
    e = report.get('evidence')
    if not isinstance(e, dict):
        return False
    mem = e.get('gpu_memory')
    return (e.get('wallpaper_service') in ('activating', 'inactive')
            and e.get('hermes_llama_service') == 'inactive'
            and e.get('wallpaper_child_pids') == []
            and e.get('cuda_compute_pids') == []
            and type(e.get('ollama_loaded_models')) is int
            and e['ollama_loaded_models'] == 0
            and isinstance(mem, dict)
            and type(mem.get('free_mib')) is int
            and mem['free_mib'] >= REQUIRED_FREE_MIB)


def send_ready(notify_socket: str) -> None:
    if not notify_socket or not isinstance(notify_socket, str):
        raise SupervisorError('NOTIFY_SOCKET missing: refusing unsupervised launch')
    address = ('\x00' + notify_socket[1:]) if notify_socket.startswith('@') else notify_socket
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.sendto(b'READY=1\nSTATUS=Wallpaper supervisor admitted by GPU lease guard', address)


def stop_candidate(process, *, timeout: float = 15.0) -> None:
    """Stop only the subprocess group created by this wrapper."""
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def start_guarded(*, db: Path, wallpaper: Path,
                  arbiter, gpu_report: Callable[[], dict],
                  notify: Callable[[], None],
                  spawn: Callable[[Path], object] | None = None,
                  startup_delay: float = 0.5):
    """Run one arbiter-admitted startup; return (decision, owned subprocess).

    Restoration is deliberately refused: no grant is provided to try_start.
    The caller must retain the subprocess as the systemd unit's child.
    """
    owned = None
    if spawn is None:
        spawn = lambda path: subprocess.Popen([str(path)], stdin=subprocess.DEVNULL,
                                               start_new_session=True, close_fds=True)

    def launch():
        nonlocal owned
        owned = spawn(wallpaper)

    def ready():
        if owned is None:
            return False
        if startup_delay:
            time.sleep(startup_delay)
        if owned.poll() is not None:
            return False
        notify()
        return True

    def abort():
        stop_candidate(owned)

    decision = arbiter.try_start(db, launch, ready, abort,
                                 gpu_safe=lambda: wallpaper_gpu_safe(gpu_report()))
    return decision, owned


def serve() -> int:
    notify_socket = os.environ.get('NOTIFY_SOCKET', '')
    if not notify_socket:
        raise SupervisorError('Type=notify user service required; no wallpaper started')
    arbiter = load_sibling('tensor-gpu-wallpaper-arbiter.py', 'tensor_gpu_wallpaper_arbiter_service')
    probe = load_sibling('tensor-gpu-probe.py', 'tensor_gpu_probe_wallpaper_service')
    decision, child = start_guarded(db=STATE_DB, wallpaper=WALLPAPER, arbiter=arbiter,
                                    gpu_report=probe.probe,
                                    notify=lambda: send_ready(notify_socket))
    if not decision.started:
        # Do not retry on every five-second Restart=on-failure period when an
        # admission veto is intentional. A later explicit start can retry.
        print(json.dumps({'wallpaper_started': False, 'reason': decision.reason}), flush=True)
        return 0
    if child is None:
        raise SupervisorError('Arbiter approved startup without an owned process')
    # Systemd KillMode=control-group delivers SIGTERM to supervisor + children.
    return child.wait()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve', action='store_true', help='Run only from the Type=notify user unit')
    parser.add_argument('--version', action='version', version='tensor-gpu-wallpaper-systemd stage2e-source-only')
    args = parser.parse_args()
    if not args.serve:
        print(json.dumps({'mode': 'read-only', 'installed': False,
                          'production_control_enabled': False,
                          'needs': ['verified lease database', 'Type=notify user unit',
                                    'restoration handoff', 'Hermes/Hyprland callsite audit']}, sort_keys=True))
        return 0
    try:
        return serve()
    except (OSError, ValueError, SupervisorError, subprocess.SubprocessError) as exc:
        print('Wallpaper guard refused startup: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
