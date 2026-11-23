# Nexus Docker project renames — Stage 6F

Date: 2026-11-19

## Project changes

- `nexus-makersvault` -> `makersvault`
- `nexus-homelable` -> `homelable`

## Validation

- Compose definitions equivalent except for project names.
- External networks retained, including homelable_homelable_net.
- Existing container names, mounts, devices and images retained.
- Health, HTTP baselines, DNS and runtime configuration verified.
- Application data backed up with containers stopped.
- Private rollback backup: `/var/backups/homelab/docker-stage6f-fq4odc01`.
- No network or application-data deletion.

Historical inventory digest for `/srv/containers/compose/makersvault/compose.yaml`:
- Recorded: `0b85f54afc6effab87f06b822babcfb141b486d4d44ff356366a37cb7b692ca0`
- Verified Git/live: `77c72d30ca487b71a5688660720d37f690bdecb89c7571796aa723f7c43d116b`
