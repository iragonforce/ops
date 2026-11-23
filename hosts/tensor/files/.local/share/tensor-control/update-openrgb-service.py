#!/usr/bin/env python3
import pathlib,subprocess
p=pathlib.Path.home()/'.config/systemd/user/openrgb.service';s=p.read_text()
s=s.replace(' --client 127.0.0.1:6743','')
if 'ExecStartPost=' not in s:s=s.replace('Restart=on-failure','ExecStartPost=/home/iragonforce/.local/share/tensor-control/venv/bin/python /home/iragonforce/.local/share/tensor-control/openrgb-ready.py\nRestart=on-failure')
p.write_text(s)
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
subprocess.run(['systemctl','--user','restart','openrgb.service'],check=True)
print('Single hardware SDK; canonical controls separately use OpenLinkHub SDK')
