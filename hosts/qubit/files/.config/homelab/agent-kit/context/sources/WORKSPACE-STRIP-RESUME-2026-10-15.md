# Tensor center workspace strip DPMS recovery — 2026-10-15

## Cause observed

The center strip process was alive and its layer surface was on DP-5, but its process environment contained `WAYBAR_PRIMARY_OUTPUT=FALLBACK`. Live Hyprland monitors were DP-5 and DP-3, with occupied workspaces 1, 2, 3 and 5 on DP-5 plus workspace 10 on DP-3. The launcher selected an output only once during startup. Restarting the service during a DPMS transition could cache Hyprland's temporary FALLBACK output, and the Python strip then filtered normal desktops against that nonexistent output indefinitely. The original center surface was only 100 px wide.

## Changes

- `~/.config/hypr/scripts/start-workspace-strip.sh`: no longer caches a monitor name before the Python app starts; clears the inherited output override.
- `~/.config/waybar/workspace-strip.py`: resolves a live, non-disabled physical monitor instead of trusting stale output names; prefers the 3440x1440 primary display, then focused/first available display. Rejects temporary FALLBACK-only monitor lists without clearing the last good buttons. Rebinds when the selected output changes. Adds an in-process two-second refresh retry and bounds Hyprland queries to three seconds. Preserves existing icons, workspace filtering/order, drag and app-preserving close behavior.
- Logs selected output and rendered workspace IDs on button rebuild, without client titles.
- Restarted only `workspace-strip.service`; no compositor, side Waybar, desktop apps, lighting or fan controls were restarted/changed.

## Operational checks

Follow-up UI request: workspace buttons now show their numeric ID on pointer enter and restore their existing icon on pointer leave, ignoring GTK child-crossing events. The plus control is now a separate compact rounded button on the left, with a 7px gap from the workspace pill, a subtle outline/background, and brighter hover feedback. Changes are confined to the center app's own widget tree and inline CSS; shared side-bar styling was not edited. Exercised actual GTK enter/leave signals on real buttons for IDs 1,2,3,10: each icon → number → icon check passed. The restarted live strip remains one DP-5 surface (265px wide), with no startup/CSS errors in its service journal. Physical pointer behavior and appearance still need user confirmation. Existing rollback files below predate both changes.

Python compile and shell syntax checks passed. Installed files read back equal to staged files. The running strip logged `Workspace strip output=DP-5 workspaces=10,1,2,3,5`; its single actual layer surface on DP-5 measured 268 px wide. Invoking the actual selection function with live Hyprland monitor data and the previously broken inherited FALLBACK value selected DP-5. Invoked `tensor-desktop.py bars`, the existing bar-recovery path used by visual standby resume; subsequent service readback remained active and rendered the same workspace IDs. No formal test suite was added or run.

A full visual-standby cycle was not triggered to avoid blanking the user's active desktop. Physical icon appearance and repeated `hibernate`/resume behavior remain for user confirmation. This change addresses observed cached-output filtering, not the separate historical portrait-display flicker issue.

## Rollback

Tensor private backup directory: `~/.local/state/workspace-strip-resume-fix/`.
Restore `workspace-strip.py.before` to `~/.config/waybar/workspace-strip.py` and `start-workspace-strip.sh.before` to `~/.config/hypr/scripts/start-workspace-strip.sh`, retaining executable mode, then restart only `systemctl --user restart workspace-strip.service`. Backup files preserve the old cached-output bug. No full kit/runtime redeployment was performed.
