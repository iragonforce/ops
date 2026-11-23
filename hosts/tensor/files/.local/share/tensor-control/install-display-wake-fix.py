#!/usr/bin/env python3
import pathlib,shutil,re
home=pathlib.Path.home();backup=home/'.local/state/tensor-control/display-wake-backup-20261012'
backup.mkdir(parents=True,exist_ok=True,mode=0o700)
for name in ['hyprland.lua','monitors.conf']:
 p=home/'.config/hypr'/name;b=backup/name
 if not b.exists():shutil.copy2(p,b)
p=home/'.config/hypr/hyprland.lua';s=p.read_text()
def rule(match):
 line=match.group(0)
 if '["vrr"]' not in line:line=line[:-3]+', ["vrr"] = 0, ["bitdepth"] = 8, ["cm"] = "srgb" })'
 return line
s=re.sub(r'hl\.monitor\(\{[^\n]*\["output"\] = "DP-3"[^\n]*\}\)',rule,s)
p.write_text(s)
p=home/'.config/hypr/monitors.conf';s=p.read_text()
def block(match):
 text=match.group(0)
 if 'LG Ultra HD 0x00063B9B' not in text:return text
 text=re.sub(r'(?m)^\s*(vrr|cm|bitdepth|sdr_min_luminance|sdr_max_luminance)\s*=.*\n','',text)
 return text[:-1]+'  vrr = 0\n  bitdepth = 8\n  cm = srgb\n}'
s=re.sub(r'monitorv2\s*\{[^}]*\}',block,s);p.write_text(s)
print('Secondary display configured for fixed-refresh 8-bit SDR; backups preserved')
