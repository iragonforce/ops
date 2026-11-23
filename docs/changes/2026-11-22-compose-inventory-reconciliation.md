# Nexus Compose inventory reconciliation

Date: 2026-11-22
Host: nexus
Branch: consolidate

## Changes

The deployment inventory was corrected for:

| Project | Old directory | Canonical directory |
|---|---|---|
| baikal | baikal-baikal-1 | baikal |
| netbootxyz | netbootxyz-netboot | netbootxyz |
| obsidian | obsidian-nexus | obsidian |

All directories are below `/srv/containers/compose/`.

Exactly three existing inventory records were updated.
Only their `source` and `target` fields changed.

The original baseline hashes, overwrite policies, modes,
and `deployed` flags were retained. The historical baseline
hashes are not equal to the current deployed file hashes;
this condition requires separate review before automated
deployment.

## Validation

Canonical and legacy Git source files matched their
corresponding deployed Compose files byte-for-byte.

No running containers or Compose configurations were changed.

## Recovery

Six unique historical configuration backups were previously
committed in `db099a6`.

Archive:
`docs/archive/nexus-compose-recovery/2026-11-22/`

The previous inventory version remains recoverable from
Git history.

Original legacy deployment directories are intentionally
retained until the next cleanup stage.

## Remaining work

- Classify current inventory references.
- Reconcile the Glance Obsidian container identity.
- Verify Compose management paths.
- Remove obsolete Git source files and deployed directories.
- Preserve running container identities and startup times.
