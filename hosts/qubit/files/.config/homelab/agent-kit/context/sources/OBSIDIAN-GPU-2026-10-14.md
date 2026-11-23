# Tensor Obsidian GPU launch repair — 2026-10-14

## Finding

The running Obsidian process inherited global Electron fallback flags:
`--disable-gpu`, `--disable-gpu-compositing`, `--disable-software-rasterizer`, and disabled
VizDisplayCompositor. Its GPU subprocess used `--use-gl=disabled`.

The existing desktop shortcut already called `~/.local/bin/obsidian-gpu`, which filters those
flags. Hyprland startup instead ran the unqualified `obsidian` command. This user's shell PATH
also contains a different npm Obsidian CLI, so the startup command was ambiguous.

## Changes

- Startup now explicitly calls `/home/iragonforce/.local/bin/obsidian-gpu`.
- The same wrapper remains the desktop launcher.
- Wrapper selects NVIDIA PRIME rendering and enables GPU rasterization.
- Existing global Electron flags and the npm CLI were left intact.
- Obsidian was relaunched through the wrapper.
- Its existing full-screen/workspace rules remain in place.

No invented application configuration keys were added; no saved setting disabling hardware
acceleration was found in the checked JSON preferences.

## Verification

A temporary loopback-only Chromium diagnostics endpoint reported:

- Renderer: ANGLE / NVIDIA GeForce RTX 5070 / OpenGL 4.5.0 / driver 615.78.08.
- GPU compositing: enabled.
- WebGL: enabled.
- GPU rasterization: enabled_force.
- OpenGL and accelerated canvas: enabled.

After verification, Obsidian was restarted with identical permanent GPU configuration and
without diagnostic flags. No debugging endpoint is part of the persistent launcher.
The final normal-launch GPU subprocess appeared in NVIDIA's graphics process list using 437 MiB;
no GPU-disable flags remained, and port 19224 had no listener. The Obsidian window was full screen
on workspace 2.
These checks establish hardware rendering; graph-view frame rate has not been measured.
Complete reboot launch has not been observed yet.

## Rollback

Private backups on Tensor:
`~/.local/state/obsidian-gpu-fix-20261014/obsidian-gpu.before` and `session-start.sh.before`.

Restore these to `~/.local/bin/obsidian-gpu` and `~/.config/hypr/scripts/session-start.sh`,
then relaunch Obsidian. That restores the prior startup behavior, including inherited GPU
disable flags on that path. No vault content was edited.

Qubit copies of original and updated scripts are in `outputs/tensor-obsidian-gpu/current`
and `changed`. Animation research is in `WAYBAR-ANIMATIONS.md`.

Primary reference: [Electron GPU feature status API](https://www.electronjs.org/docs/latest/api/app#appgetgpufeaturestatus).
