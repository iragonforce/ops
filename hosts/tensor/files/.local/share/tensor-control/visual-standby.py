#!/usr/bin/env python3
# Control visual standby while retaining live processes, network and SSH. See visual-standby.py(1) for source and integration details.
"""Visual standby only: never suspend, hibernate, or power off the host."""

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Control visual standby while retaining live processes, network and SSH.\nUsage: visual-standby.py  [ARGUMENT ...]\n\nSource: hosts/tensor/files/.local/share/tensor-control/visual-standby.py in ~/ops\nSee man visual-standby.py for the existing call sites and argument handling.')
        raise SystemExit(0)
import fcntl,importlib.util,json,os,pathlib,subprocess,sys,time
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor,ModeData,ModeFlags,ModeColors,ModeDirections
BASE=pathlib.Path(__file__).parent
def module(name):
    spec=importlib.util.spec_from_file_location(name,BASE/(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
rgb=module('tensor-rgb');desktop=module('desktop')
RUN=pathlib.Path('/run/user/1000');MARKER=RUN/'tensor-visual-standby.json'
SNAPSHOT=rgb.STATE/'visual-standby-snapshot.json'
PROFILE='TensorVisualResume'
def identity(d):
    metadata=d.metadata
    return (d.name,int(d.type),metadata.serial,metadata.location,metadata.description)
def native_snapshot(client):
    result=[]
    for device in client.devices:
        mode=device.modes[device.active_mode]
        mode.pack(client.comms._protocol_version)
        data=dict(vars(mode))
        if data['colors'] is not None:data['colors']=[[c.red,c.green,c.blue] for c in data['colors']]
        result.append({'identity':identity(device),'mode':data,'colors':[[c.red,c.green,c.blue] for c in device.colors]})
    return result
def mode_from_json(data):
    data=dict(data);data['flags']=ModeFlags(data['flags']);data['color_mode']=ModeColors(data['color_mode'])
    if data['direction'] is not None:data['direction']=ModeDirections(data['direction'])
    if data['colors'] is not None:data['colors']=[RGBColor(*c) for c in data['colors']]
    return ModeData(**data)
def save_json(path,data):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data)+'\n');temporary.chmod(0o600);temporary.replace(path)
def capture(snapshot_path=SNAPSHOT,profile=PROFILE,save_hub=True):
    # Save mode parameters and individual LED colors through the existing SDK.
    client=OpenRGBClient('127.0.0.1',6742,name='Tensor visual standby snapshot')
    try:
        # Persist active modes, effect parameters, and every LED color directly.
        # Avoid silent server saves and the SDK's older .orp binary format.
        native=native_snapshot(client)
        names=[d.name for d in client.devices]
    finally:client.disconnect()
    hub={}
    for sid,d in rgb.devices().items():
        live=d.get('DeviceProfile',{})
        hub[sid]={'original_path':live.get('Path'),'integration':bool(live.get('OpenRGBIntegration')),
                  'speed_profiles':live.get('SpeedProfiles',{}),
                  'active_profile':next((name for name,p in d.get('userProfiles',{}).items() if p.get('Active')),None)}
        if save_hub:rgb.olh('/userProfile',{'deviceId':sid,'userProfileName':profile},method='PUT')
    p=rgb.STATE/'rgb-state.json'
    result={'format':3,'time':time.time(),'native_controllers':names,'native_devices':native,'hub':hub,'bridge_colors':{},
            'logical_rgb':json.loads(p.read_text()) if p.exists() else None}
    result['profile']=profile
    save_json(snapshot_path,result);return result
def restore_hub(snapshot,original=False):
    available=rgb.devices()
    for sid,entry in snapshot['hub'].items():
        if sid not in available:raise RuntimeError('Saved OpenLinkHub controller is unavailable')
        profile=entry.get('active_profile') if original else None
        if not profile:
            profile=next((name for name,p in available[sid].get('userProfiles',{}).items()
                          if original and p.get('Path')==entry.get('original_path')),None)
        profile=profile or snapshot.get('profile',PROFILE)
        rgb.olh('/userProfile/change',{'deviceId':sid,'userProfileName':profile})
        rgb.olh('/color/setOpenRgbIntegration',{'deviceId':sid,'mode':0})
def restore_awake():
    """Wake uses OpenRGB Default plus the original native OLH user profiles."""
    snapshot=json.loads(SNAPSHOT.read_text())
    rgb.default_profile()
    restore_hub(snapshot,original=True)
    logical=snapshot.get('logical_rgb') or {}
    logical.update(state='ON',fans='awake-profile',openrgb_profile='Default',corsair_owner='OpenLinkHub')
    save_json(rgb.STATE/'rgb-state.json',logical)
def restore(snapshot_path=SNAPSHOT,default_fans=True):
    snapshot=json.loads(snapshot_path.read_text())
    profile=snapshot.get('profile',PROFILE)
    client=OpenRGBClient('127.0.0.1',6742,name='Tensor visual standby restore')
    try:
        if sorted(d.name for d in client.devices)!=sorted(snapshot['native_controllers']):
            raise RuntimeError('RGB controller inventory changed; saved state retained')
        if snapshot.get('format')==3:
            saved=snapshot['native_devices']
            current={identity(d):d for d in client.devices}
            if set(current)!=set(tuple(d['identity']) for d in saved):raise RuntimeError('RGB device identities changed')
            for old in saved:
                device=current[tuple(old['identity'])]
                colors=old['colors']
                # Older snapshots predate the GPU holder on motherboard header 1.
                if (device.name=='ASUS ROG STRIX X870-A GAMING WIFI' and
                    len(colors)==3 and len(device.colors)==13):
                    colors=colors+[[0,0,0]]*10
                if len(colors)!=len(device.colors):raise RuntimeError('RGB LED inventory changed')
                device.set_colors([RGBColor(*c) for c in colors])
                # Restore effect speed/direction/colors as well as its mode ID.
                device.set_mode(mode_from_json(old['mode']))
        elif any(p.name.lower()==profile.lower() for p in client.profiles):
            client.load_profile(profile)
        elif snapshot.get('logical_rgb',{}).get('state')=='OFF':
            # Repair the first-generation snapshot whose server save silently
            # failed. Its recorded state was off; no prior effect is recoverable.
            for device in client.devices:
                device.set_colors([RGBColor(0,0,0) for _ in device.colors])
                mode=next((m for m in device.modes if m.name.lower()=='off'),None)
                if mode is None:mode=next((m for m in device.modes if m.name.lower()=='direct'),None)
                if mode is None:raise RuntimeError('No safe off mode for controller')
                device.set_mode(mode)
            print('Recovered legacy snapshot using its recorded RGB-off state')
        else:raise RuntimeError('Legacy native RGB snapshot is missing; prior lighting cannot be reconstructed')
    finally:client.disconnect()
    restore_hub(snapshot)
    if default_fans:rgb.fans(False)
    logical=snapshot.get('logical_rgb')
    if logical is not None:
        if default_fans:logical['fans']='default'
        save_json(rgb.STATE/'rgb-state.json',logical)

import signal

PROCESS_STATE = RUN / 'tensor-visual-standby-wallpapers.json'

def wallpaper_info(pid):
    proc = pathlib.Path('/proc') / str(pid)
    try:
        if proc.stat().st_uid != os.getuid():
            return None
        executable = os.readlink(proc / 'exe').removesuffix(' (deleted)')
        if pathlib.Path(executable).name != 'linux-wallpaperengine':
            return None
        fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        return {'pid': int(pid), 'starttime': fields[19], 'state': fields[0]}
    except (OSError, IndexError, ValueError):
        return None

def freeze_wallpapers():
    snapshot = (json.loads(PROCESS_STATE.read_text())
                if PROCESS_STATE.exists() else {'version': 1, 'processes': []})
    saved = snapshot['processes']
    known = {(p['pid'], p['starttime']) for p in saved}
    new = []

    for proc in pathlib.Path('/proc').iterdir():
        if not proc.name.isdecimal():
            continue
        info = wallpaper_info(proc.name)
        if not info or info['state'] in ('T', 't'):
            continue
        key = (info['pid'], info['starttime'])
        if key not in known:
            new.append({'pid': info['pid'], 'starttime': info['starttime']})

    if not new:
        return

    # Persist identities before sending SIGSTOP for crash recovery.
    snapshot['processes'] = saved + new
    save_json(PROCESS_STATE, snapshot)

    try:
        for entry in new:
            info = wallpaper_info(entry['pid'])
            if info and info['starttime'] == entry['starttime']:
                try:
                    os.kill(entry['pid'], signal.SIGSTOP)
                except ProcessLookupError:
                    pass
    except BaseException:
        resume_wallpapers()
        raise

    print(f'Wallpaper processes suspended: {len(new)}')

def resume_wallpapers():
    if not PROCESS_STATE.exists():
        return

    snapshot = json.loads(PROCESS_STATE.read_text())
    for entry in snapshot['processes']:
        info = wallpaper_info(entry['pid'])
        if info and info['starttime'] == entry['starttime']:
            try:
                os.kill(entry['pid'], signal.SIGCONT)
            except ProcessLookupError:
                pass

    PROCESS_STATE.unlink()
    print('Wallpaper processes resumed')


CPU_HELPER = '/usr/local/sbin/tensor-standby-cpu'

def cpu_power(action):
    result = subprocess.run(
        ['sudo', '-n', CPU_HELPER, action],
        capture_output=True, text=True, timeout=20
    )
    if result.returncode:
        raise RuntimeError(
            f'CPU {action} failed: '
            + (result.stderr.strip() or result.stdout.strip())
        )
    if result.stdout.strip():
        print(result.stdout.strip())


GPU_STATE = RUN / 'tensor-visual-standby-gpu.json'

def gpu_uuid():
    result = subprocess.run(
        ['/usr/bin/nvidia-smi', '-i', '0',
         '--query-gpu=uuid', '--format=csv,noheader'],
        capture_output=True, text=True, check=True, timeout=10
    )
    return result.stdout.strip()

def gpu_power(action):
    if action == 'enter':
        uuid = gpu_uuid()
        if GPU_STATE.exists():
            saved = json.loads(GPU_STATE.read_text())
            if saved.get('uuid') != uuid:
                raise RuntimeError('GPU identity changed')
        else:
            # Persist recovery intent before applying the clock restriction.
            save_json(GPU_STATE, {
                'version': 1,
                'uuid': uuid,
                'restore': 'automatic'
            })
        flags = ['-lgc', '600,1200']

    elif action == 'resume':
        if not GPU_STATE.exists():
            return
        saved = json.loads(GPU_STATE.read_text())
        if saved.get('uuid') != gpu_uuid():
            raise RuntimeError('GPU identity changed')
        flags = ['-rgc']

    else:
        raise ValueError('Unsupported GPU action')

    result = subprocess.run(
        ['sudo', '-n', '/usr/bin/nvidia-smi', '-i', '0', *flags],
        capture_output=True, text=True, timeout=20
    )
    if result.returncode:
        raise RuntimeError(
            'NVIDIA clock operation failed: '
            + (result.stderr.strip() or result.stdout.strip())
        )

    if action == 'resume':
        GPU_STATE.unlink()
        print('GPU automatic graphics clocks restored')
    else:
        print('GPU graphics clocks limited to 600-1200 MHz')

def restore_standby():
    # Independent recovery: one failed component cannot block another.
    steps = [
        ('GPU', lambda: gpu_power('resume')),
        ('CPU', lambda: cpu_power('resume')),
        ('Wallpaper Engine', resume_wallpapers),
        ('Displays', desktop.wake),
        ('OpenRGB', lambda: rgb.saved_profile('Default')),
        ('OpenLinkHub', lambda: rgb.hub_profile('default')),
    ]
    errors = []

    for name, operation in steps:
        try:
            operation()
        except Exception as error:
            message = f'{name}: {error}'
            errors.append(message)
            print('Recovery failed: ' + message, file=sys.stderr)

    if errors:
        # Keep marker for explicit recovery retry.
        raise RuntimeError('Incomplete standby recovery: ' + '; '.join(errors))

    MARKER.unlink(missing_ok=True)
    (RUN / 'hypr-locked-dpms-off').unlink(missing_ok=True)
    print('Displays awake; CPU, wallpapers and RGB restored')

def main(action):
    os.umask(0o077)

    with open(RUN / 'tensor-visual-standby.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        if action == 'status':
            print('visual standby' if MARKER.exists() else 'awake')
            return

        if action == 'resume' and not MARKER.exists():
            return

        with open(rgb.STATE / 'rgb.lock', 'w') as rgb_lock:
            fcntl.flock(rgb_lock, fcntl.LOCK_EX)

            if action == 'enter':
                MARKER.touch(mode=0o600)

                try:
                    desktop.dispatch('hl.dsp.dpms({action="off"})')
                    rgb.saved_profile('Off')
                    rgb.hub_profile('Off')
                    freeze_wallpapers()
                    cpu_power('enter')
                    gpu_power('enter')
                except BaseException:
                    print(
                        'Standby entry failed; attempting recovery',
                        file=sys.stderr
                    )
                    try:
                        restore_standby()
                    except BaseException as error:
                        print(
                            f'Automatic recovery incomplete: {error}',
                            file=sys.stderr
                        )
                    raise

                print('Visual standby active; CPU power profile applied')

            elif action == 'resume':
                restore_standby()

            else:
                raise SystemExit('Use enter, resume, or status')

if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'enter')
