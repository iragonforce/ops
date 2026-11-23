# Tensor SSH and visual standby — 2026-10-14

## Completed changes

- `/etc/ssh/sshd_config.d/00-local-ssh.conf`: use local authorized keys, disable reverse DNS, reduce prior DEBUG3 logging to INFO, and set client keepalives. Local keys and authentication policy were preserved.
- `/etc/systemd/system/sshd.service.d/30-local-userdb.conf`: set `SYSTEMD_BYPASS_USERDB=1` for sshd. This bypasses userdb IPC during supplementary-group lookup. Global NSS and PAM configuration remain unchanged.
- `tailscale set --ssh=false`: stop intercepting port 22 with Tailscale SSH's browser authorization flow. The installed OpenSSH daemon now handles SSH over the encrypted Tailscale network with the existing keys.
- `tensor-desktop.py`: discover the live Hyprland socket directly; bound compositor calls to 8 seconds and fallback user-manager lookups to 3 seconds. A failed workspace-bar manager call no longer prevents display/RGB recovery.
- `visual-standby.py` and `tensor-desktop.py`: remove automatic repeated 30/60 Hz transitions after wake. Explicit `monitors repair` remains available.
- `~/.config/hypr/hyprland.lua`: add `AQ_MGPU_NO_EXPLICIT=1` before monitor configuration. This changes cross-GPU buffer synchronization for the NVIDIA-rendered, AMD-connected portrait display. **A new Hyprland session is required; the active session cached the old value. This is a proposed graphics workaround awaiting physical validation, not a confirmed permanent repair.**

## Checks performed

- `sshd -t` passed before sshd restart.
- Fresh SSH worked after the daemon restart.
- A detached 10-second visual standby/wake cycle completed. During standby, a fresh LAN SSH connection succeeded in 0.73 seconds including an HTTPS request; systemd reported `running`; archlinux.org returned HTTP 200 in 0.58 seconds.
- After wake, both monitors were enabled. The portrait screen reported 3840×2160, approximately 60 Hz, XRGB8888, SDR, and VRR disabled. These software readings cannot establish absence of visible flicker; the user reported continued blinking.
- Additional checks identified Tailscale SSH demanding browser reauthorization. After switching to OpenSSH, `ssh tensor`, LAN SSH, and Tailscale SSH using the trusted LAN host-key alias all succeeded in approximately 0.16–0.17 seconds.
- Internet HTTPS still returned HTTP 200 in 0.55 seconds after wake.
- Hyprland configuration reload returned no configuration errors.
- No further automatic display test loop is running. Repeated mode cycling was removed after the user's blinking report.

## Findings and remaining work

The previous boot's root manager reload began at 13:06:07, failed to start its generator sandbox after 90 seconds, then abandoned the bulk automount. SSH's debug trace stalled during local-user identity/group processing. The exact generator failure cause remains unproven; the targeted sshd setting removes one observed dependency but does not repair a future root-manager freeze or eliminate PAM's session-manager dependency.

The separate `ssh tensor` timeout was reproduced as a Tailscale SSH authorization wait and has been resolved for the existing key-based access.

The graphics change requires logout/login (or a user-initiated reboot) and a subsequent visual standby/wake check with physical confirmation. Do not mark the flicker fixed before that check. Do not kill the active desktop while the user may have unsaved work.

The `hibernate` command remains visual standby only. System suspend and real hibernation remain disabled so RAM, processes, network, and SSH stay available. The 30-minute inactivity trigger and keyboard resume behavior are preserved.

## Backups and rollback

See `ROLLBACK.md`. Original user files are under `~/.local/state/standby-stability-20261014/before/`; root backups are under `/var/lib/tensor-standby-stability-20261014/`.

## Primary references

- [Aquamarine environment options](https://github.com/hyprwm/aquamarine/blob/main/docs/env.md): documented `AQ_MGPU_NO_EXPLICIT` behavior.
- [Aquamarine DRM source](https://github.com/hyprwm/aquamarine/blob/main/src/backend/drm/DRM.cpp): the option is cached while processing multi-GPU buffers.
- [systemd userdb source](https://github.com/systemd/systemd/blob/main/src/shared/userdb.c): `SYSTEMD_BYPASS_USERDB` disables userdb IPC.
