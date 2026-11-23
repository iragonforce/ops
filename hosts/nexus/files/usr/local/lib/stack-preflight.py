import sys,pathlib,subprocess,json
cfg=json.loads(subprocess.check_output(['docker','compose','-f',sys.argv[1],'config','--format','json'],text=True))
for name,s in cfg['services'].items():
 if s.get('profiles'):continue
 for m in s.get('volumes',[]):
  if m.get('type')=='bind':
   assert pathlib.Path(m['source']).exists(),f'Missing source for {name}: {m["source"]}'
 for net,n in s.get('networks',{}).items():
  ip=(n or {}).get('ipv4_address')
  if not ip or not ip.startswith(('192.168.2.','192.168.3.','192.168.4.','192.168.5.')):continue
  existing=subprocess.run(['docker','inspect',s.get('container_name',name)],capture_output=True,text=True)
  if existing.returncode==0 and json.loads(existing.stdout)[0]['State']['Running']:continue
  vlan=ip.split('.')[2]
  probe=subprocess.run(['arping','-D','-c','2','-w','3','-I','enp6s0.'+vlan,ip],capture_output=True)
  assert probe.returncode==0,f'Address conflict for {name}: {ip}'
