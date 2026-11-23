# Tensor visual standby

Configured 2026-10-12.

## Commands

On Tensor, run `hibernate` to enter visual standby. `hibernate resume` restores it manually, including over SSH. `hibernate status` prints `awake` or `visual standby`. No sudo is required. These commands do not perform kernel hibernation or suspend.

After 1800 seconds without local input, Hypridle runs the same command. Keyboard or mouse activity restores displays and lighting. A one-second idle listener also handles resume after manually invoking standby. Existing manual locking remains available and is not added to automatic idle standby. Idle inhibitors are ignored for these listeners, so video playback does not suppress the requested 30-minute inactivity behavior.

The host, RAM, storage, network, running applications, and SSH remain powered and available. Turning RAM/storage off would be incompatible with operating this running computer through SSH.

## Lighting and cooling

Before changing lighting, the helper saves native OpenRGB active modes, effect parameters and individual LED colors directly into a private local JSON file, an OpenLinkHub user-profile snapshot per controller, and individual SDK-owned Corsair LED colors. Repeated entry while already in standby does not overwrite the saved state with black.

Standby turns displays/RGB off and assigns the existing case-fan Off curves while preserving the AIO pump/radiator cooling assignments. Resume loads the saved OpenRGB modes/colors, restores the saved OpenLinkHub lighting profile/effects, restores SDK-owned individual Corsair colors, then assigns every speed-controlled channel its saved default cooling profile. If lighting was already off before entry, it remains off after resume. btop returns to DP-3/workspace 10.

OpenLinkHub's restored snapshot appears as user profile `TensorVisualResume`; its lighting matches the captured state, while fan speed assignments are reset to those from `default`. Saved temperature curves are not edited. Externally animated SDK lighting resumes its captured LED frame; an external effects producer must continue running to resume its animation.

State is private under `~/.local/state/tensor-control/`; the active standby marker is under `/run/user/1000/`, so stale state is not automatically resumed after reboot. Entry/resume and RGB changes use locks. Failed restoration retains the snapshot and marker for retry with `hibernate resume`.

## Installed changes

- Added `~/.local/bin/hibernate` and `~/.local/share/tensor-control/visual-standby.py`.
- Replaced Hypridle's prior 300-second locked-only rule with the 1800-second standby rule and input-resume listener.
- Enabled one managed `hypridle.service`; updated session startup to start that same service instead of launching a second daemon.
- Updated `monitors on/off`, monitor resume hooks, and manual lock display handling to share the snapshot restoration path and avoid forcing red/default RGB on wake.
- Extended the existing RGB API helper to support the OpenLinkHub PUT profile-save operation.

Observed: one Hypridle process, service active/enabled, two rules loaded, compositor/input connection established. Profile-save/load and LED restore APIs were inspected. No standby/resume cycle or 30-minute wait was run during installation; first physical key wake remains to be observed.

### Profile restore repair

The user's first `hibernate resume` failed because OpenRGB's SDK save request did not create the named server-side profile. Recovered that standby using its recorded RGB-off state, restored the saved Corsair lighting and default fan curves, and cleared the standby marker. Tensor is awake and Hypridle is active.

Future capture uses snapshot format 3, storing full active-mode settings and per-LED colors directly in `visual-standby-snapshot.json`. It bypasses both server profile saves and the Python SDK's older binary profile format, which rejects brightness fields present in newer controllers. Controller identity and LED-count checks remain in place. A separate four-controller local recovery snapshot was successfully written during repair.

Following the secondary display wake workaround, the user requested a live cycle: `hibernate`, wait 10 seconds, then `hibernate resume`. Entry and restore completed successfully with format 3. The user confirmed the green display flicker is gone. This cycle used command-based resume; keyboard-triggered resume and the full 30-minute timer remain unobserved.

Repair backups: `~/.local/state/tensor-control/profile-fix-20261012/`. The original failed snapshot is retained there for reference.

## Rollback

While still in the graphical session, run `hibernate resume` first if in standby. Stop `systemctl --user stop hypridle.service`. Restore the corresponding files from `~/.local/state/tensor-control/visual-standby-backup-20261012/` (names use underscores in place of slashes). The prior Hypridle service was disabled; restore that state with `systemctl --user disable hypridle.service`, then launch Hypridle using the prior session startup configuration. Remove only the new hibernate wrapper/helper if they did not exist before.

OpenLinkHub's pre-change database is preserved at `/var/lib/tensor-control-backup-20261012/visual-standby-database`. Prefer leaving the harmless TensorVisualResume snapshots in place; restore that database only with OpenLinkHub stopped if rollback of changed active profiles is needed. Existing OpenRGB/OpenLinkHub and Home Assistant controls remain configured.
