# Rollback — Tensor standby stability

Use a working SSH connection or the local console. Keep it open while changing SSH.

## SSH

1. Remove `/etc/ssh/sshd_config.d/00-local-ssh.conf` and `/etc/systemd/system/sshd.service.d/30-local-userdb.conf`.
2. Run `sudo sshd -t` before restarting anything. If it fails, restore the root backup or correct the configuration from the existing connection.
3. Run `sudo systemctl daemon-reload` and `sudo systemctl restart sshd` only while the system manager is responsive. Verify a second SSH login before closing the original connection.
4. To restore Tailscale's browser-authorized SSH handler, run `sudo tailscale set --ssh=true`. It can require fresh browser authorization. This is independent of restoring OpenSSH configuration.

Root copies of the original sshd configuration and NSS file are stored in `/var/lib/tensor-standby-stability-20261014/`. NSS and PAM were not edited.

## Desktop helper and graphics

Restore these files from `~/.local/state/standby-stability-20261014/before/`:

- `tensor-desktop.py` → `~/.local/share/tensor-control/tensor-desktop.py`
- `visual-standby.py` → `~/.local/share/tensor-control/visual-standby.py`
- `hyprland.lua` → `~/.config/hypr/hyprland.lua`

The saved graphics file preserves all prior monitor, window, and workspace rules. Restore only the `AQ_MGPU_NO_EXPLICIT` line if other settings have changed since this backup. Log out/in after removing the environment option: the running backend caches it.

Restoring the original helpers reinstates the prior automatic 30/60 Hz display resets, which did not eliminate recurrent flicker. Prefer retaining bounded timeouts if rolling back only the graphics option.

No kernel parameters, GPU drivers, real sleep policy, global NSS/PAM configuration, keys, passwords, fan curves, or network addressing were modified by this repair.
