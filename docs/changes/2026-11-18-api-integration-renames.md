# Nexus API integration naming migration

Date: 2026-11-18
Host: nexus

## Verified migrations

The following Compose projects and containers were renamed:

- `homelab-adguard-summary` -> `adguard-summary` (project `adguard-summary`).
- `homelab-npm-summary` -> `npm-summary` (project `npm-summary`).
- `homelab-stepca-summary` -> `stepca-summary` (project `stepca-summary`).
- `homelab-tensor-ollama-read` -> `tensor-ollama-read` (project `tensor-connector`).
- `homelab-observability` -> `observability` (project `observability`).

## Deployment

Compose source files are under
`/srv/containers/compose/<project>/`.

The original project working directories are retained
because some configurations depend on relative paths.

For four projects, both `compose.yaml` and
`compose.rename.json` must be supplied explicitly.

Example for `adguard-summary`:

```sh
docker compose -p adguard-summary \
  --project-directory /opt/homelab-api/adapters/adguard-summary \
  -f /srv/containers/compose/adguard-summary/compose.yaml \
  -f /srv/containers/compose/adguard-summary/compose.rename.json \
  up -d
```

`observability` uses its single `compose.yaml`.

## Compatibility

- Legacy Docker DNS aliases remain active.
- Kong still uses the legacy upstream names.
- Original Compose locations remain compatibility links.
- Glance and deployment inventory updates are pending.

## Recovery

Original adapter backups:
`/var/backups/homelab/rename-integrations-nncqkfha`.

Original observability backup:
`/var/backups/homelab/rename-observability-fd1h0u1l`.

Restore the original Compose configuration and project
identity before removing a renamed container.
Do not delete Docker networks or persistent storage.

## Validation performed

- New project and container identities verified.
- Original images, mounts, environment and restart policies preserved.
- Adapter HTTP `/healthz` returned 200 for the four integrations.
- Old and new Docker DNS names resolved.
- Kong legacy upstream DNS names remained resolvable.
