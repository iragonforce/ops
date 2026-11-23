#!/usr/bin/env python3
# Report or select the existing Hermes authentication mode without exposing credentials. See hermes-auth-mode.py(1) for source and integration details.
"""Runs on Nexus as root; selects the existing Hermes container's auth mode."""

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Report or select the existing Hermes authentication mode without exposing credentials.\nUsage: hermes-auth-mode.py  [ARGUMENT ...]\n\nSource: hosts/nexus/files/usr/local/libexec/hermes-auth-mode.py in ~/ops\nSee man hermes-auth-mode.py for the existing call sites and argument handling.')
        raise SystemExit(0)
import os,pathlib,sys,yaml
root=pathlib.Path(os.environ.get('HERMES_HOME','/srv/containers/data/hermes/data'));p=root/'config.yaml'
d=yaml.safe_load(p.read_text());mode=sys.argv[1]
if mode not in ['chatgpt','api']:raise SystemExit('Use chatgpt or api')
model=d.get('model',{}).get('default','gpt-5.5').removeprefix('codex/')
d['model']={'provider':'openai-codex' if mode=='chatgpt' else 'openai','default':model}
for block in d.get('auxiliary',{}).values():
    if isinstance(block,dict) and 'provider' in block:
        block.update({'provider':d['model']['provider'],'model':model,'base_url':''})
        if 'api_key' in block:block['api_key']=''
providers=d.setdefault('providers',{})
providers['openai']={'name':'OpenAI API','base_url':'https://api.openai.com/v1','api_mode':'responses','model':model}
d['fallback_providers']=[]
d.setdefault('terminal',{}).update({'backend':'local','cwd':'/opt/data/workspace'})
d['timezone']='America/Toronto'
temp=p.with_suffix('.tmp');temp.write_text(yaml.safe_dump(d,sort_keys=False));temp.chmod(0o600);temp.replace(p)
print('Hermes provider selected: '+mode+'; credentials remain private')
