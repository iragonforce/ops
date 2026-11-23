# Nexus external Compose source retirement

Date: 2026-11-23
Host: nexus

## Purpose

Eliminate redundant Compose file contents while preserving
compatibility with existing Docker Compose project metadata.

## Compatibility symlinks

- /opt/data/network-alias-dns/compose.yaml
- /opt/receipt-wrangler/compose.yml
- /opt/receipt-wrangler/compose.override.yml
- /mnt/fast/photon/compose.yaml

Each path now resolves to its canonical file under
/srv/containers/compose/<project>/.

Original files are preserved at:

/var/backups/homelab/compose-external-retirement-sapurwp3

All three effective Compose models were confirmed unchanged
before and after the replacement. All 78 running containers
retained their identities, startup times and states.

## Git source retirement

The redundant Git source copies for network-alias-dns and
Photon were retired. Their previous bytes remain recoverable
from commit 917531c and the external backup above.

The canonical sources remain tracked under:

hosts/nexus/files/srv/containers/compose/

## Preserved exceptions

- API Gateway: legacy files and inactive authentication
  overlay retained pending separate environment reconciliation.
- Hermes: deployed quota-test image and variable intentionally
  differ from Git and remain untouched.
- CraftControl: alternate Compose definitions retained pending
  classification.

No Docker services were recreated or restarted.

## Rollback

To restore an original external Compose file, copy its
corresponding file from the backup directory to the
original path using a temporary file and atomic rename,
preserving ownership and permissions.

The canonical configuration files must not be removed
as part of this rollback.
