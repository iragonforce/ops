# Nexus API integration deployment registration

Date: 2026-11-18
Host: nexus

## Purpose

Register the five finalized API integrations in
`inventory/deployments.json`.

All five Git-managed Compose definitions were
byte-identical to their installed configurations.

## Canonical deployments

### adguard-summary

- Source: `hosts/nexus/files/srv/containers/compose/adguard-summary/compose.yaml`
- Target: `/srv/containers/compose/adguard-summary/compose.yaml`
- SHA-256: `87e71e8f92a6c2bdf378da9139dc51771a24d29927f6ae6996ec7ea069748764`
- Mode: `0o600`
- Deployed: `False`

### npm-summary

- Source: `hosts/nexus/files/srv/containers/compose/npm-summary/compose.yaml`
- Target: `/srv/containers/compose/npm-summary/compose.yaml`
- SHA-256: `b6505a80ed175d7ae3b3bdfd810137a0ecea08ba5ab8f3ab2d8e30daf994a594`
- Mode: `0o664`
- Deployed: `False`

### stepca-summary

- Source: `hosts/nexus/files/srv/containers/compose/stepca-summary/compose.yaml`
- Target: `/srv/containers/compose/stepca-summary/compose.yaml`
- SHA-256: `0d47c0061b384647e5c018382e3ac0a1fd283d67e10cd37fe8b60a850f41f7d2`
- Mode: `0o600`
- Deployed: `False`

### tensor-connector

- Source: `hosts/nexus/files/srv/containers/compose/tensor-connector/compose.yaml`
- Target: `/srv/containers/compose/tensor-connector/compose.yaml`
- SHA-256: `572c52fa47a54198efad2461131b0b447207b0748a9a3a3532b9316993465775`
- Mode: `0o664`
- Deployed: `False`

### observability

- Source: `hosts/nexus/files/srv/containers/compose/observability/compose.yaml`
- Target: `/srv/containers/compose/observability/compose.yaml`
- SHA-256: `fd6fbf122d6b6b06f90399e2319e93d0965499265fb36b4437e95f33330bf9e4`
- Mode: `0o600`
- Deployed: `False`

## Deployment policy

`preserve target; overwrite only unchanged baseline or previously deployed digest`

The existing adopted-configuration convention
is preserved with `deployed: false`.

The recorded modes reflect actual installed files.
No file permissions were changed.

The npm-summary Compose file was observed with
mode `0664`. This is group-writable and can be
reviewed separately if stricter permissions are
required. The inventory operation did not modify it.

## Validation

- All five Compose files are Git-tracked.
- Git and installed file digests match.
- Existing deployment assets remain unchanged.
- All five mappings use the repository schema.
- No containers or services were modified.

## Rollback

Private inventory backup: `/var/backups/homelab/api-deployments-7rg_dvsu/deployments.json`.

The parent Git commit also contains the
pre-change inventory.
