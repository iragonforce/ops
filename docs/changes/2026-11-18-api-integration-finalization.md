# Nexus API integration finalization

Date: 2026-11-18
Host: nexus

## Canonical identities

- `adguard-summary`: container `adguard-summary`; legacy DNS alias `homelab-adguard-summary`
- `npm-summary`: container `npm-summary`; legacy DNS alias `homelab-npm-summary`
- `stepca-summary`: container `stepca-summary`; legacy DNS alias `homelab-stepca-summary`
- `tensor-connector`: container `tensor-ollama-read`; legacy DNS alias `homelab-tensor-ollama-read`
- `observability`: container `observability`; legacy alias `homelab-observability`

## Compose

All five integrations use a single canonical
`/srv/containers/compose/<project>/compose.yaml`.
The four temporary rename overlays were merged and deleted.
Original working directories and compatibility symlinks remain.

## Kong upstreams

- `homelab-adguard-summary` -> `adguard-summary`
- `homelab-npm-summary` -> `npm-summary`
- `homelab-stepca-summary` -> `stepca-summary`
- `homelab-tensor-ollama-read` -> `tensor-ollama-read`
- `homelab-observability` -> `observability`

The live Kong configuration at
`/opt/homelab-api/config/kong.json` was updated
and reloaded without recreating the gateway.

The Kong JSON is not committed because its contents
require a separate credential/security review.

## Glance

Five service records were updated to canonical
container identifiers.

## Validation

- Four Compose models were preserved exactly.
- Four services were recreated using one Compose file each.
- All five integration health endpoints returned HTTP 200.
- Images, mounts, environments, and restart policies
  were preserved.
- Legacy and canonical DNS names resolved.
- Ten Kong API routes were probed before and after reload.

## Backup

`/var/backups/homelab/api-finalize-jsvmqwst`

The private backup contains the original Compose files,
Kong configuration, and Glance registry.
It must not be committed without credential review.

## Remaining

Register these five source-to-installed mappings in
`inventory/deployments.json` after inspecting its schema.
Remove compatibility aliases only after all consumers
have been updated and verified.
