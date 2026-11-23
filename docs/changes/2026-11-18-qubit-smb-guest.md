# Qubit — Nexus SMB guest automounts

Date: 2026-11-18
Host: qubit
Protocol: SMB through native macOS autofs

## Configuration

Git source: `hosts/qubit/files/etc/auto_blinkwired_smb`
Installed map: `/etc/auto_blinkwired_smb`

Required `/etc/auto_master` entry:

```text
/- /etc/auto_blinkwired_smb
```

## Mounts

- `/Users/nexus-smb/fast` -> `//guest:@nexus/fast`
- `/Users/nexus-smb/bulk` -> `//guest:@nexus/bulk`
- `/Users/nexus-smb/t7` -> `//guest:@nexus/T7`

Mount options: `smbfs,nosuid,nodev,noowners`.
No SMB passwords or credential files are required.

## Verified behavior

- All three SMB mounts activated successfully.
- Directory access succeeded.
- Native autofs triggers were verified.
- Existing NFS mounts remained operational.

## Pending acceptance

- Reboot persistence.
- Remote access through Tailscale.
- Review of Tailscale TCP 445 authorization.

## Rollback

Restore the previous autofs configuration after
ensuring the SMB mounts are no longer in use.

Original backup:
`/private/var/tmp/qubit-smb-autofs.W9yqnX`

Additional recovery backup:
`/private/var/tmp/qubit-smb-recovery.HsPMpdxQ`
