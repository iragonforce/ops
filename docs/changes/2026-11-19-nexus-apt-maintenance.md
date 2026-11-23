# Nexus daily APT maintenance

Date: 2026-11-19
Host: nexus, Debian 13

## Configuration
- Service: apt-maintenance.service
- Timer: apt-maintenance.timer
- Schedule: 02:00 America/Toronto
- Operations: update, upgrade --with-new-pkgs, autoremove, autoclean
- Automatic reboot: disabled
- Configuration files: hosts/nexus/files/etc/systemd/system/
- Logs: journalctl -u apt-maintenance.service
- Missed runs: not executed automatically at boot

## Previous configuration
- apt-daily.timer: enabled
- apt-daily-upgrade.timer: enabled
- unattended-upgrades: not installed
- APT::Periodic: no configured values

## Rollback
Disable apt-maintenance.timer.
Re-enable apt-daily.timer and apt-daily-upgrade.timer.
Remove the two custom units from /etc/systemd/system/.
Run systemctl daemon-reload.

This rolls back scheduling, not package upgrades already applied.
