# Nexus Docker Compose fleet consolidation — final acceptance

Date: 2026-11-23
Host: nexus
Branch: consolidate
Acceptance baseline: dedcfe6

## Result

**PASS — zero acceptance issues.**

- 78 of 78 Docker containers running.
- 42 of 42 Compose projects have Git-tracked canonical primary files.
- 41 of 42 deployed primary files match Git byte-for-byte.
- Hermes is the sole documented primary-file exception.
- Four active supplementary Compose overlays verified against Git.
- Eight legacy Compose compatibility symlinks verified.
- Six redundant legacy Git source files retired.
- Live Glance catalog matches Git.
- Container identities, states and startup timestamps unchanged.
- Rollback artifacts verified present.

## Canonical source

Deployment directory:

`/srv/containers/compose/<project>/`

Git source:

`hosts/nexus/files/srv/containers/compose/<project>/`

Legacy Compose paths that remain in Docker metadata are
preserved using compatibility symlinks.

## Documented exceptions

### Hermes

The deployed configuration uses:

`localhost/hermes-agent:v0.21.6-tools-1-quota5`

It also includes `HERMES_QUOTA_TEST_FILE`.

These are the only effective Compose differences from Git.
The running container matches the deployed configuration.
The Qdrant network attachment is committed and verified.

Do not overwrite the deployed test configuration without
first determining whether the quota experiment is complete.

### API Gateway

Original, canonical and compatibility-symlink Compose
configurations rendered identical structural models.

Full environment interpolation remains unverified because
the required deployment environment inputs were unavailable.

Do not recreate API Gateway without resolving those inputs.

The inactive `compose.photon-auth.yml` is preserved.

### CraftControl

The active two-service Compose configuration is tracked.
Alternative Compose definitions are retained separately.

### Protected Hermes backups

A root-owned 0700 backup directory caused a Git status
permission warning. Its permissions were intentionally
left unchanged.

## Recovery artifacts

- `/var/backups/homelab/compose-batch-b-ADz4g0Yv`
- `/var/backups/homelab/glance-obsidian-OW2rtPVk`
- `/var/backups/homelab/compose-external-retirement-sapurwp3`
- `/var/backups/homelab/api-gateway-compose-retirement-yfalb0i9`

Historical configurations are also preserved in Git
history and documented recovery archives.

## Operational conclusion

The consolidation is accepted.

No container recreation, restart or data migration is
required for closure.

Future work on Hermes quota testing, API Gateway
environment restoration, and CraftControl alternatives
is separate from this completed consolidation.
