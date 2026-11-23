# Nexus Docker project renames — Stage 6H-B

Date: 2026-11-19

## Project changes

- `nexus-monitoring` -> `monitoring`

## Validation

- Compose definitions equivalent except for project names.
- External and host networks preserved; Glance namespace dependency verified.
- Existing container names, mounts, devices and images retained.
- Health, HTTP baselines, DNS and runtime configuration verified.
- Application data backed up with containers stopped.
- Private rollback backup: `/var/backups/homelab/docker-stage6h-b-jnvm4p38`.
- No network or application-data deletion.

Historical inventory digest for `/srv/containers/compose/monitoring/compose.yaml`:
- Recorded: `23c4ba37fec7c3f9da3edd4c7ec5e55b9eeb62d41fe1a909b7037daebe2bdbaa`
- Verified Git/live: `9dfeb855b35f8e4477355c3082884c26cc1ac776da071b9ad5cc0fd6ecf5b6c0`
