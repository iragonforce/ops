# Nexus SMB guest deployment

Date: 2026-11-18
Hosts: nexus, tensor, qubit

## Server

Nexus Samba exports three passwordless read/write shares:

- `fast` at `/mnt/fast`
- `bulk` at `/mnt/bulk`
- `T7` at `/mnt/t7`

The three additional named shares retain authentication.

Configuration source:
`hosts/nexus/files/etc/samba/smb.conf`

The existing access-guard firewall restrictions remain in place.

## Tensor

Persistent systemd CIFS automounts:

- `/mnt/nexus-smb/fast`
- `/mnt/nexus-smb/bulk`
- `/mnt/nexus-smb/t7`

Guest authentication uses:

`guest,username=nexus_guest_probe_20261118,vers=3.0`

The username is deliberately nonexistent and triggers
Samba guest mapping. It is not a credential.

The previous SMB password was retained in a protected
rollback backup outside Git.

## Qubit

Native macOS autofs mounts:

- `/Users/nexus-smb/fast`
- `/Users/nexus-smb/bulk`
- `/Users/nexus-smb/t7`

Configuration:
`hosts/qubit/files/etc/auto_blinkwired_smb`

Authentication uses `guest:@nexus` without a password.

Existing NFS mounts remain unchanged.

## Verification

- All three Qubit SMB mounts passed filesystem tests.
- All three Tensor SMB mounts passed guest CIFS testing.
- Nexus Samba is active and serves both clients.
- Client configurations were merged into `consolidate`.

Deployment inventory baselines for client units use the
verified Git source. They are not a fresh runtime audit.

## Remaining security verification

Tailscale Serve forwards TCP 445 to Samba loopback.

Because the shares are writable without authentication,
tailnet policy must restrict SMB access to trusted devices.

Do not consider remote guest SMB secured until this
authorization policy has been verified.

Reboot recovery and remote-network SMB access also remain
separate acceptance checks.

## Rollback

Nexus original Samba configuration:
`/var/backups/homelab/smb-guest-0Ypg8tN9/smb.conf`

Qubit autofs recovery:
`/private/var/tmp/qubit-smb-recovery.HsPMpdxQ`

Tensor rollback files are stored in the root-protected
backup directory reported by its migration script.

Never remove the Samba account database or unrelated
authentication state during rollback.
