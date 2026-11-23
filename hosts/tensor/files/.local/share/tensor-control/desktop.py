#!/usr/bin/env python3
# Control the configured desktop/display state through the existing tensor-control implementation. See desktop.py(1) for source and integration details.
"""Use Tensor's live Hyprland session and keep one visible secondary btop."""

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Control the configured desktop/display state through the existing tensor-control implementation.\nUsage: desktop.py  [ARGUMENT ...]\n\nSource: hosts/tensor/files/.local/share/tensor-control/desktop.py in ~/ops\nSee man desktop.py for the existing call sites and argument handling.')
        raise SystemExit(0)
import json,os,pathlib,subprocess,sys,time,fcntl
def env():
    e=os.environ.copy()
    e.setdefault('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}')
    # Discover the compositor directly. Desktop wake must not depend on a
    # responsive systemd user manager or its D-Bus connection.
    try:
        instances=json.loads(subprocess.check_output(['hyprctl','-j','instances'],env=e,text=True,timeout=3))
        live=max(instances,key=lambda instance:instance['time'])
        e['HYPRLAND_INSTANCE_SIGNATURE']=live['instance']
        e['WAYLAND_DISPLAY']=live['wl_socket']
        e.setdefault('DISPLAY',':0')
        return e
    except (subprocess.SubprocessError,ValueError,KeyError):
        pass
    try:
        out=subprocess.check_output(['systemctl','--user','show-environment'],env=e,text=True,timeout=3)
    except subprocess.SubprocessError:
        return e
    for line in out.splitlines():
        if '=' in line:
            k,v=line.split('=',1)
            if k in ['HYPRLAND_INSTANCE_SIGNATURE','WAYLAND_DISPLAY','DISPLAY','XDG_RUNTIME_DIR']:e[k]=v
    return e
E=env()
def hypr(*args):return subprocess.check_output(['hyprctl',*args],env=E,text=True,timeout=8).strip()
def dispatch(expression):return hypr('eval','hl.dispatch('+expression+')')
def reset_secondary(monitor=None):
    m=monitor or next((m for m in json.loads(hypr('-j','monitors')) if m['name']=='DP-3'),None)
    if not m or 'LG Ultra HD' not in m.get('description',''):return
    # A real mode transition reinitializes the AMD display pipeline after DPMS.
    mode='3840x2160@60'
    alt=next((x for x in m.get('availableModes',[]) if x.startswith(f'{m["width"]}x{m["height"]}@30.')),None)
    if alt is None:return
    def apply(value):
        rule='hl.monitor({output="DP-3",mode='+json.dumps(value)+',position='+json.dumps(f'{m["x"]}x{m["y"]}')+',scale='+str(m['scale'])+',transform='+str(m['transform'])+',vrr=0,bitdepth=8,cm="srgb"})'
        return hypr('eval',rule)
    try:
        apply(alt.removesuffix('Hz'));time.sleep(1)
    finally:apply(mode)
def wake():
    dispatch('hl.dsp.dpms({action="on"})')
    # Avoid repeated 30/60 Hz transitions on wake. Synchronization is handled
    # by the compositor backend; an explicit manual repair remains available.
    for _ in range(30):
        monitors=json.loads(hypr('-j','monitors'))
        if all(m.get('dpmsStatus') for m in monitors):break
        time.sleep(.1)
def bars():
    try:
        subprocess.run(['systemctl','--user','restart','workspace-strip.service'],env=E,check=True,timeout=5)
    except subprocess.SubprocessError as error:
        # Display/RGB recovery must continue if the bar's manager is unavailable.
        print(f'Workspace bar restart failed: {type(error).__name__}',file=sys.stderr)
    if subprocess.run(['pgrep','-u',str(os.getuid()),'-x','waybar'],stdout=subprocess.DEVNULL).returncode:
        subprocess.Popen([str(pathlib.Path.home()/'.config/hypr/scripts/start-waybar.sh')],env=E,
                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
def btop():
    lock=open('/run/user/1000/tensor-btop.lock','w');fcntl.flock(lock,fcntl.LOCK_EX)
    monitors=json.loads(hypr('-j','monitors'))
    secondary=next((m for m in monitors if m['name']=='DP-3'),None)
    if not secondary:return
    clients=json.loads(hypr('-j','clients'))
    matches=[c for c in clients if c.get('class')=='com.btop.term']
    if not matches:
        subprocess.Popen(['ghostty','--class=com.btop.term','-e','btop'],env=E,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        for _ in range(40):
            matches=[c for c in json.loads(hypr('-j','clients')) if c.get('class')=='com.btop.term']
            if matches:break
            time.sleep(.1)
    dispatch('hl.dsp.workspace.move({workspace="10",monitor="DP-3"})')
    for c in matches:dispatch('hl.dsp.window.move({workspace="10",window='+json.dumps('address:'+c['address'])+',follow=false})')
    focused=next((m['name'] for m in monitors if m.get('focused')), 'DP-5')
    dispatch('hl.dsp.focus({monitor="DP-3"})');dispatch('hl.dsp.focus({workspace="10"})')
    dispatch('hl.dsp.focus({monitor='+json.dumps(focused)+'})')
if __name__=='__main__':
    action=sys.argv[1] if len(sys.argv)>1 else 'btop'
    if action=='btop':btop()
    elif action=='on':wake();bars();btop()
    elif action=='bars':bars()
    elif action=='repair-display':reset_secondary();btop()
    elif action=='off':dispatch('hl.dsp.dpms({action="off"})')
    else:raise SystemExit('Use btop, on, or off')
