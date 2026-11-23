#!/usr/bin/python3
# Relay the existing Checkmk monitoring request. See relay.py(1) for source and integration details.
"""Forced SSH command on Nexus, root owned; four fixed read-only collectors."""

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Relay the existing Checkmk monitoring request.\nUsage: relay.py  [ARGUMENT ...]\n\nSource: hosts/nexus/files/usr/local/libexec/checkmk/relay.py in ~/ops\nSee man relay.py for the existing call sites and argument handling.')
        raise SystemExit(0)
import pathlib,subprocess,sys
root=pathlib.Path('/etc/nexus/secrets/checkmk')
host=sys.argv[1] if len(sys.argv)==2 else ''
if host=='nexus':
    subprocess.run(['/usr/local/libexec/checkmk/agent-linux'],check=True)
    print('<<<local:sep(0)>>>',flush=True)
    subprocess.run(['/usr/bin/python3','/usr/local/libexec/checkmk/local-checks.py'],check=True)
elif host in ['qubit','tensor','udr7']:
    target={'qubit':'iragonforce@100.103.67.56','tensor':'iragonforce@100.114.178.50','udr7':'root@192.168.1.1'}[host]
    command=['/usr/bin/ssh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
             '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','-o','UserKnownHostsFile='+str(root/'known_hosts'),
             '-i',str(root/'relay_ed25519'),target]
    subprocess.run(command,check=True,timeout=80)
else:raise SystemExit('Collector must be nexus, qubit, tensor, or udr7')
