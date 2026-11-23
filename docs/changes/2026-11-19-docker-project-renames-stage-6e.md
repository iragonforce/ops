# Nexus Docker project renames — Stage 6E

Date: 2026-11-19

## Renames

- `nexus-cups` -> `cups`; container `cups` retained
- `nexus-baikal-baikal-1` -> `baikal`; container `baikal-baikal-1` retained
- `nexus-vikunja` -> `vikunja`; container `vikunja` retained

## Safety and recovery

- Compose models verified equivalent apart from project identity.
- Persistent application data backed up with containers stopped.
- Exact image, environment, mount, device and network checks.
- Original containers retained until successful Git push.
- Private configuration and data backup: `/var/backups/homelab/docker-stage6e-0rwlxrdn`.
- No named Docker volumes or project networks removed.
