#!/usr/bin/env python3
"""Own isolated nft table; preserve all other firewall configuration."""
import pathlib,subprocess
root=pathlib.Path('/var/lib/tensor-control-backup-20261012')
p=root/'nft-rules.before.txt'
if not p.exists():p.write_text(subprocess.check_output(['nft','list','ruleset'],text=True));p.chmod(0o600)
config=pathlib.Path('/etc/tensor-control/guard.nft')
config.write_text('''table inet tensor_control {
 chain input {
  type filter hook input priority -10; policy accept;
  iifname "lo" accept
  tcp dport { 6742, 8769 } ip saddr { 192.168.4.2, 192.168.1.2, 192.168.1.4,192.168.1.102, 192.168.4.254, 100.103.67.56, 100.96.255.81 } accept
  tcp dport { 6742, 6743, 8769 } drop
 }
}
''')
script=pathlib.Path('/usr/local/sbin/tensor-control-guard')
script.write_text('''#!/bin/sh
set -eu
if nft list table inet tensor_control >/dev/null 2>&1; then
 { echo 'delete table inet tensor_control'; cat /etc/tensor-control/guard.nft; } | nft -f -
else nft -f /etc/tensor-control/guard.nft; fi
''');script.chmod(0o700)
pathlib.Path('/etc/systemd/system/tensor-control-guard.service').write_text('''[Unit]
Description=Limit Tensor SDK and fixed controls to trusted hosts
Before=tensor-control.service
After=network-pre.target
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/tensor-control-guard
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
''')
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','enable','--now','tensor-control-guard'],check=True)
print('Dedicated Tensor controls firewall enabled')
