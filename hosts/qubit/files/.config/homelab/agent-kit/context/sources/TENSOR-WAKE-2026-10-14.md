# Tensor wake, desktop, and reboot state changes — 2026-10-14

## Host and verified baseline

Tensor: Arch Linux, LAN 192.168.1.3, Tailscale 100.114.178.50.
Kernel 7.2.9-arch1-1; Hyprland 0.56.2; Aquamarine 0.15.1.
Intel I226-V Ethernet: enp6s0, MAC bc:fc:e7:6f:95:42, PCI 0000:06:00.0.
Primary ultrawide DP-5 uses NVIDIA RTX 5070; vertical LG 4K DP-3 uses AMD Radeon 610M.

Before changes, the previous boot recorded repeated Ethernet link flaps followed by
`igc 0000:06:00.0 enp6s0: PCIe link lost, device now detached` at 01:21:33.
EEE was already disabled and runtime PM already set to on. NIC PCIe ASPM L1 was enabled.
There is no evidence that the visual standby command suspended the host.
The stale pacman lock seen earlier was absent after the user's reboot; no lock was deleted.

## Implemented

### Ethernet

- Disabled PCIe ASPM/L1 substate power saving only on the identified Intel NIC link.
- Persisted the setting through `/etc/udev/rules.d/85-tensor-ethernet.rules` and
  `tensor-ethernet-stability.service`, ordered before NetworkManager.
- Runtime PM remains on. Wake-on-LAN remains enabled (`g`).
- No management IP, DNS, IPv6, router, mirrorlist, or other device's power policy was changed.
- This is a mitigation for the observed PCIe detachment. Long idle operation is still needed
  to determine whether the NIC/firmware problem recurs.

### Workspace center bar

- Existing Waybar left/right surfaces retained. The center pill is a separate GTK layer-shell process.
- Added `workspace-strip.service`, automatic failure restart, independent startup and resume recreation.
- Corrected workspace actions to Hyprland's Lua dispatcher API; the old helper sent Lua text to the legacy dispatcher.
- Dragging reorders workspace buttons and saves their order.
- Closing a nonpersistent workspace moves its windows to another workspace; it never sends window close/kill.
- Workspace 10 remains protected for the secondary btop display.
- Added a plus button visible only on the center pill's right-edge hover; it creates an unused workspace ID.
- Center icon size 22 px, consistent button spacing and 49 px overall height.
- Rebinds monitor selection after output changes and restarts the center surface after wake.

### Window rules

- Active configuration is `~/.config/hypr/hyprland.lua`; the legacy `.conf` was not edited.
- Obsidian starts full screen on workspace 2; the already-running window was also made full screen.
- XP-Pen `PenTablet` starts floating, centered, 900×650; the existing window was resized accordingly.
- Existing Super+V floating toggle and window move/resize bindings retained.

### Vertical 4K wake flicker

- Fixed the generated `monitors.conf` profile, which still enabled VRR and automatic color management.
- Added an override in `monitors.lua` for this LG display so regenerated profiles retain
  3840×2160 at 60 Hz, VRR off, 8-bit SDR/sRGB.
- Wake waits for DPMS acknowledgement and physical panel settling, then switches 30 Hz → 60 Hz.
- An additional reset occurs after RGB restoration, btop placement, and bar recreation settle.
- Earlier attempts that reset only before btop/bar recovery still flickered, despite manual reset clearing it.
- The user confirmed **no flicker** after the final 10-second standby/wake cycle with the reset at the end.
- Added `monitors repair` to repeat the display-only reset without rebooting or closing applications.
- `AQ_MGPU_NO_EXPLICIT` was investigated but not persisted; its value is cached by Aquamarine.
  No experimental kernel graphics parameters or compositor restart were applied.

### RGB/fan persistence

- Removed unconditional `rgb-on.sh` invocation from desktop startup, which forced a startup color.
- Added `tensor-rgb-persistence.service` to restore actual native modes/effect settings/LED colors
  and saved OpenLinkHub fan/lighting profiles at the next boot.
- Checkpoints every 60 seconds and on orderly service shutdown; native snapshot data is private.
- OpenLinkHub profiles are saved when their settings change rather than rewritten every checkpoint.
- Captures a separate awake-state checkpoint before visual standby. Temporary standby RGB-off/fan-Off
  settings cannot overwrite the intended reboot state.
- Reboot restoration retains saved fan profiles. Normal visual standby resume keeps the pre-existing
  behavior of selecting default fan curves.
- User-manager shutdown is ordered before OpenLinkHub shutdown; the checkpoint service stops before OpenRGB.
- Existing AIO protection and the user-defined Off curve/75°C thermal override were not changed.
- Sudden power loss can lose changes since the last completed checkpoint (up to approximately 60 seconds).
- Complete machine reboot restoration has not been observed yet.

### Boot console and watchdog

- `/etc/vconsole.conf` referenced missing `ter-v12n`; replaced it with installed `default8x16`.
- Restarted `systemd-vconsole-setup.service` successfully and rebuilt both normal and LTS initramfs images.
- Retained hardware reboot watchdog. Runtime watchdog was already disabled, reboot watchdog was 10 minutes,
  and hardware `nowayout` was 0. The shutdown warning alone did not establish a fault requiring disablement.
- Disabled the duplicate system Ollama unit, which failed because the working user Ollama unit owns port 11434.
  The working user service remains active.

## Checks performed

- SSH worked during visual standby and after wake. Google returned HTTP 200 after wake in ~0.17 seconds.
- Arch mirror returned HTTP 200 in ~0.03 seconds; a VLC package was fetched successfully to /dev/null.
  VLC was not installed. These short transfers are not a 2.3 Gb/s WAN throughput measurement.
- Ethernet: 2500 Mb/s, full duplex, link detected; WOL g; NIC ASPM L1 read back as 0.
- No new NIC detach/PCIe error appeared during the observed cycles.
- Both monitor DPMS states returned on; vertical display 60 Hz/XRGB8888, primary ~159.96 Hz/XRGB8888.
- Both Waybar and workspace-strip surfaces present on DP-5; each height 49.
- One center-strip service, zero automatic restarts; Hyprland reports no configuration errors.
- Obsidian full-screen state 2; XP-Pen floating true and 900×650.
- No failed system units after the console fix and removal of the duplicate Ollama unit.
- Reboot-state snapshot format 3 exists and includes four native RGB controllers and two OpenLinkHub controllers.
- Checkpoint service stop logged `Shutdown lighting/fan checkpoint saved`; it restarted successfully.
- The final display wake cycle completed and the user confirmed no green flicker.

## Rollback and records

Private original files, NIC power values, NetworkManager reference copy, initramfs images, and a manifest:
`/var/lib/tensor-wake-fix-20261014` on Tensor (root-only).
Detailed rollback: `/var/lib/tensor-wake-fix-20261014/ROLLBACK.md`.

Stop and disable the new user services before reverting them. Disable
`tensor-ethernet-stability.service` before removing the NIC unit/script/udev rule.
Restore original desktop files from the manifest, reload system and user managers, and reload Hyprland
using its live session environment. Restore both saved monitor configuration files together.
For the console rollback restore vconsole.conf and matching saved initramfs images together.
Re-enabling the duplicate system Ollama unit recreates its port conflict.

Qubit reference files: `outputs/tensor-wake-fix/current` (originals), `changed` (installed sources), and this record.
No secrets are included. Do not rerun install.py: it deliberately refuses to replace the existing backup.

## Remaining observations

- Full reboot restoration, extended idle NIC stability, and repeated physical display wake behavior.
- The drag/drop/hover affordances are installed; their physical mouse interaction has not been observed by Codex.
- Tensor has a local IPv6 ULA/default RA but no working public IPv6 connection in the checks; IPv4 works.
  No IPv6 or router changes were made during this repair.

## Primary references consulted

- [Hyprland Lua dispatchers and window control](https://wiki.hypr.land/configuring/code-snippets/)
- [Hyprland multi-GPU environment options](https://wiki.hypr.land/configuring/core/environment-variables/)
- [Linux PCI sysfs interface](https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci)
- [systemd watchdog configuration](https://github.com/systemd/systemd/blob/main/man/systemd-system.conf.xml)
- [AMDGPU module parameters](https://docs.kernel.org/gpu/amdgpu/module-parameters.html)

## Follow-up: plus hover repair

The user reported that the plus did not appear. Replaced the invisible/insensitive button
inside an EventBox with a normal, always-interactive 30 px button. Only its glyph is hidden
between hovers; enter/motion reveals it and leaving hides it. Restarted only workspace-strip.service.
The service is active, its center surface is present, and no configuration error was reported.
The prior version is saved on Tensor at
`~/.local/state/tensor-wake-fix-20261014/workspace-strip.before-plus-fix.py`.
