#!/usr/bin/env python3
# Maintain the configured RGB state through the existing persistence integration. See rgb-persistence.py(1) for source and integration details.
"""Save actual controller state, and restore it once per host boot."""

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Maintain the configured RGB state through the existing persistence integration.\nUsage: rgb-persistence.py \n\nSource: hosts/tensor/files/.local/share/tensor-control/rgb-persistence.py in ~/ops\nSee man rgb-persistence.py for the existing call sites and argument handling.')
        raise SystemExit(0)
import fcntl, hashlib, importlib.util, json, pathlib, signal, threading

BASE = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location('visual', BASE/'visual-standby.py')
visual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visual)
SNAPSHOT = visual.rgb.STATE/'reboot-rgb-snapshot.json'
RESTORED = visual.RUN/'tensor-rgb-boot-restored'
PROFILE = 'TensorBootResume'
stop = threading.Event()
last_hub = None

def snapshot():
    global last_hub
    # Match standby's lock order; never save its temporary black/Off state.
    with open(visual.RUN/'tensor-visual-standby.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if visual.MARKER.exists():
            return
        with open(visual.rgb.STATE/'rgb.lock', 'w') as rgb_lock:
            fcntl.flock(rgb_lock, fcntl.LOCK_EX)
            profiles = {}
            for sid, device in visual.rgb.devices().items():
                profiles[sid] = {k:v for k,v in device.get('DeviceProfile', {}).items()
                                 if k not in ('Path','Active')}
            fingerprint = hashlib.sha256(json.dumps(profiles,sort_keys=True).encode()).hexdigest()
            visual.capture(SNAPSHOT, PROFILE, save_hub=fingerprint != last_hub)
            last_hub = fingerprint

def main():
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    if not RESTORED.exists():
        if SNAPSHOT.exists():
            with open(visual.rgb.STATE/'rgb.lock','w') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                visual.restore(SNAPSHOT, default_fans=False)
            print('Previous lighting and fan profiles restored', flush=True)
        RESTORED.touch(mode=0o600)
    snapshot()
    while not stop.wait(60):
        try:
            snapshot()
        except Exception as exc:
            print('RGB checkpoint failed: '+type(exc).__name__, flush=True)
    snapshot()
    print('Shutdown lighting/fan checkpoint saved', flush=True)

if __name__ == '__main__':
    main()
