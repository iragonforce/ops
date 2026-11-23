# Hermes restricted Nexus management — 2026-11-19

## Purpose

Replace Hermes' unrestricted Docker socket access with
a source-restricted SSH management interface.

## Verified

- Nexus management endpoint: 192.168.5.254:22.
- Hermes source: 192.168.5.55.
- Dedicated management account: hermes-mgmt (UID 994).
- Dedicated Ed25519 SSH key: nexus-mgmt.
- SSH restricted by source and user.
- Forced command: /usr/local/libexec/hermes-nexus-mgmt.
- Commands: health, containers.
- Read-only Docker reporting via exact-command sudoers.
- Five end-to-end SSH acceptance tests passed.
- Unauthorized commands and original iragonforce login denied.
- Existing SSH access from Qubit and Tensor preserved.

## Firewall

Authoritative generator:
hosts/nexus/files/usr/local/sbin/access-guard

The new exception must be deployed separately and verified
after an access-guard refresh.

## Outstanding security work

- Remove Hermes' direct Docker socket access.
- Remove unnecessary Docker group membership.
- Restrict writable host storage mounts.
- Preserve approved deployments through a separate
  narrowly authorized management workflow.
- Verify behavior after container recreation.

No existing SSH keys or credentials were rotated.

## Recovery

Verified SSH configuration backup:
/var/backups/homelab/hermes/mgmt-interface.Sfqc6d7f/sshd_config

Restore only if needed, then run sshd -t and reload
ssh.service. Git provides the versioned configuration
and firewall-generator rollback history.

## Staged Docker socket isolation

The Git-managed Hermes Compose configuration removes:

- Direct /var/run/docker.sock bind mount.
- Supplemental Docker group 999.

The change is not yet deployed. The existing Hermes
container and runtime configuration remain unchanged.

Before recreation, preserve the required CLI packages
in a reproducible image and verify rollback.

The existing broad writable storage mounts are not
addressed by this stage.

The restricted SSH management interface currently
supports health and read-only container inspection.
Service modification requires separate authorization.

## Staged storage isolation

Seven unrelated storage mounts are now declared read-only:
the broad /mnt/fast mount, project, screenshots, downloads,
documents, 3d-models and /mnt/bulk/data.

The dedicated /opt/data mount remains writable for Hermes
runtime state, memory, hooks, SSH keys and Git worktrees.

This change is Git-only until deployment acceptance passes.
Host filesystem ownership and ZFS settings are unchanged.

Container root capabilities and remaining credential/
network access paths require a separate security review.
