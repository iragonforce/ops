# Tensor input-control setup — 2026-10-14

## MX Master 3 completed after SSH recovery

- Solaar's user service is installed, active, and enabled. The desktop startup script restarts it after importing the current graphical environment, preserving unrelated startup commands.
- Mouse serial `883F2247`, receiver device WPID `4082`, is now online on Tensor with 100% battery.
- Live device readback confirms 1000 DPI, ratcheted/adaptive scrolling with SmartShift threshold 20, and thumb-rest button diversion. Solaar's saved Mouse Gestures mode uses hardware diversion plus software interpretation.
- Five rules are saved and loaded for this mouse only. Back/Forward, middle-click, the wheel-mode button, and native horizontal thumb-wheel scrolling remain normal.
- Thumb-rest click opens the application launcher. Hold it and move left/right to switch existing desktops; up toggles fullscreen; down toggles floating mode. These actions call native Hyprland APIs, avoiding simulated modifier keys under Wayland.
- Run `mx-master-settings` or `solaar` to open the GUI and Rule Editor. Physical gesture response still requires user confirmation.
- Input Remapper is installed but inactive; its existing autoload map is empty. Existing older presets were preserved and not activated. Do not run the earlier `finish-setup.sh` just to configure this mouse.
- Mouse setup backups: `~/.local/state/input-controls-20261014/mx-master3-before/manifest.json` and the files named there. No firmware was flashed and pairing was preserved.

### Mouse rollback

Stop and disable `solaar.service`. Restore files listed as previously existing in the backup manifest, and remove files listed as new. Preserve later edits to the desktop startup script; remove only its MX Master Solaar restart block if appropriate. Reload the user manager and start Solaar again if retaining the prior Logitech settings. No package removal is required.

The sections below describe the initial installation stage; the current mouse status above supersedes their pending mouse/service statements.

## Completed

- Identified Logitech Unifying receiver 046d:c52b with one paired MX Master 3.
- User confirmed MX Master 3 Easy-Switch channel **2** controls Tensor.
- Identified connected Keychron K2, USB 05ac:024f, through its stable input-device name.
- Installed Solaar 1.1.20-2 and evtest 1.36-1 from Arch repositories.
- Installed dependencies and built Input Remapper 2.2.1-1 from a reviewed AUR PKGBUILD,
  using the upstream release archive with checksum verification; no tests run.
- Pacman installed Input Remapper. Its systemd/udev/D-Bus post-install hooks subsequently failed.
- Preserved an unowned earlier input-remapper autostart file under
  `/var/lib/input-controls-20261014/input-remapper-autoload.desktop.before` before package installation.
- Existing active-session ACLs already allowed this user access to the receiver and /dev/uinput;
  Solaar supplied its normal uaccess rules. No world-writable permissions were added.
- At the initial installation stage, no firmware flashing, pairing removal, custom key mappings, or keyboard layout changes were performed.

## Initial prepared stage (superseded for Solaar)

`solaar.service`, startup changes, and `finish-setup.sh` are prepared on Qubit.
They start Solaar in the tray and restore user-selected Input Remapper autoload presets at desktop login.
The completion script patches the current startup file so later edits are preserved.
Run it as iragonforce on Tensor once systemd/D-Bus and SSH are working, after inspecting any existing
Input Remapper autoload presets. Existing remapping configuration has not yet been inventoried.

No claim is made that either GUI has been launched or that Input Remapper's service is active.
The mouse was reported offline by Solaar at the last successful device query. The user subsequently
confirmed channel 2 controls Tensor; a fresh device-settings query is pending SSH recovery.

## Software usage

- `solaar`: Logitech DPI/scrolling/buttons/device configuration and its Rule Editor.
- `input-remapper-gtk`: generic keyboard/mouse keybindings, combinations and macros on Wayland.
- Solaar rule features have Wayland limitations, particularly application-specific conditions and
  some simulated modifier handling; use Input Remapper or native Hyprland binds where appropriate.
- K2 key remapping can happen at the OS input layer. Actual Fn/backlight-key event exposure and
  firmware version/history have not yet been verified. No firmware alteration is needed for ordinary OS key remapping.

## Blocker and diagnostics

Pacman hooks reported `Reload daemon failed: Connection timed out`, udev varlink reload timeout,
and D-Bus reload `Transport endpoint is not connected`. Fresh SSH completed protocol negotiation,
then stalled after offering the user key. Nexus could still ping Tensor with ~0.08 ms latency.
This is not evidence that the Ethernet link detached again or that any firmware was flashed.
Local-console diagnostics or a user-initiated reboot may be required before continuing.

## Rollback

Stop/disable input-remapper.service and the future solaar.service before uninstalling their packages.
Restore the backed-up autostart file after removing the package-owned replacement if returning to the
prior installation state. Preserve ~/.config/input-remapper* and ~/.config/solaar configurations.
If finish-setup.sh is later run, its startup backup is ~/.local/state/input-controls-20261014/session-start.sh.before.
Do not remove shared Python/GTK dependencies automatically; other applications use them.

## References

- [Solaar capabilities](https://github.com/pwr-Solaar/Solaar/blob/master/docs/capabilities.md)
- [Solaar rule support and Wayland limitations](https://github.com/pwr-Solaar/Solaar/blob/master/docs/rules.md)
- [Input Remapper](https://github.com/sezanzeb/input-remapper)
- [Keychron OS key-remapping guidance](https://help-center.keychron.com/en-us/article/360021616533-how-to-remap-or-reassign-keys)
