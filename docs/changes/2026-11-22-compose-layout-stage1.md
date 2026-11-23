# Compose directory consolidation — stage 1

Date: 2026-11-22

## Objective

Standardize Nexus Compose deployment directories under
`/srv/containers/compose/<project>/`, with corresponding
Git sources under
`hosts/nexus/files/srv/containers/compose/<project>/`.

## Stage 1

Standardized and validated these four projects:

- api-gateway
- baikal
- netbootxyz
- obsidian

Seven Compose files were copied.

The effective Compose models were verified equivalent to the
original deployments. Kong's relative configuration bind mount
was converted to its existing absolute host path in the
standardized copy.

## Important transition boundary

This stage only creates standardized configuration copies.

Existing containers still retain their original Compose
working-directory and configuration-file labels.

The historical configuration files remain preserved and
Git-tracked until management-path references and the effects
of future Compose reconciliation have been checked.

Do not assume that running `docker compose up -d` from the
new directory is guaranteed to avoid container recreation.

No container recreation, restart, network reassignment,
mount migration or persistent-data relocation is authorized
by this stage.

## Remaining work

- Audit remaining projects and relative path dependencies.
- Reconcile systemd, scripts and deployment references.
- Establish final authoritative Compose sources.
- Verify future Compose reconciliation behavior.
- Retire historical source copies only when safe.
