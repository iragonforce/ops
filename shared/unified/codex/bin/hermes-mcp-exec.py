#!/usr/bin/env python3
import sys,json,os,pathlib,subprocess
# Executed on Nexus. Read configuration there; credentials never enter Codex config.
if os.geteuid()!=0:
 os.execv('/usr/bin/sudo',['sudo','-n','/usr/bin/python3',__file__,*sys.argv[1:]])
import yaml
profile,server=sys.argv[1:3]
if not profile.replace('-','').replace('_','').isalnum():raise SystemExit('Invalid profile')
base=pathlib.Path('/srv/containers/data/hermes/data')
root=base
cfg=yaml.safe_load((root/'config.yaml').read_text()) or {}
mapfile=root/'codex-sync/mcp-aliases.json'
aliases=json.loads(mapfile.read_text()) if mapfile.exists() else {}
key=aliases.get(profile+':'+server,server)
spec=cfg['mcp_servers'][key]
envelope={'profile':'main','spec':spec}
logs=pathlib.Path('/var/log/nexus-recovery/mcp');logs.mkdir(mode=0o700,exist_ok=True)
log=logs/(profile+'-'+server+'.log')
err=log.open('a')
p=subprocess.Popen(['/usr/bin/docker','exec','-i','--user','10000:10000','-w','/opt/data','hermes','/opt/hermes/.venv/bin/python','/opt/data/codex-sync/mcp-runtime.py'],stdin=subprocess.PIPE,stderr=err)
p.stdin.write(json.dumps(envelope).encode()+b'\n');p.stdin.flush()
try:
 while True:
  chunk=os.read(0,65536)
  if not chunk:break
  p.stdin.write(chunk);p.stdin.flush()
except (BrokenPipeError,KeyboardInterrupt):pass
finally:
 try:p.stdin.close()
 except BrokenPipeError:pass
 try:code=p.wait(timeout=10)
 except subprocess.TimeoutExpired:p.terminate();code=p.wait()
sys.exit(code)
