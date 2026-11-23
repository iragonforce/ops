#!/usr/bin/env python3
# Read or change the configured RGB state through the existing tensor-control implementation. See tensor-rgb.py(1) for source and integration details.
"""Control only the existing OpenRGB SDK and OpenLinkHub's saved profiles."""

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Read or change the configured RGB state through the existing tensor-control implementation.\nUsage: tensor-rgb.py  [ARGUMENT ...]\n\nSource: hosts/tensor/files/.local/share/tensor-control/rgb.py in ~/ops\nSee man tensor-rgb.py for the existing call sites and argument handling.')
        raise SystemExit(0)
import fcntl,json,os,pathlib,subprocess,sys,time,urllib.request
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
class OpenLinkClient(OpenRGBClient):
    # OpenLinkHub implements controller packets but not profile/plugin lists.
    def update_profiles(self): pass
    def update_plugins(self): pass
STATE=pathlib.Path.home()/'.local/state/tensor-control';STATE.mkdir(parents=True,exist_ok=True)
def olh(path,body=None,method=None):
    req=urllib.request.Request('http://127.0.0.1:27003/api'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'},method=method)
    with urllib.request.urlopen(req,timeout=5) as r:d=json.load(r)
    if body is not None and d.get('status')!=1:raise RuntimeError('OpenLinkHub rejected '+path)
    return d
def devices():return {sid:d['GetDevice'] for sid,d in olh('/devices/').get('devices',{}).items() if sid!='cluster' and isinstance(d.get('GetDevice'),dict) and d['GetDevice'].get('userProfiles')}
def saved_profile(name):
    profile=pathlib.Path.home()/'.config/OpenRGB/profiles'/f'{name}.json'
    if not profile.is_file():raise RuntimeError(f'OpenRGB {name} profile is missing')
    completed=subprocess.run(['/usr/bin/openrgb','--noautoconnect','--client','127.0.0.1:6742',
                              '--profile',name],
                             env={**os.environ,'QT_QPA_PLATFORM':'offscreen'},
                             capture_output=True,text=True,timeout=20)
    if completed.returncode:raise RuntimeError(f'OpenRGB could not load {name}: {completed.stderr.strip()}')
def hub_profile(name):
    for sid,d in devices().items():
        if name not in d['userProfiles']:raise RuntimeError(f'OpenLinkHub {name} profile is missing on {sid}')
        olh('/userProfile/change',{'deviceId':sid,'userProfileName':name})
def fans(off):
    for sid,d in devices().items():
        default=d['userProfiles']['default']['SpeedProfiles']
        for key,ch in d.get('devices',{}).items():
            if not ch.get('HasSpeed'):continue
            label=d['userProfiles']['default'].get('Labels',{}).get(key,ch.get('label',''))
            protected=ch.get('description')=='AIO' or 'AIO' in label.upper() or default.get(key,'').lower()=='aio'
            profile=default.get(key,ch.get('profile','Quiet')) if protected or not off else 'Off'
            olh('/speed',{'deviceId':sid,'channelId':int(key),'profile':profile})
    return 'Off' if off else 'default'
def default_profile():
    """Load the user's existing native-controller default, never the OLH bridge."""
    profile=pathlib.Path.home()/'.config/OpenRGB/profiles/Default.json'
    if not profile.is_file():raise RuntimeError('OpenRGB Default profile is missing; saved standby state retained')
    # OpenRGB's client must detect the server controllers to apply the profile.
    saved_profile('Default')
    saved=json.loads(profile.read_text())['controllers']
    expected={(d['name'],d.get('location',''),d.get('serial','')):d['modes'][d['active_mode']]['name'] for d in saved}
    c=OpenRGBClient('127.0.0.1',6742,name='Tensor default profile readback')
    try:
        for d in c.devices:
            mode=expected.get((d.name,d.metadata.location,d.metadata.serial))
            if mode is None or d.modes[d.active_mode].name!=mode:
                raise RuntimeError('OpenRGB Default does not match current controllers; saved standby state retained')
    finally:c.disconnect()
def lighting(off,color=None):
    for sid,d in devices().items():
        olh('/userProfile/change',{'deviceId':sid,'userProfileName':'Off' if off else 'default'})
        # OpenLinkHub owns case/AIO controllers in both awake and Off profiles.
        olh('/color/setOpenRgbIntegration',{'deviceId':sid,'mode':0})
    fans(off)
    if not off and color is None:default_profile()
    c=OpenRGBClient('127.0.0.1',6742,name='Tensor unified control')
    try:
        for d in c.devices if off or color is not None else []:
            mode=next((m for m in d.modes if m.name.lower()==('off' if off else 'static')),None)
            if mode is None:mode=next((m for m in d.modes if m.name.lower()=='direct'),d.modes[0])
            d.set_mode(mode)
            if not off or mode.name.lower()!='off':d.set_color(RGBColor(*(color if color is not None and not off else ([0,0,0] if off else [255,0,0]))))
        c.update()
        # Never enable SDK ownership or send Direct frames to OLH controllers.
        # Never overwrite the user's saved Default/Off OpenRGB profiles.
        result={'state':'OFF' if off else 'ON','color':{'r':(color or [255,0,0])[0],'g':(color or [255,0,0])[1],'b':(color or [255,0,0])[2]},'fans':'Off' if off else 'default'}
        (STATE/'rgb-state.json').write_text(json.dumps(result)+'\n')
        print(json.dumps({'state':result['state'],'controllers':[(d.name,d.modes[d.active_mode].name) for d in c.devices],'case_controllers':len(devices())}))
    finally:c.disconnect()
if __name__=='__main__':
    with open(STATE/'rgb.lock','w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        action=sys.argv[1] if len(sys.argv)>1 else 'on'
        if action in ['off','on']:lighting(action=='off')
        elif action=='color':lighting(False,[max(0,min(255,int(x))) for x in sys.argv[2:5]])
        elif action in ['fans-off','fans-on']:print(fans(action=='fans-off'))
        else:raise SystemExit('Use on, off, color R G B, fans-on, or fans-off')
