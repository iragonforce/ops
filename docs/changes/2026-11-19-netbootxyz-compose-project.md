# Netbootxyz Compose project simplification

Date: 2026-11-19
Host: nexus

- Previous project: `netbootxyz-netboot`
- New project: `netbootxyz`
- Container name retained: `netbootxyz-netboot`
- Compose directory retained unchanged
- Four bind mounts and external networks preserved
- Compose model checked for equivalence
- Docker image, environment and health verified
- Glance and deployment inventory synchronized

Private rollback configuration: `/var/backups/homelab/netbootxyz-project-82a_t4e8`

Restore the original Compose definition and recreate
the container using project `netbootxyz-netboot` if needed.
Do not remove persistent data, Docker networks, or volumes.
