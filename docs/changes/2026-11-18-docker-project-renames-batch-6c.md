# Nexus Docker project renaming — Stage 6C

Date: 2026-11-18
Host: nexus

## Project renames

- `nexus-bambustudio` → `bambustudio`; container `bambustudio` preserved
- `nexus-minecraft-bedrock` → `minecraft-bedrock`; container `minecraft-bedrock` preserved
- `nexus-netbootxyz-netboot` → `netbootxyz-netboot`; container `netbootxyz-netboot` preserved
- `nexus-webhook-notify` → `webhook-notify`; container `webhook-notify` preserved

## Inventory reconciliation

- Target: `/srv/containers/compose/bambustudio/compose.yaml`
  - Historical baseline: `a67464eb50f38ef3e906c34e47619b5dba6183f54be1e7eff0c39e7a700d4fef`
  - Verified Git/live digest: `85fe4f3727c849ce929ac3b8c1db8aaae870bb2cbe99ccfe0f8223e80159d6f5`

## Verification

- Compose models equivalent except for project identity.
- Original container names preserved.
- Images and environments preserved.
- Bind mounts and external networks preserved.
- Docker device mappings and security settings preserved.
- DNS aliases and health checks verified.
- Reachable HTTP response baselines checked.
- Deployment inventory reconciled.
- Git staging validated before runtime interruption.

## Rollback

Configuration backups are recorded in the deployment output.
Original containers are retained, stopped, until commit
and push have completed successfully.

Do not delete Docker volumes, networks, or application data.
