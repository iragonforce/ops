#!/usr/bin/env python3
import json,pathlib,shutil,subprocess,time,urllib.request
p=pathlib.Path('/var/lib/openlinkhub/config.json');backup=pathlib.Path('/var/lib/tensor-control-backup-20261012/openlink-config.before.json')
if not backup.exists():shutil.copy2(p,backup)
d=json.loads(p.read_text());d['enableOpenRGBTargetServer']=True;d['openRGBPort']=6743;p.write_text(json.dumps(d,indent=2)+'\n')
subprocess.run(['systemctl','restart','openlinkhub.service'],check=True)
for _ in range(40):
    try:
        data=json.load(urllib.request.urlopen('http://127.0.0.1:27003/api/devices/',timeout=2));break
    except Exception:time.sleep(.25)
else:raise RuntimeError('OpenLinkHub did not return')
for sid,v in data.get('devices',{}).items():
    if sid=='cluster' or not isinstance(v.get('GetDevice'),dict) or not v['GetDevice'].get('userProfiles'):continue
    req=urllib.request.Request('http://127.0.0.1:27003/api/color/setOpenRgbIntegration',data=json.dumps({'deviceId':sid,'mode':1}).encode(),headers={'Content-Type':'application/json'})
    result=json.load(urllib.request.urlopen(req,timeout=5))
    if result.get('status')!=1:raise RuntimeError('Device rejected SDK integration')
print('OpenLinkHub SDK enabled on separate port 6743; cooling remains owned by OpenLinkHub')
