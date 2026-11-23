# Nexus NFSv3 child-export traversal repair

Date: 2026-11-12
Hosts: nexus (server), tensor (client)

## Problem

Tensor mounted 192.168.1.2:/srv/nfs/fast using NFSv3.
Documents and Downloads appeared empty because their paths
were separate filesystems beneath the parent export.

Direct child NFS mounts displayed the expected files.

## Change

Added nohide only for Tensor (192.168.1.3) on:

- /srv/nfs/fast/documents
- /srv/nfs/fast/downloads

All other client rules and export permissions were preserved.
Applied using exportfs -ra without restarting NFS.

## Verification

- Direct child mounts exposed existing data and .stfolder.
- A fresh parent NFSv3 mount traversed both child filesystems.
- Tensor's permanent /home/nexus/fast mount was refreshed.
- Documents: 20 entries, marker present.
- Downloads: 10 entries, marker present.
- Systemd: running, zero failed units.

## Recovery

Original export configuration:
/var/backups/homelab/nexus-exports-before-nohide-20261112-192653.conf

Restore the file to /etc/exports.d/nexus.exports and
run exportfs -ra if rollback is required.

Syncthing folder recovery remains separate.
