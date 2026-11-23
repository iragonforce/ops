# Nexus SMB share cleanup and Bonjour

Date: 2026-11-18
Host: nexus

## Changes

Removed Samba share definitions:

- Bulk Shared Files
- Fast Shared Files
- Bulk Storage - 1 TB Limit

Retained:

- bulk -> /mnt/bulk
- fast -> /mnt/fast
- T7 -> /mnt/t7

No underlying storage directories or files were deleted.

Installed Avahi and registered the SMB DNS-SD service
`_smb._tcp` on TCP port 445, advertised as NEXUS.

The existing Samba guest configuration, NFS configuration,
SSH configuration and access-guard firewall are preserved.

## Source

- hosts/nexus/files/etc/samba/smb.conf
- hosts/nexus/files/etc/avahi/services/smb.service
- inventory/deployments.json

## Verification

Samba configuration validated using testparm.
All three remaining shares verified in testparm.
Avahi service started and enabled.

External Finder discovery must be verified from Qubit.
mDNS firewall ingress remains subject to verification.

## Rollback

Configuration backup: `/var/backups/homelab/smb-share-cleanup.M6nVXrtA/smb.conf`

Restore the backed-up Samba configuration, validate using
testparm, and reload smbd.

Git history preserves the prior six-share configuration.
