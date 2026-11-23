# Nexus Docker project renames — Stage 6B

Date: 2026-11-18
Host: nexus

## Project renames

- `nexus-vert` -> `vert`; container `vert` unchanged
- `nexus-vertd` -> `vertd`; container `vertd` unchanged
- `nexus-stirling-pdf` -> `stirling-pdf`; container `stirling-pdf` unchanged

## Inventory reconciliation

### `/srv/containers/compose/stirling-pdf/compose.yaml`

- Historical baseline: `e413147e77aaaf43026c6c0fe3d66edd36ccb343d32e5ddba684e0b8c5d3c76d`
- Verified previous source: `2cf0ee79634804680b263e04fbfc266a7787374444e22c6558738e9a675281cd`
- New canonical source: `1af62cd0858352598eb8c4840ed7d5cb6d097c5c2767721cb700a4c10699665b`

## Verification

- Source and installed Compose matched before migration.
- Candidate Compose models were equivalent.
- Original container names were preserved.
- Image and environment were preserved.
- Persistent bind mounts were preserved.
- Docker device mappings were preserved.
- External network memberships were preserved.
- Existing DNS aliases were preserved.
- Container health checks passed.
- Vert HTTP response remained HTTP 200.
- Git sources and deployment inventory synchronized.

## Rollback

The original Compose files, inventory and Glance
configuration were backed up before modification.

On a runtime failure, the affected containers are
recreated using their previous Compose project names.

No Docker networks, volumes or persistent application
data are intentionally removed.
