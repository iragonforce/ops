# Tensor standby lighting ownership

2026-10-18, America/Toronto. User requested native OpenLinkHub profiles for Corsair case/AIO controllers, OpenLinkHub Off on visual standby, and OpenRGB Default on wake.

## Observed causes

- tensor-rgb.py explicitly enabled OpenRGBIntegration on each hub and wrote Direct SDK frames through OpenLinkHub's bridge. Saved Off hub profiles also had integration enabled.
- The OpenRGB server was stopped; the checkpoint service repeatedly reported ConnectionRefusedError.
- Saved OpenRGB Default described old detector names/LED counts: Dominator RAM with 12 LEDs, an older GPU name and a 33-LED motherboard. Current discovery reports Vengeance RAM with 10 LEDs, the Gaming OC GPU and a three-LED motherboard.
- The old Python SDK's profile-load request did not complete cleanly with OpenRGB 1.1. The installed OpenRGB CLI successfully handles its current JSON profiles.

## Changes

- Updated ~/.local/share/tensor-control/tensor-rgb.py: select native OpenLinkHub Off/default profiles, force integration disabled, preserve protected AIO assignments, and never write SDK frames to the hub bridge or overwrite saved OpenRGB profiles during on/off commands.
- Updated visual-standby.py: capture the original hub profile name, restore that original native profile on wake, and load OpenRGB Default for the native motherboard/RAM/GPU controllers. Boot snapshot restore also retains native OpenLinkHub ownership.
- Default loading uses the installed OpenRGB CLI as a client with automatic connection disabled, then checks actual controller modes with a fresh SDK client.
- Rebased only OpenRGB profiles/Default.json onto the currently detected controller identities, capabilities and LED counts. Preserved chosen Direct/Spectrum Cycle effects and color palette; adjusted LED arrays to current sizes. Original JSON and mapping retained privately. Removed the temporary hardware-baseline profile from the UI after saving its recovery copy.
- Updated ~/.local/bin/hibernate to start its existing OpenRGB service if unavailable before enter/resume. A no-op resume with no standby marker remains a no-op.
- Started the existing OpenRGB service and restarted its checkpoint service. No Hyprland restart, real suspend, reboot, monitor blanking or network changes.

## Operational checks

A lighting-only Off/wake cycle passed: both hubs stayed native, saved Off profiles now have integration disabled, native OpenRGB devices switched off, protected AIO curve assignments remained intact, and original awake hub RGBProfiles/SpeedProfiles/profile paths were restored. Wake readback matched Default: RAM Direct, GPU Spectrum Cycle, motherboard Spectrum Cycle. OpenRGB, checkpoint service and hypridle were active; the fresh boot snapshot records native hub ownership.

No temperature curves or their 75°C safety ramp were edited. Motor behavior and the temperature-triggered ramp were not physically exercised. No formal tests were added/run. A complete display/keyboard wake cycle was not performed; portrait-screen flicker remains a separate pending issue. Existing idle timeout and wake key bindings were preserved.

## Rollback

Tensor user backup: ~/.local/state/tensor-control/recovery/standby-olh-20261018. Restore saved tensor-rgb.py, visual-standby.py and hibernate to their original locations; restore Default-before-hardware-mapping.json to ~/.config/OpenRGB/profiles/Default.json if reverting the profile migration. Original full OpenRGB configuration and snapshots are also preserved there.

Root OpenLinkHub profile backup: /var/backups/homelab/tensor-standby-olh-20261018/profiles. Restore profiles only while OpenLinkHub is stopped, then start it. Restart the checkpoint service after restoring helpers. Reverting old Off profiles also restores their old SDK-enabled behavior. Preserve newer user changes when choosing a rollback.
