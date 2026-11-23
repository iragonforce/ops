#!/usr/bin/env python3
import os,pathlib,shutil,subprocess
BASE=pathlib.Path.home()/'.local/share/tensor-control'
HOME=pathlib.Path.home();BIN=HOME/'.local/bin';BACKUP=HOME/'.local/state/tensor-control/visual-standby-backup-20261012'
BACKUP.mkdir(parents=True,exist_ok=True,mode=0o700)
paths=['.config/hypr/hypridle.conf','.config/hypr/scripts/monitor-resume.sh','.config/hypr/scripts/session-start.sh','.config/hypr/scripts/lock-manual.sh','.local/bin/monitors','.local/bin/hibernate']
for name in paths:
    p=HOME/name;b=BACKUP/name.replace('/','_')
    if p.exists() and not b.exists():shutil.copy2(p,b)
shutil.copy2(BASE/'hypridle-visual-standby.conf',HOME/'.config/hypr/hypridle.conf')
wrapper='''#!/bin/bash
set -euo pipefail
action=${1:-enter}
if [[ "$action" == resume && ! -f /run/user/1000/tensor-visual-standby.json ]]; then exit 0; fi
exec /home/iragonforce/.local/share/tensor-control/venv/bin/python /home/iragonforce/.local/share/tensor-control/visual-standby.py "$action"
'''
p=BIN/'hibernate';p.write_text(wrapper);p.chmod(0o755)
# Existing manual/HA monitor controls share the same snapshot and restoration.
p=BIN/'monitors';p.write_text('''#!/bin/bash
set -euo pipefail
case "${1:-}" in
 off) exec /home/iragonforce/.local/bin/hibernate ;;
 on)
   if [[ -f /run/user/1000/tensor-visual-standby.json ]]; then exec /home/iragonforce/.local/bin/hibernate resume; fi
   exec /usr/bin/python3 /home/iragonforce/.local/share/tensor-control/desktop.py on ;;
 *) echo 'Use monitors on or monitors off' >&2; exit 2 ;;
esac
''');p.chmod(0o755)
p=HOME/'.config/hypr/scripts/monitor-resume.sh';p.write_text('''#!/bin/bash
set -euo pipefail
exec /home/iragonforce/.local/bin/hibernate resume
''');p.chmod(0o755)
p=HOME/'.config/hypr/scripts/session-start.sh'
s=p.read_text().replace('run_once hypridle hypridle','systemctl --user start hypridle.service >>"$LOGDIR/hypridle-start.log" 2>&1 || true')
p.write_text(s)
p=HOME/'.config/hypr/scripts/lock-manual.sh'
p.write_text('''#!/bin/bash
set -euo pipefail
if pidof hyprlock >/dev/null 2>&1; then exit 0; fi
/home/iragonforce/.local/bin/monitors on
hyprlock
/home/iragonforce/.local/bin/monitors on
''');p.chmod(0o755)
subprocess.run(['systemctl','--user','stop','hypridle.service'],check=True)
subprocess.run(['pkill','-x','hypridle'],check=False)
subprocess.run(['systemctl','--user','enable','--now','hypridle.service'],check=True)
print('Installed hibernate visual standby and one managed idle daemon; timeout 1800 seconds')
