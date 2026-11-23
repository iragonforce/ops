#!/usr/bin/env python3

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Report hashes and deployment targets for the existing shared configuration.\nUsage: audit.py \n\nSource: shared/unified/bin/audit.py in ~/ops\nSee man audit.py for the existing call sites and argument handling.')
        raise SystemExit(0)
# Report hashes and deployment targets for the existing shared configuration. See audit.py(1) for source and integration details.
import pathlib,hashlib,json,subprocess,socket
h=pathlib.Path.home();r=h/'.config/homelab/unified';summary={'host':socket.gethostname().split('.')[0]}
for name in ['nvim','codex/skills']:
 rows=[]
 for p in sorted((r/name).rglob('*')):
  if p.is_file() and not any(x.startswith(('.st','._','.DS_')) for x in p.relative_to(r/name).parts):rows.append(str(p.relative_to(r/name))+':'+hashlib.sha256(p.read_bytes()).hexdigest())
 summary[name]={'files':len(rows),'sha256':hashlib.sha256('\n'.join(rows).encode()).hexdigest()}
summary['skill_definitions']=len(list((r/'codex/skills').rglob('SKILL.md')))
summary['nvim_config_target']=str((h/'.config/nvim').resolve())
summary['codex_config_target']=str((h/'.codex/config.toml').resolve())
print(json.dumps(summary,indent=2))
