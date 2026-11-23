# Nexus Compose consolidation — Batch B

Date: 2026-11-23
Host: nexus

## Scope

Canonical Git sources for Receipt Wrangler, Photon,
and CraftControl.

## Receipt Wrangler

Preserved the existing application data paths:
- /opt/receipt-wrangler/data
- /opt/receipt-wrangler/logs

The existing environment file remains outside Git:
- /opt/receipt-wrangler/.env

Canonical management requires explicitly passing:
--env-file /opt/receipt-wrangler/.env

This is required for Compose variable interpolation;
it does not require introducing service-level env_file
declarations or copying credentials.

## Photon

Preserved the existing build context, data paths,
external secret files, and proxy-backend static
address 172.16.11.200.

## CraftControl

Preserved the existing two-service production
Compose definition.

Alternative docker-compose.yml files remain in
the deployed directory for separate classification.

## Verification

All three original and candidate effective Compose
models were verified identical before installation.

No Docker containers were recreated.

## Recovery

Pre-change deployed files are preserved under
/var/backups/homelab/compose-batch-b-*/

Historical canonical configurations are also
preserved in the Git archive for this batch.

Original external application data and secrets
were not moved.

## Follow-up

- Deploy the corrected Glance Obsidian catalog.
- Audit external legacy Compose copies.
- Finalize API Gateway and Media management paths.
- Verify full fleet canonical Git coverage.
