# Nexus historical Docker Compose recovery configurations

Archived: 2026-11-22
Repository: iragonforce/ops
Branch at preservation: consolidate

## Purpose

These six files are original, byte-for-byte historical
Compose configurations from three obsolete deployment
directories.

They were preserved before filesystem consolidation
because their exact Git blobs were absent from all
reachable repository history.

## Source directories

- /srv/containers/compose/baikal-baikal-1/
- /srv/containers/compose/netbootxyz-netboot/
- /srv/containers/compose/obsidian-nexus/

## Historical changes

The backups predate portions of the container naming,
restart policy, and resource-limit recovery work.

The Obsidian backups additionally contain historical
user/group and volume configuration differences.

These files are archival evidence, not active deployment
configurations. Do not deploy them without reviewing their
historical semantics and environment dependencies.

## Current canonical deployment directories

- /srv/containers/compose/baikal/
- /srv/containers/compose/netbootxyz/
- /srv/containers/compose/obsidian/

## Integrity

SHA256SUMS records the exact archived file contents.

Historical Docker Compose labels may still reference the
original directories until containers are naturally
recreated or their management metadata is reconciled.
