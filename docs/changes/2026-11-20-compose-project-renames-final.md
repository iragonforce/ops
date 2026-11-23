# Final Nexus Docker Compose project migrations

Date: 2026-11-20

## Outcome

All 22 originally targeted `nexus-*` Compose project
renames have been completed.

### IoT

- `nexus-iot` to `iot`
- Six containers verified
- Network addresses and USB mappings preserved

### Step CA

- `nexus-step-ca` to `step-ca`
- Original CA certificate identity preserved
- Three static addresses preserved
- Live startup command retained in Git

### Media

- `nexus-media` to `media`
- Ten containers verified
- Gluetun VPN route and egress verified
- Seven shared-network-namespace applications verified
- Existing `nexus-media_gluetun-egress` bridge retained
  as an external network, with its original Docker ID

### Infrastructure

- `nexus-infrastructure` to `infrastructure`
- Seven containers verified
- Images, environment, mounts, network addresses,
  and published ports preserved
- AdGuard DNS, Authentik and NPM connectivity verified
- AdGuard published port 1054 reconciled with Git

## Recovery backups

- Step CA:
  `/var/backups/homelab/docker-stage6k-step-ca-mGGb3Ec4`
- Media:
  `/var/backups/homelab/docker-media-final-6T3bKo6t`
- Infrastructure:
  `/var/backups/homelab/docker-stage6m-infrastructure-eVSHhZIU`

## Rollback

Use the appropriate project-specific backup and preserved
Compose configuration. Capture current state and data before
any rollback. Never start old and new projects simultaneously.

The Media bridge retains its historical Docker name and
ownership label intentionally; do not delete it.

## Outstanding source reconciliation

The live Infrastructure `compose.override.yaml` is not yet
represented in Git. It contains Authentik SMTP configuration,
including a password-related setting. Do not copy it into Git
until its sensitive values are safely externalized.

The two unrelated preexisting untracked change records remain
outside this migration.

## Scope

This record covers Compose project names. Optional
container-name simplification is a separate task.
