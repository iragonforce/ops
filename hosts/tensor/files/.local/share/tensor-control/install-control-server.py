#!/usr/bin/env python3
import json,pathlib,shutil,subprocess,sys
role=sys.argv[1];source=pathlib.Path(sys.argv[2])
assert role in ['tensor','nexus']
conf=pathlib.Path('/etc/tensor-control');conf.mkdir(mode=0o700,exist_ok=True)
shutil.copy2(source/'control.json',conf/'control.json');(conf/'control.json').chmod(0o600)
target=pathlib.Path('/usr/local/lib/tensor-control');target.mkdir(parents=True,exist_ok=True)
shutil.copy2(source/'control-server.py',target/'control-server.py');(target/'control-server.py').chmod(0o755)
p=pathlib.Path('/etc/systemd/system/tensor-control.service')
units='vlans.service' if role=='nexus' else 'openlinkhub.service user@1000.service'
p.write_text(f'''[Unit]
Description=Authenticated Tensor lighting, display and power controls ({role})
Wants=network-online.target {units}
After=network-online.target {units}
[Service]
Type=simple
User=iragonforce
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
LoadCredential=control.json:/etc/tensor-control/control.json
ExecStart=/usr/bin/python3 /usr/local/lib/tensor-control/control-server.py
Restart=on-failure
RestartSec=5
UMask=0077
[Install]
WantedBy=multi-user.target
''');p.chmod(0o644)
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','enable','--now','tensor-control.service'],check=True)
print('Authenticated fixed-action control service enabled on '+role)
