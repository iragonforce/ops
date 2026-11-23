#!/usr/bin/env python3
"""Usage inventory from existing logs. No prompts, credentials, or tool arguments are saved."""
from pathlib import Path
import json,re,collections,datetime,socket,os,subprocess
h=Path.home();root=h/'.codex/sessions';counts=collections.Counter();sessions=collections.defaultdict(set);files=0
roots=[r'/skills',r'\.codex/skills',r'\.agents/skills',r'\.config/homelab/unified/codex/skills',r'/opt/data/skills']
patterns=[re.compile(s+r'/([^\n"\'`\\;]+?)/SKILL\.md') for s in roots]
for p in root.rglob('*.jsonl'):
 files+=1
 try:
  with p.open(errors='replace') as f:
   for line in f:
    if 'SKILL.md' not in line:continue
    try:d=json.loads(line);v=d.get('payload',{} )
    except (ValueError,AttributeError):continue
    if v.get('type') not in ('function_call','custom_tool_call'):continue
    name=v.get('name','');args=v.get('arguments',v.get('input',''))
    if not isinstance(args,str):args=json.dumps(args)
    if not re.search(r'\b(cat|sed|head|read_file|read_text|readFile|open)\b',args):continue
    found=set()
    for rx in patterns:
     for m in rx.finditer(args):
      skill=m[1].strip().split('/')[-1]
      if len(skill)<100 and not any(c in skill for c in '{}*?'):found.add(skill)
    for skill in found:counts[skill]+=1;sessions[skill].add(p.stem)
 except (PermissionError,OSError):pass
report={'host':socket.gethostname().split('.')[0],'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'metric':'observed explicit skill-read requests in Codex function-call logs; not success, benefit, or metadata impressions','session_files_scanned':files,'skills':[{'name':k,'read_requests':v,'sessions':len(sessions[k])} for k,v in counts.most_common()]}
out=h/'.local/state/agent-usage';out.mkdir(parents=True,exist_ok=True);p=out/'codex-skills.json';p.write_text(json.dumps(report,indent=2));p.chmod(0o600)
if Path('/usr/local/libexec/hermes-skill-usage').exists():
 try:
  result=subprocess.check_output(['sudo','-n','/usr/local/libexec/hermes-skill-usage'],stderr=subprocess.DEVNULL,text=True,timeout=30)
  native=json.loads(result);dest=out/'hermes-skills.json';dest.write_text(json.dumps(native,indent=2));dest.chmod(0o600)
 except (OSError,ValueError,subprocess.SubprocessError):pass
print(json.dumps({'host':report['host'],'session_files_scanned':files,'distinct_skills_observed':len(counts),'read_requests':sum(counts.values()),'report':str(p)}))
