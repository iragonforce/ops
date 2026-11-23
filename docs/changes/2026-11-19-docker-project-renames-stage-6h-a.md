# Nexus Docker project renames — Stage 6H-A

Date: 2026-11-19

## Project changes

- `nexus-portainer` -> `portainer`

## Validation

- Compose definitions equivalent except for project names.
- Portainer external networks retained without renaming.
- Existing container names, mounts, devices and images retained.
- Health, HTTP baselines, DNS and runtime configuration verified.
- Application data backed up with containers stopped.
- Private rollback backup: `/var/backups/homelab/docker-stage6h-a-xxn3vs2r`.
- No network or application-data deletion.
