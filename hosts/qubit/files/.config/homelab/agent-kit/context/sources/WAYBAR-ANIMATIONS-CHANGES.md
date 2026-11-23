# Tensor Waybar transitions — 2026-10-14

Installed on Tensor:

- Color hover transitions: 100 ms ease-out.
- General hover backgrounds/borders: 150 ms; shadows: 180 ms.
- Workspace background/active transitions: 160 ms; active hover slightly brighter.
- Plus reveal/hide: 120 ms CSS opacity fade.
- The plus button stays mapped and interactive; its `plus-visible` class controls only the glyph.
- Fixed widths, padding, icon sizing, and drag/reorder behavior retained.

Files: `~/.config/waybar/style.css` and `~/.config/waybar/workspace-strip.py`.
Waybar reloaded via SIGUSR2; the center strip restarted independently. Current reload logs
showed no CSS parsing errors. Physical animation appearance has not been observed by Codex.

Rollback copies on Tensor:
`~/.local/state/waybar-animations-20261014/{style.css.before,workspace-strip.py.before}`.
Restore these to their original paths, reload Waybar with `pkill -USR2 -x waybar`, then restart
`workspace-strip.service` after the Waybar reload finishes.

Original and installed sources are saved alongside this record under `current/` and `changed/`.
