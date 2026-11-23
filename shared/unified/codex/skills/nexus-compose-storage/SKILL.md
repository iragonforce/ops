---
name: nexus-compose-storage
description: Work on Nexus Compose services or storage while preserving datasets, credentials and rollback paths.
---

# Nexus Compose and storage

Confirm the execution host and inspect the current Compose definition, container mounts, health and dependent services before a change. Maintained Compose lives in `/srv/containers/compose`; active data is under `/srv/containers/data`. Confirm bind sources exist before recreating a service.

Preserve bulk and fast pools, snapshots, fixed Docker addresses, radio identities and private credentials in `/etc/nexus/secrets`. Never format pools, recursively change pool ownership, or migrate a live database without a matching old image and data rollback.

Record the exact before-state and a targeted rollback for consequential changes. Use `jq`/`yq` for bounded inventories and `shellcheck` for shell scripts when relevant. Use Trivy only for an assigned security audit, with selected scanners and concise findings. Report operational checks as checks, not proof of untested physical behavior. Do not add formal tests unless asked.
