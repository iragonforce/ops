# Nexus Docker project renames — Stage 6I-A

Date: 2026-11-19

## Project changes

- `nexus-n8n` -> `n8n`

## Validation

- Compose definitions equivalent except for project names.
- Five static IPv4 assignments and external networks preserved.
- Existing container names, mounts, devices and images retained.
- Health, HTTP baselines, DNS and runtime configuration verified.
- Application data backed up with containers stopped.
- Private rollback backup: `/var/backups/homelab/docker-stage6i-a-sm5h5uia`.
- No network or application-data deletion.
