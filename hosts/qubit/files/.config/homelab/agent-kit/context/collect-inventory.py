#!/usr/bin/env python3
# Collect metadata for the existing historical infrastructure inventory; do not repeat discovery without need. See collect-inventory.py(1) for source and integration details.
"""Run on Nexus. Export selected infrastructure metadata, never config/env values."""

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Collect metadata for the existing historical infrastructure inventory; do not repeat discovery without need.\nUsage: collect-inventory.py \n\nSource: hosts/qubit/files/.config/homelab/agent-kit/context/collect-inventory.py in ~/ops\nSee man collect-inventory.py for the existing call sites and argument handling.')
        raise SystemExit(0)
import datetime
import json
import socket
import subprocess

def run(argv):
    return subprocess.check_output(argv, text=True, timeout=25).strip()

container_ids = run(['sudo', '-n', 'docker', 'ps', '-aq']).split()
containers = []
for item in json.loads(run(['sudo', '-n', 'docker', 'inspect', *container_ids])):
    labels = item['Config'].get('Labels') or {}
    state = item['State']
    containers.append({
        'name': item['Name'].lstrip('/'), 'image': item['Config']['Image'],
        'image_id': item['Image'], 'status': state['Status'],
        'exit_code': state['ExitCode'], 'finished_at': state.get('FinishedAt'),
        'health': state.get('Health', {}).get('Status'),
        'restart_policy': item['HostConfig']['RestartPolicy']['Name'],
        'compose_project': labels.get('com.docker.compose.project'),
        'compose_service': labels.get('com.docker.compose.service'),
        'networks': [{'name': name, 'ipv4': net.get('IPAddress'),
                      'mac': net.get('MacAddress')} for name, net in item['NetworkSettings']['Networks'].items()],
        'mounts': [{'source': mount.get('Source'), 'target': mount['Destination'],
                    'type': mount['Type'], 'writable': mount['RW']} for mount in item['Mounts']],
        'published_ports': item['NetworkSettings'].get('Ports'),
    })
networks = []
network_ids = run(['sudo', '-n', 'docker', 'network', 'ls', '-q']).split()
for net in json.loads(run(['sudo', '-n', 'docker', 'network', 'inspect', *network_ids])):
    networks.append({'name': net['Name'], 'driver': net['Driver'],
                     'internal': net['Internal'], 'ipam': net['IPAM'].get('Config', [])})
result = {
    'collected_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'Nexus metadata only; no environment, credentials, health-log contents, or application data',
    'host': socket.gethostname(), 'tailscale_ipv4': run(['tailscale', 'ip', '-4']),
    'zpool_summary': run(['sudo', '-n', 'zpool', 'list', '-H', '-o', 'name,size,alloc,free,health']),
    'zpool_status': run(['sudo', '-n', 'zpool', 'status', '-x']),
    'nfs_exports': run(['sudo', '-n', 'exportfs', '-v']),
    'containers': sorted(containers, key=lambda entry: entry['name']),
    'networks': sorted(networks, key=lambda entry: entry['name']),
}
print(json.dumps(result, indent=2))
