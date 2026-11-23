#!/usr/bin/env python3
import pathlib,subprocess
h=pathlib.Path.home();base=h/'.local/share/tensor-control'
rgb=f'{base}/venv/bin/python {base}/tensor-rgb.py'
desk=f'/usr/bin/python3 {base}/desktop.py'
def write(p,s):p.write_text(s);p.chmod(0o755)
for p,a in [(h/'.local/bin/rgb-off','off'),(h/'.local/bin/rgb-default','on'),(h/'.config/hypr/scripts/rgb-off.sh','off'),(h/'.config/hypr/scripts/rgb-on.sh','on')]:write(p,'#!/bin/sh\nexec '+rgb+' '+a+'\n')
write(h/'.local/bin/rgb','#!/bin/sh\nexec '+rgb+' "$@"\n')
write(h/'.local/bin/monitors',f'''#!/bin/bash
set -euo pipefail
case "${{1:-}}" in
 off) touch /run/user/1000/hypr-locked-dpms-off; {rgb} off; {desk} off ;;
 on) rm -f /run/user/1000/hypr-locked-dpms-off; {desk} on; {rgb} on ;;
 *) echo 'Use monitors on or monitors off' >&2; exit 2 ;;
esac
''')
p=h/'.config/hypr/scripts/monitor-resume.sh'
write(p,'''#!/bin/bash
set -euo pipefail
state_file=/run/user/1000/hypr-locked-dpms-off
if [[ "${1:-}" != --force && ! -e "$state_file" ]]; then exit 0; fi
exec /home/iragonforce/.local/bin/monitors on
''')
p=h/'.config/hypr/scripts/locked-idle-off.sh'
write(p,'''#!/bin/bash
set -euo pipefail
pidof hyprlock >/dev/null || exit 0
exec /home/iragonforce/.local/bin/monitors off
''')
p=h/'.config/hypr/scripts/session-start.sh';s=p.read_text()
s=s.replace("run_shell_once ghostty-btop 'ghostty --class=com.btop.term -e btop'",desk+' btop >>"$LOGDIR/btop-placement.log" 2>&1 &')
p.write_text(s)
p=h/'.config/hypr/hyprland.lua';s=p.read_text()
s=s.replace('hl.workspace_rule({ ["workspace"] = "10", ["monitor"] = "DP-3" })','hl.workspace_rule({ ["workspace"] = "10", ["monitor"] = "DP-3", ["default"] = true, ["persistent"] = true })')
p.write_text(s)
# Move the broken old unit aside: the session script owns btop.
p=h/'.config/systemd/user/btop-autostart.service'
if p.is_symlink() and not p.exists():p.rename(h/'.local/state/tensor-control/backup-20261012/btop-autostart.service.broken')
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
subprocess.run(['/usr/bin/python3',str(base/'desktop.py'),'btop'],check=True)
print('Installed unified rgb/monitors commands and persistent secondary btop placement')
