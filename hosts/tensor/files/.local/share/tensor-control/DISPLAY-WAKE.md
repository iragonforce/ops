# Secondary 4K display wake workaround

Applied 2026-10-12 in response to green flickering after visual standby.

## Findings

- Secondary LG Ultra HD: DP-3, connected to AMD iGPU PCI 0000:73:00.0 (`amdgpu`), 3840×2160 at approximately 60 Hz, portrait transform 3, scale approximately 5/3.
- Main LG ultrawide: DP-5, connected to RTX 5070 PCI 0000:01:00.0 (`nvidia`), 3440×1440 at approximately 160 Hz.
- Live outputs were already 8-bit and VRR was inactive. The saved secondary monitor profile nevertheless requested VRR and automatic color management with SDR luminance overrides.
- No matching recent GPU/display kernel errors were found. A specific hardware/driver cause is not established.

## Changes

- Set the secondary monitor's static and generated saved rules to fixed refresh (`vrr=0`), 8-bit (`bitdepth=8`), sRGB (`cm=srgb`). Removed its generated SDR luminance overrides. Main monitor profile was preserved.
- Added `reset_secondary()` and `wake()` to the existing desktop helper. When waking DP-3 from DPMS off, the helper briefly changes the same 4K output to its supported 30 Hz mode, then returns to the prior approximately 60 Hz mode. The temporary mode keeps the same position, rotation and scale; the final mode is restored in a `finally` block.
- Routed visual-standby resume and regular display-on handling through `wake()`.
- Added a manual repair action: `python ~/.local/share/tensor-control/desktop.py repair-display`.

The mode switch was applied to the running secondary output. Hyprland reports no configuration errors; DP-3 is 3840×2160 at 59.997 Hz and workspace 10, while DP-5 remains at 159.962 Hz and workspace 1.

At the user's request, `hibernate` was run, followed by `hibernate resume` after 10 seconds. Both completed successfully, restoring displays, saved lighting, and default cooling profiles. The user confirmed the green flicker is gone. No kernel suspend or reboot was performed.

## Rollback

Restore `hyprland.lua` and `monitors.conf` from `~/.local/state/tensor-control/display-wake-backup-20261012/`. Restore desktop and standby helpers from `~/.local/share/tensor-control/tensor-desktop.before-display-fix.py` and `visual-standby.before-display-fix.py`. Reload Hyprland's configuration in the current graphical session. Do not restart the compositor while unsaved applications are running.

Official references: [monitor modes](https://wiki.hypr.land/configuring/core/monitors/modes/) and [monitor color settings source](https://github.com/hyprwm/hyprland-wiki/blob/main/content/configuring/core/monitors/colors.md).
