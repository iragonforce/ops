# Nexus API gateway — 2026-11-09

The Hermes desktop project **API** is anchored at `/opt/data/workspace/api`. Its non-secret Compose source, complete 75-container inventory, 69-route Kong catalog, root response snippet, and encrypted rollback artifacts are on the private `iragonforce/backup` branch `api-gateway-2026-11-09`. The live deployment remains `/opt/homelab-api` on Nexus; there is no second gateway. The private repository branch is a secret-bearing configuration backup **only in encrypted form**; it is not an application-state or independent Bitwarden backup. Read the project `README.md` and `RECOVERY.md` before changing it.

Kong 3.9.4 has 69 services, five JWT consumers (the four original consumers plus dedicated `qbittorrent-metrics` with only `media-read`), a disabled Admin API, and a global JWT gate with per-service ACLs. The monitoring consumer was deployed and tested November 13; see `docs/current/nexus-qbittorrent-monitoring.md`. NPM proxy host 201 forwards `api.blinkwired.com` to `api-gateway:8000`. Its exact-root Nginx location returns a non-sensitive JSON welcome document; all other paths are proxied to Kong. Cloudflare Access intercepts public requests before the origin, so a signed-in external client check remains outstanding. Local NPM TLS returned 200 for root and authenticated read routes, 401 for protected paths without JWT. Direct Kong root remains 404 by design; NPM owns the domain root response.

The previously pending GET-only Sonarr, Radarr, Lidarr, Prowlarr, qBittorrent and Bazarr full API routes are active for `api-full-read` consumers, with upstream keys injected from Bitwarden. Photon status was restored with its existing vault token. The existing live Bazarr key was added to Bitwarden Secrets Manager `infrastructure` as `BAZARR_API_KEY` (ID `2e42c538-42e7-491b-936a-b4fd013950c3`). The sole remaining `api-expansion-pending` route is FlareSolverr's arbitrary-target POST; do not grant it without a separately scoped SSRF/egress review. The detailed route list and unmatched-container dispositions are in the API workspace, not repeated here.

A verified encrypted pre-change Kong JSON and NPM host record were pushed to the private GitHub branch before modification. The November 9 Kong artifact has plaintext SHA-256 `e4e87e34e9df8d50fbe03e2d16779a0c07acdbbcddce17420799de9a3f0156fa`; the **current live** file after the monitoring consumer deployment is `e94fd7644853dfcc51876059b36a5152c0c7e2b4c5ebd19e65ad5a135f79eda9`, encrypted on private `iragonforce/backup` branch `qbittorrent-metrics-kong-2026-11-12`. Its Bitwarden decryption key is `API_KONG_BACKUP_GPG_PASSPHRASE_V1` (ID `08d472d9-9c70-49de-9008-b4fd0132c9c8`). Do not expose either value or the raw Kong JSON in Git or logs. Roll back with the selected encrypted Git revision after checking live drift and preserving the matching Compose overlay; use `/opt/homelab-api` as the *actual host path* in disposable Compose tooling. The old NPM upstream was broken, so revert it only if intentionally returning to that pre-task condition. Owner-side independent Bitwarden retrieval and external signed-in Cloudflare Access behavior are not yet verified.

## Deployment recovery verification — 2026-11-21

The running Compose project and container are `api-gateway`.
The original deployment directory remains `/opt/homelab-api` for compatibility with existing Compose metadata and environment dependencies. The canonical configuration directory is `/srv/containers/compose/api-gateway`. The four active Compose paths under `/opt/homelab-api` are compatibility symlinks to the canonical Compose files. The inactive `compose.photon-auth.yml` remains a separate regular file. Structural Compose equivalence was verified, but full environment interpolation remains unverified.

The Git-managed Compose sources are under
`hosts/nexus/files/srv/containers/compose/api-gateway/`:

- `compose.yml`
- `compose.override.yml`
- `compose.qbittorrent-auth.yml`
- `compose.api-expansion.yml`

`compose.photon-auth.yml` is not part of the active deployment.
Do not include it implicitly during recovery.

### Bitwarden credential mappings

The existing `agent-secrets.service` uses an encrypted systemd
credential named `bws-access-token`. Its machine account was
verified to retrieve all 17 required Kong deployment values.

| Compose variable | Bitwarden secret key |
|---|---|
| ADGUARD_PASSWORD | ADGUARD_PASSWORD |
| ADGUARD_USER | ADGUARD_USER |
| CHECKMK_NEXUS_API_KEY | CHECKMK_NEXUS_API_KEY |
| HOME_ASSISTANT_API_KEY | HOME_ASSISTANT_API_KEY |
| KONG_BAZARR_API_KEY | BAZARR_API_KEY |
| KONG_LIDARR_API_KEY | LIDARR_API_KEY |
| KONG_PROWLARR_API_KEY | PROWLARR_API_KEY |
| KONG_RADARR_API_KEY | RADARR_API_KEY |
| KONG_SONARR_API_KEY | SONARR_API_KEY |
| KONG_SYNCTHING_API_KEY | SYNCTHING_API_KEY |
| N8N_API_TOKEN | N8N_API_TOKEN |
| PHOTON_API_TOKEN | PHOTON_API_TOKEN |
| PORTAINER_API_KEY | PORTAINER_API_KEY |
| QBITTORRENT_API_KEY | QBITTORRENT_API_KEY |
| WEALTHFOLIO_RECEIPT_MATCH_READ | WEALTHFOLIO_RECEIPT_MATCH_READ |
| WRANGLER_API_KEY | WRANGLER_API_KEY |
| ZIGBEE2MQTT_AUTH_TOKEN | ZIGBEE2MQTT_AUTH_TOKEN |

Resolve secrets by exact Bitwarden key. Do not rely on matching
values or exporting secrets to persistent plaintext files.

The November 21 verification authenticated to Bitwarden
independently of Kong, resolved all 17 keys, rendered the four-file
Compose model, and matched all required values against the
healthy running container without mismatches.

This verifies credential availability and configuration rendering,
not a complete disaster-recovery rebuild.

### Network recovery and API acceptance

A Docker address collision prevented Nginx Proxy Manager from
starting. Photon dynamically occupied NPM's reserved
`proxy-backend` address `172.16.11.4`.

Verified final network state:

- NPM: `proxy-backend` 172.16.11.4; `docker-vlan` 192.168.5.20
- Photon: `proxy-backend` 172.16.11.200
- Kong: `proxy-backend` 172.16.11.108

Photon's address is pinned in `/srv/containers/compose/photon/compose.yaml`.
Its non-secret Compose source is tracked at
`hosts/nexus/files/srv/containers/compose/photon/compose.yaml`.
The three secret mounts retain their existing external sources;
credential contents are not stored in Git.

Local acceptance through NPM HTTPS:

- `https://api.blinkwired.com/`: HTTP 200
- Six representative unauthenticated GET routes: HTTP 401
- Authenticated Sonarr, Radarr, Lidarr, Prowlarr, Bazarr,
  and qBittorrent GET endpoints: HTTP 200, all six

Kong remains healthy with 69 services and five JWT consumers.

### Recovery boundaries

The existing encrypted Kong configuration backups are documented
in this file and the API project recovery documentation. Preserve
their encryption and verify the relevant revision before restoring.

Do not store raw Kong JWT signing secrets, Bitwarden credentials,
or decrypted configuration in this repository.

The stopped `api-gateway-rollback` container was retained during
acceptance. It may be retired only after protected metadata backup
and a final running-state verification.

External signed-in Cloudflare Access acceptance is separate from
the completed local NPM/Kong acceptance tests.
