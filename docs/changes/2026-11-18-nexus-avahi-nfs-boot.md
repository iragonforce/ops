# Nexus Bonjour and NFS persistence

Date: 2026-11-18
Host: nexus

## Changes

Avahi is restricted to enp6s0 (LAN).

The existing SMB advertisement remains NEXUS
on DNS-SD service _smb._tcp, TCP port 445.

Docker bridges and unrelated interfaces are excluded.

NFS uses WantsMountsFor=/srv/nfs/t7, preserving
availability of the remaining exports when T7 is absent.

Samba and NFS export definitions were not modified.

## Verification

- NFS, Samba, Avahi and storage-shares active
- Services enabled at boot
- T7 bind mount dependency verified
- Avahi service advertised on the physical LAN interface
- Docker advertisements excluded

Actual reboot and remote Finder discovery are pending.

## Rollback

Backup directory:
`/var/backups/homelab/nexus-avahi-nfs.2rCYecPm`

Restore Avahi configuration and remove the NFS drop-in.
Reload systemd and restart Avahi.
