# Storage and TrueNAS → Debian migration

## Historical baseline

TrueNAS SCALE 25.10.1 was replaced by Debian 13. The pre-install archive is `/mnt/bulk/debian-migration`; `PLAN.md` and `post-install/` contain recovery and subsequent configuration records. The initial statement that no changes had been made applied only to the first inspection phase; many later changes were completed.

| Disk | Role | Verified identity during restoration |
|---|---|---|
| SATA SSD, approximately 238.5 GB | Debian boot/engine storage; formerly boot-pool | Verify current serial/partition map before any disk operation |
| HDD, approximately 18.2 TB | bulk | Serial ZYD0L4FN; pool GUID 2119212528721849216 |
| NVMe, approximately 2 TB | fast | Serial S7U6NJ0Y233332T; pool GUID 12978747864126690130 |

Only bulk and fast were imported following initial read-only inspection. The old boot pool was not imported. Pools were not recreated and pool features were not upgraded. Debian's recorded ZFS version was 2.3.9; verify before compatibility work.

Archive records report 106 received boot datasets / 173 snapshots and 33 received fast datasets / 95 snapshots. Fast preinstall snapshot GUID coverage was checked. A later source snapshot absent from the archive was created after the archive. The completed Oct 8 bulk scrub reported no repairs/errors. This is historical evidence, not a new full archive verification.

## Current layout and rollback sources

- Shared bulk files: `/mnt/bulk/data/{media,downloads,documents,projects}` where populated; retain unclassified/legacy paths and migration manifests.
- Backups: `/mnt/bulk/backups/{host,services,databases}` and preserved migration archive.
- Maintained Compose: `/srv/containers/compose/<stack>`.
- Active service data: `/srv/containers/data`, backed by clone `fast/debian-live`.
- Local builds: `/srv/containers/builds`, backed by `fast/debian-builds`.
- Private environment files: `/etc/nexus/secrets/<stack>`.
- Original `/mnt/fast` and received reference datasets are recovery/reference sources; distinguish them from active clones.
- Source snapshots `bulk@nexus-before-restore-20261011` and `fast@nexus-before-restore-20261011` were held with `nexus-restoration`.
- Normal boot imports use `/etc/zfs/zpool.cache` for bulk/fast and `nexus-zfs-unlock.service`. Bulk key path is `/etc/zfs/keys/bulk.key`; values must stay private.

Do not recursively chmod/chown entire pools. UID 1000 access was granted only to selected migrated/shared trees. The initial ACL dump was partial; use held snapshots and later metadata records rather than treating that dump as complete rollback.

Docker engine/image storage remains on the boot SSD's ext4 storage; application data/builds reside on fast. Database major upgrades used copies or staged upgrades. Reverting an image alone after a schema upgrade is insufficient.

## NFS and SMB

The user chose shared files on both drives, not whole pool roots or live databases. Dedicated exports under `/srv/nfs` map allowed clients with `all_squash,anonuid=1000,anongid=1000`, synchronous read/write access. Live export definitions are captured in `11-live-nexus-inventory.json`.

Qubit uses Tailscale NFS mounts, macOS static automount support and a recovery daemon; installations required local macOS administrator approval, which the user completed. Tensor uses automounts under `/home/nexus/{bulk,fast}` and `/home/qubit`; a recovery timer handles Nexus mounts. Do not casually change hard NFS mounts to soft, expose application databases, or replace macOS maps without checking current state.

Windows-compatible SMB and a clearly labelled 1 TB limited bulk share were configured according to later records. Verify the actual share/dataset quota before promising available capacity; do not apply a quota to the entire bulk pool.

Live handoff capture: bulk and fast were ONLINE; `zpool status -x` is in the inventory. No full checksum pass or new scrub was run for this pack.

## 2026-10-15 — Verified NFS routing and remaining Qubit mount

- Tensor `/home/qubit` → `100.103.67.56:/Users/iragonforce`, Tailscale; normal-user read/write/rename/delete passed.
- Tensor `/home/nexus/{fast,bulk}` → `192.168.1.2:/srv/nfs/{fast,bulk}`, LAN; normal-user read/write/rename/delete passed on fast and bulk/documents. Updated fstab and existing recovery helper/service/order; existing timer remains active. Backup: `/var/lib/homelab-nfs-20261015-211919/` on Tensor. Restore saved files to their original paths, daemon-reload and ordinarily restart idle mounts plus the existing timer to roll back.
- Qubit `/Users/nexus/{fast,bulk}` retains `100.96.255.81:/srv/nfs/{fast,bulk}`, Tailscale; the same file-operation checks passed on fast and bulk/documents.
- Qubit `/Users/tensor` remains pending: legacy `/etc/auto_nfs` is not referenced in `/etc/auto_master`. Prepared installer `~/.local/state/nfs-share-20261015/apply-qubit-nfs.sh` activates a hard Tailscale direct map to Tensor `/home/iragonforce`. macOS administrator authentication failed (-60007); both live maps are unchanged. User must authorize locally, then mount and file operations need verification. The installer saves original maps in `/var/db/homelab-nfs-<timestamp>/` before changes.
- User chose home-directory sharing instead of exposing Tensor's arch-sys/arch-data devices. Nexus remains shared-files-only. No restart/off-site recovery was exercised; full kit sync remains pending.
