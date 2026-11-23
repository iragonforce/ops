# Tensor Bluetooth and right Waybar widget — 2026-10-15

## Changes

Tensor had an unblocked kernel Bluetooth adapter hci0 but no BlueZ daemon, utilities or manager. Installed only bluez 5.87-2, bluez-utils 5.87-2 and blueman 2.4.6-2 using the existing Pacman database, without a system upgrade. Package hooks regenerated existing initramfs images successfully. Enabled/started bluetooth.service and powered hci0 on. The first immediate power request raced service/controller initialization and returned no default controller; a subsequent normal-user power request succeeded. BlueZ's installed default main.conf retains AutoEnable=true as its documented/default commented setting; no custom daemon configuration or pairing data was written by this task.

Added native `bluetooth` to `group/pill-right` immediately after tray, before audio. Icon is shown in on/off/no-controller states, dimmed off, with a connection count when connected and status/device tooltips. Left click runs blueman-manager; right click runs `~/.local/bin/bluetooth-toggle`. The small helper reads controller power status and toggles it using bluetoothctl as the normal user. CSS matches the existing right pill. Config template and the actual generated `/run/user/1000/waybar-config-iragonforce.jsonc` were updated, then the existing Waybar process reloaded using SIGUSR2. Center workspace code/service and app placements were not changed.

## Checks and limits

- Bluetooth service active and enabled; D-Bus Adapter1 Powered=true and Discoverable=false; rfkill unblocked.
- Actual installed right-click helper powered off then on successfully with D-Bus property readback; final power left on.
- Native module options checked against installed waybar-bluetooth(5). Generated configuration parsed and contained bluetooth in the right group. GTK CSS/config reload succeeded; actual accessible Waybar tree contained the Bluetooth icon label. Hyprland layer readback showed one Waybar surface plus one center-strip surface on DP-5, not duplicates.
- blueman-manager command exists; packages installed at the versions above. No device pairing/connection, audio playback, reboot persistence, physical click or physical visual appearance was exercised. No pairing/trust records were deleted. Discoverability was not enabled. Historical tray/child-process warnings in Waybar's existing log predate this change and were not treated as new Bluetooth failures.

## Rollback

Tensor backups: `~/.local/state/waybar-bluetooth-20261015/{config.jsonc.before,style.css.before,runtime-config.jsonc.before}`. Restore template/style and matching generated runtime configuration, then SIGUSR2 only the live Waybar PID. Remove the newly added `~/.local/bin/bluetooth-toggle` if no longer used. Disable/stop bluetooth.service and power off for the prior disabled-radio-service state; bluez/bluez-utils/blueman were absent before this task, so they may be removed only after checking no new dependents or user devices require them. Do not erase `/var/lib/bluetooth` as routine rollback. Private staged installer/helper live under the same state directory, not the home root. Full kit mirror/runtime deployment was not run.
