# API Gateway Compose source retirement

Date: 2026-11-23
Host: nexus
Project: api-gateway

## Canonical source

The four active Compose definitions are tracked under:

hosts/nexus/files/srv/containers/compose/api-gateway/

Deployed source:

/srv/containers/compose/api-gateway/

## Legacy compatibility

The following paths under /opt/homelab-api are now
symlinks to their matching canonical Compose files:

- compose.yml
- compose.override.yml
- compose.qbittorrent-auth.yml
- compose.api-expansion.yml

Docker's existing Compose labels still reference the
original paths. These paths therefore remain usable.

The original inactive compose.photon-auth.yml is retained
as an ordinary file and is not part of the active model.

## Verification

The original, canonical, and symlink-based Compose
definitions rendered identical structural models.

Normal interpolation could not be validated because
the required deployment environment inputs were absent.

The environment-dependent runtime configuration has not
been reconstructed or changed.

All 78 Docker containers remained running with unchanged
IDs, start times, and status during the migration.

No Docker restart, recreation, or deployment occurred.

## Backups

Original Compose files, including the inactive overlay:

/var/backups/homelab/api-gateway-compose-retirement-yfalb0i9

The previous tracked Git sources remain recoverable from:

f829dad

## Rollback

To restore an original Compose file:

1. Copy the corresponding file from the backup directory
   to a temporary file beside its original path.
2. Preserve the backed-up ownership and permissions.
3. Atomically rename the temporary file over the symlink.
4. Compare the restored file with the backup.

To recover the former Git source records, restore only
the affected paths from commit f829dad and commit that
targeted restoration.

Do not delete canonical files, the inactive overlay,
application data, external secrets, or Docker state.

## Outstanding

Fully interpolated Compose equivalence remains unverified.
Any future API Gateway recreation must first establish
the required environment and secrets.
