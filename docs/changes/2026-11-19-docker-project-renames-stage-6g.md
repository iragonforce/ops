# Nexus Docker project renames — Stage 6G

Date: 2026-11-19

## Project changes

- `nexus-checkmk` -> `checkmk`
- `nexus-syncthing` -> `syncthing`
- `nexus-telegram` -> `telegram`

## Validation

- Compose definitions equivalent except for project names.
- Existing external networks retained without renaming.
- Existing container names, mounts, devices and images retained.
- Health, HTTP baselines, DNS and runtime configuration verified.
- Application data backed up with containers stopped.
- Private rollback backup: `/var/backups/homelab/docker-stage6g-rb4ay4nj`.
- No network or application-data deletion.

Historical inventory digest for `/srv/containers/compose/syncthing/compose.yaml`:
- Recorded: `baf3b35bb6c01647606d6c052e02e4949cac6920083739937bc1cfe160780d1f`
- Verified Git/live: `738c1c9bcb8b1747c0f42ce13dbfbf06ade6cc48d6d45efe1bbac3e921a073c5`
