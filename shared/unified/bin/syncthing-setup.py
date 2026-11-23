#!/usr/bin/env python3

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Configure legacy Syncthing distribution; retired after Git adoption.\nUsage: syncthing-setup.py \n\nSource: shared/unified/bin/syncthing-setup.py in ~/ops\nSee man syncthing-setup.py for the existing call sites and argument handling.')
        raise SystemExit(0)
# Configure legacy Syncthing distribution; retired after Git adoption. See syncthing-setup.py(1) for source and integration details.
import pathlib,xml.etree.ElementTree as E,urllib.request,json,socket
host=socket.gethostname().split('.')[0].lower();h=pathlib.Path('/home/iragonforce') if host=='nexus' else pathlib.Path.home()
paths=[h/'.local/state/syncthing/config.xml',h/'Library/Application Support/Syncthing/config.xml',pathlib.Path('/srv/containers/data/syncthing/config/config/config.xml')]
p=next(p for p in paths if p.exists());xml=E.parse(p).getroot();key=xml.findtext('gui/apikey');addr=xml.findtext('gui/address');port=addr.rsplit(':',1)[1];url='http://'+('192.168.5.9' if host=='nexus' else '127.0.0.1')+':'+port

def call(path,body=None,method=None):
 data=json.dumps(body).encode() if body is not None else None
 req=urllib.request.Request(url+'/rest/'+path,data=data,headers={'X-API-Key':key,'Content-Type':'application/json'},method=method)
 with urllib.request.urlopen(req,timeout=15) as r:
  s=r.read();return json.loads(s) if s else None
status=call('system/status');devices=call('config/devices');ids={d.get('name'):d['deviceID'] for d in devices}
selfid=status['myID'];ids[host]=selfid
folder_defaults=call('config/defaults/folder');existing=call('config/folders')
for suffix,kind in [('codex','sendreceive'),('nvim','sendonly' if host=='qubit' else 'receiveonly'),('tmux','sendonly' if host=='qubit' else 'receiveonly')]:
 fid='homelab-unified-'+suffix
 folder=next((f for f in existing if f['id']==fid),None) or dict(folder_defaults)
 folder.update(id=fid,label='Homelab unified '+suffix,path=('/data/homelab-unified/'+suffix if host=='nexus' else str(h/'.config/homelab/unified'/suffix)),type=kind,ignorePerms=True,fsWatcherEnabled=True,rescanIntervalS=60)
 folder['devices']=[{'deviceID':ids[n],'introducedBy':'','encryptionPassword':''} for n in ['qubit','tensor','nexus'] if n in ids]
 version=dict(folder.get('versioning',{}));version.update(type='',params={});folder['versioning']=version
 root=h/'.config/homelab/unified'/suffix;(root/'.stfolder').mkdir(exist_ok=True)
 (root/'.stignore').write_text('.DS_Store\n._*\n.git\n*.swp\n*.swo\n')
 call('config/folders/'+fid,folder,'PUT')
 print(host,fid,kind,'configured')
print('Configuration saved; local version archives and automatic backup copies are disabled')
