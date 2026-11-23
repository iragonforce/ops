#!/usr/bin/env python3
import os,sys,json,pathlib,re,urllib.request,urllib.error,hashlib
# Read only the envelope before exec; do not buffer subsequent JSON-RPC input.
b=bytearray()
while True:
 c=os.read(0,1)
 if not c or c==b'\n':break
 b.extend(c)
e=json.loads(b);s=e['spec'];profile=e['profile'];base=pathlib.Path('/opt/data');home=base if profile=='main' else base/'profiles'/profile
from dotenv import dotenv_values
for p in [base/'.env',home/'.env']:
 if p.exists():
  for k,v in dotenv_values(p).items():
   if v is not None:os.environ[k]=v
os.environ['HERMES_HOME']=str(home);os.environ['HOME']='/opt/data'
def expand(v):
 return re.sub(r'\$\{([^}]+)\}',lambda m:os.environ.get(m[1],''),str(v))
for k,v in s.get('env',{}).items():os.environ[k]=expand(v)
if s.get('command'):
 argv=[expand(s['command']),*[expand(v) for v in s.get('args',[])]]
 os.execvpe(argv[0],argv,os.environ)
url=expand(s['url']);headers={k:expand(v) for k,v in s.get('headers',{}).items()};session=None;version=None
headers.update({'Content-Type':'application/json','Accept':'application/json, text/event-stream'})
aliases={}
def emit(d):
 tools=d.get('result',{}).get('tools')
 if isinstance(tools,list):
  for tool in tools:
   original=tool['name'];safe=re.sub(r'[^A-Za-z0-9_-]','_',original)
   if len(safe)>32:safe=safe[:23]+'_'+hashlib.sha256(original.encode()).hexdigest()[:8]
   aliases[safe]=original;tool['name']=safe
 print(json.dumps(d),flush=True)
for line in sys.stdin:
 try:q=json.loads(line)
 except ValueError:continue
 if q.get('method')=='tools/call':
  args=q.get('params',{});args['name']=aliases.get(args.get('name'),args.get('name'))
 h=dict(headers)
 if session:h['Mcp-Session-Id']=session
 if version:h['MCP-Protocol-Version']=version
 try:
  req=urllib.request.Request(url,data=json.dumps(q).encode(),headers=h,method='POST')
  with urllib.request.urlopen(req,timeout=float(s.get('timeout',120))) as r:
   session=r.headers.get('Mcp-Session-Id',session)
   if r.status in (202,204):continue
   if 'text/event-stream' in r.headers.get('Content-Type',''):
    data=[]
    for raw in r:
     text=raw.decode().rstrip('\r\n')
     if text.startswith('data:'):data.append(text[5:].lstrip())
     elif not text and data:
      d=json.loads('\n'.join(data));data=[];emit(d)
      if d.get('id')==q.get('id'):
       version=d.get('result',{}).get('protocolVersion',version);break
   else:
    body=r.read()
    if body:
     d=json.loads(body);version=d.get('result',{}).get('protocolVersion',version);emit(d)
 except Exception as exc:
  if 'id' in q:emit({'jsonrpc':'2.0','id':q['id'],'error':{'code':-32000,'message':'Nexus MCP upstream unavailable ('+type(exc).__name__+')'}})
