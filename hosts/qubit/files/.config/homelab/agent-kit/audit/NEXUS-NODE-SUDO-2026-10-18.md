# Nexus node administration

2026-10-18, America/Toronto. Explicitly requested and authorized by the user.

## Before

Nexus host account `node` is UID/GID 1001, home `/home/node`, shell `/bin/bash`. It had two narrow passwordless Docker exec rules for Hermes and no general sudo or direct Docker group access. Qubit's existing `nexus` alias uses `iragonforce@192.168.1.2`; another agent's existing alias was reported to use node. No SSH alias, authorized key or credential was changed.

## Change

Installed `/etc/sudoers.d/90-node-admin`, root:root mode 0440:

```sudoers
node ALL=(ALL:ALL) NOPASSWD: ALL
```

This grants full host administration to node, including Docker and nginx/Authentik container administration through sudo. Direct unprivileged Docker socket permissions remain unchanged; use `sudo -n docker ...`. Existing restricted Hermes rules were preserved.

## Checks

- Existing and resulting complete sudoers configuration passed visudo validation.
- Executed `sudo -n id -u` as host account node: returned 0.
- Executed `sudo -n docker info --format '{{.ServerVersion}}'` as node: returned Docker 29.9.0.
- No services restarted, passwords changed, SSH sessions replaced or formal tests run. Existing remote node authentication was reported by the user; checks exercised node's host privileges directly.

## Rollback

Before-state and instructions: `/var/backups/homelab/node-sudo-20261018`. Remove the new drop-in when `drop-in-was-absent` exists; otherwise restore the saved prior file with root:root ownership and mode 0440. Run `visudo -cf /etc/sudoers` afterward. Existing narrower rules are separate and remain intact.
