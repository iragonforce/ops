# Nexus legacy Compose Git source retirement

Date: 2026-11-22
Host: nexus
Branch: consolidate

## Purpose

Remove three redundant historical Compose sources:

- baikal-baikal-1 -> baikal
- netbootxyz-netboot -> netbootxyz
- obsidian-nexus -> obsidian

## Canonical configuration

Git:
hosts/nexus/files/srv/containers/compose/<project>/compose.yaml

Deployment:
/srv/containers/compose/<project>/compose.yaml

All three canonical configurations were independently
verified against their historical Git sources and deployed files.

## Preservation

Six unique historical configurations were archived
in commit db099a6.

Archive:
docs/archive/nexus-compose-recovery/2026-11-22/

The original deployed directories were moved to:

/var/backups/homelab/compose-retirement-29kPfGWq/

The inventory was corrected in commit cf37213.

## Operational impact

This change removes only obsolete repository sources.

No running Docker container, volume, network, mount,
or authentication configuration was modified.

Existing Docker Compose labels may continue referencing
historical paths until normal container recreation.

## Recovery

The removed sources remain recoverable through the
parent Git commit.

The retired deployment directories remain recoverable
from the protected filesystem rollback directory.

## Remaining work

- Correct the obsolete Glance Obsidian container reference.
- Consolidate remaining historical Compose locations.
- Review media, photon, craftcontrol, and api-gateway.
- Verify final canonical configuration coverage.
