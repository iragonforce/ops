# Syncthing and Hermes fast-pool migration

Date: 2026-11-11
Host: nexus

## Objective

Consolidate five Syncthing data directories under `/mnt/fast`,
retire the three legacy homelab synchronization shares without
deleting local files, and maintain Hermes access to the new data.

## Changes

- Merged unique files into the five destination directories.
- Preserved conflicting Git and macOS metadata without overwriting.
- Recreated Syncthing using project `nexus-syncthing`.
- Updated five Syncthing bind-mount sources to `/mnt/fast`.
- Removed the three legacy homelab Syncthing definitions.
- Recreated Hermes using project `hermes`, retaining its
  parent storage mount and adding five targeted bind mounts.
- Preserved original data directories, profiles and Kanban state.

## Verification

- Syncthing container healthy; six folders idle, zero pending
  files, deletions and reported errors.
- Tensor and Qubit connected to Nexus at verification.
- Hermes container healthy; all five mounts verified.
- UID 10000 could access all five directories.
- Kanban board directories, profile instructions and ops
  workspace remained accessible.
- No independent post-recreation Kanban task execution test.

## Git revisions

- `3cc0443`: Syncthing fast-pool mounts.
- `409eee8`: Hermes fast-pool overlays.

## Recovery

- Original directories remain under `/srv/containers/data`.
- Syncthing Compose backup:
  `/var/backups/homelab/syncthing-compose-before-fast-20261111T171232Z.yaml`
- Hermes Compose backup:
  `/var/backups/homelab/hermes-compose-before-fast-overlays.yaml`
- ZFS pre-merge snapshots were created with timestamp
  `20261111T170342Z` on `fast` and `fast/debian-live`.
- Restore the appropriate Compose file with its original
  project name and verify application state before recovery.
- Do not blindly restore snapshots over newer live data.

## Outstanding

- Verify native Hermes Kanban functionality.
- Reconcile and inventory old storage consumers.
- Refresh generated infrastructure inventories.
- Consolidate shared agent configuration through Git.
- Preserve unrelated Checkmk backup and historical state.
