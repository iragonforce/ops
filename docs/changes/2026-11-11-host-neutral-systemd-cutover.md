# Nexus host-neutral systemd migration — 2026-11-11

## Purpose

Replace unnecessary `nexus-` prefixes in host-local systemd units,
commands, supporting libraries, and manual pages.

The Nexus hostname and legitimate host-specific configuration remain
unchanged.

## Git history

- Refactor: `2a7d4e9`
- Merge into `consolidate`: `82e2a29`

## Completed

- Installed 21 renamed systemd units, 14 executables, and one library.
- Migrated Docker, NFS, Samba, Tensor-control, and Compose dependencies.
- Transferred 27 boot enablements, including 17 Compose instances.
- Transferred five periodic timers.
- Activated and verified ZFS, VLAN, host-access, NFS firewall, and
  storage-shares replacement units.
- Archived and retired 37 legacy files.
- Verified 41 deployed files against commit `2a7d4e9`.
- Preserved Docker and Tailscale process continuity throughout cutover.

## Fstab dependency correction

Two `/etc/fstab` entries initially retained references to the removed
`nexus-zfs-unlock.service`, causing four unrelated timers to fail.

Affected mounts:

- `/mnt/fast/docker-runtime/containerd`
- `/mnt/fast/docker-runtime/docker`

Both entries were corrected to use:

- `x-systemd.requires=zfs-unlock.service`
- `x-systemd.after=zfs-unlock.service`

Systemd mount units were regenerated and verified without remounting
storage or restarting Docker.

The complete `/etc/fstab` is not tracked in this repository. Future
deployment or reconstruction must preserve these corrected dependencies.

## Timer recovery

Recovered:

- `homelab-adguard-snapshot.timer`
- `homelab-npm-snapshot.timer`
- `homelab-stepca-snapshot.timer`
- `pia-media-recovery.timer`

All four became active with successful results. The latest systemd
check reported zero failed units.

## Rollback assets

- `/root/backups/host-neutral-legacy-2a7d4e9.tar`
- `/root/backups/host-neutral-retired-2a7d4e9/`
- `/root/backups/host-neutral-boot-links-2a7d4e9.tsv`
- `/root/backups/host-neutral-timers-2a7d4e9.tsv`
- `/root/backups/host-neutral-deps-2a7d4e9/`
- `/root/backups/fstab-before-zfs-unit-rename-2a7d4e9`

## Outstanding operational validation

- Confirm subsequent scheduled executions of the recovered timers.
- Investigate the unrelated Samsung T7 UUID warning before reboot.
- Verify startup ordering during a separately planned controlled reboot.

No reboot or Docker restart was performed during this migration.
