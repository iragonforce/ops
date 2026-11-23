# Hermes restricted restart pilot — 2026-11-20

- Authorized SSH command: `restart npm-summary`.
- Retained `health` and `containers` commands.
- Docker socket remains inaccessible inside Hermes.
- Sudoers restricts the operation to one exact Docker command.
- No container restart occurred during installation.
- Backup: `/var/backups/homelab/hermes/restart-pilot-20261120T002114`.
- Rollback: restore both backed-up files to their original
  locations, preserving ownership and permissions.
- The media Compose project remains excluded.
