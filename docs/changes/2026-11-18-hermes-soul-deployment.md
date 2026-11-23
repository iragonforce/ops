# Hermes coordinator instructions — 2026-11-18

Host: nexus
Project: iragonforce/ops
Component: Hermes Agent v0.21.6

## Objective

Separate Hermes' coordinator identity from infrastructure operating
policy, remove obsolete orchestration instructions, and place the
active SOUL.md under guarded Git-managed deployment.

## Source and destination

Source:
hosts/nexus/files/srv/containers/data/hermes/data/SOUL.md

Host target:
/srv/containers/data/hermes/data/SOUL.md

Container target:
/opt/data/SOUL.md

Global AGENTS.md policy changes were committed separately from
the runtime deployment. Deployment of other AGENTS.md copies is
not established by this change.

## Changes

- Replaced the previous SOUL.md with the approved concise
  Infrastructure Coordinator identity.
- Retained operating policy in the global AGENTS.md.
- Registered SOUL.md in inventory/deployments.json.
- Corrected inventory permissions to 0600.
- Deployed using the existing guarded installer.

## Verification

- Preflight: one pending deployment, zero conflicts.
- Installer applied exactly one target.
- Original SHA-256:
  def64b61cf1ad451a20cc46d0e02e8c1ab0a1496c7713973a85bbc0f3470866c
- Deployed SHA-256:
  e0521c4b62d3b6793697124b7cba259d0ea162706c825af183a9b86150c1c709
- Ownership: UID/GID 10000:10000.
- File permissions: 0600.
- Hermes container: running; restart count 0.

## Backup and rollback

Protected local original:
/var/backups/homelab/hermes/SOUL.md.baseline-def64b61cf1a

Private backup repository: iragonforce/backup
Branch: hermes-soul-2026-11-18
Backup commit: d73b7b8ef9f5ca26512bce1dd36269c5f508b8e1

Before rollback, check that the live file still matches the
recorded deployed digest. Restore only the original SOUL.md,
preserving ownership 10000:10000 and mode 0600. Verify the
original checksum afterward.

Do not restore or modify Hermes databases, sessions,
authentication, memory, or unrelated configuration.

## Source history and remaining verification

Coordinator policy commit: 2cc525e
Permission correction commit: 990f468

Fresh-session instruction loading is not yet verified.
Other AGENTS.md runtime copies require a separate deployment audit.
