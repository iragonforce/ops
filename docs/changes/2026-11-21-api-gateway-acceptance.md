# API gateway acceptance and NPM network recovery

Date: 2026-11-21

## Changes and verified outcomes

- Standardized the running Kong project/container as `api-gateway`.
- Committed the four active Kong Compose sources in `2f75e9d`.
- Verified independent Bitwarden recovery of all 17 environment values.
- Reconstructed the Compose model without credential mismatches.
- Identified Photon's dynamic allocation of NPM's reserved 172.16.11.4.
- Verified Photon running at 172.16.11.200 and NPM at 172.16.11.4.
- Verified local NPM TLS root HTTP 200.
- Verified six protected GET requests return HTTP 401 without JWT.
- Verified six authenticated API integrations return HTTP 200.

## Operational boundaries

- No Kong routes or authentication configuration needed modification.
- Existing volumes, credentials, container identities and networks retained.
- Photon Compose pin at `/mnt/fast/photon/compose.yaml` requires
  separate Git-source reconciliation.
- Keep encrypted Kong backups and recoverability documentation.
- External signed-in Cloudflare Access validation remains separate.
- Do not remove the stopped rollback container without metadata backup.
