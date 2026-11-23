# Shared Glance dashboard — 2026-10-13

## Access

| Connection | Dashboard |
|---|---|
| LAN | http://nexus.homelab.lan |
| Tailscale | https://nexus.tail4e4f0f.ts.net:8448 |
| External | https://dashboard.blinkwired.com — existing Cloudflare Access protection |
| External apex | https://blinkwired.com — existing route retained; previously deferred tunnel publication remains separate |

Views: `/services`, `/nexus`, `/tensor`. Tensor's private `/services/` index now links to the shared `/tensor` dashboard view. No second Glance instance was deployed.

## Completed changes

- Kept Glance v0.8.6 and its existing Home/Gaming/Markets content. Added current service cards on Home, replaced stale Services monitors and added Nexus/Tensor views.
- Replaced obsolete TrueNAS/homelab.io service links with an inventory of **38 endpoints**: 32 Nexus entries and six Tensor entries.
- Added an Automatic / Local network / Tailscale / External selector. Saved manual selection is per browser origin.
- Automatic selection follows the incoming dashboard connection. NPM classifies the original TCP peer (`$realip_remote_addr`); Cloudflare's connector path is external, approved LAN subnets are local, and Tailscale addresses are Tailscale.
- The private Tailscale dashboard gateway explicitly supplies Tailscale context. Direct Glance access classifies its socket peer. Only the known NPM addresses are trusted to supply context headers.
- Having Tailscale enabled does not guarantee that a public-domain connection traverses it. Automatic mode follows the actual dashboard ingress; the selector provides an explicit override.
- Cards refresh every 30 seconds while visible. Read-only endpoint checks run approximately every 60 seconds, separately for each network. Browser refresh/foreground/network-online events refresh context.
- Public probes use public DNS-over-HTTPS answers and TLS SNI, bypassing Nexus's LAN split DNS. They do not carry Cloudflare credentials, cookies or application secrets.
- Reachable, redirected, protected, restricted, private, missing-public-DNS and unreachable endpoints have distinct labels. A Cloudflare Access login redirect is **Protected**, not application Up. Missing public DNS disables the corresponding card link.
- Services with no existing LAN/public endpoint are labelled private on that network. This does not publish Tensor's controls, Cockpit or OpenLinkHub to the public internet.

## Implementation

- Glance retains its IPs/MACs and read-only config mount. Its internal HTTP listener moved to 8081; a small `glance-router` container shares its existing VLAN 5 network namespace and serves the original port 8080.
- Official Python 3.14 slim runtime is pinned to its resolved digest in `/srv/containers/compose/monitoring/compose.yaml`. Compose project name is explicitly `nexus-monitoring`.
- Router source: `/srv/containers/builds/glance-router/router.py`.
- Config, JavaScript, CSS, catalog and generated status JSON: `/srv/containers/data/glance/config` and its `assets` directory.
- NPM custom configuration: `/srv/containers/data/nginx/data/nginx/custom/glance-network.conf`, included from existing `http.conf`.
- Existing dashboard proxy hosts 174, 191 and 195 gained a read-only `/__homelab/` context route. Their existing domain/certificate/access settings were retained; the LAN host's allowlist remains in place.
- Added private HTTPS dashboard port 8448 and app gateway ports 8701–8730. Existing HA 8443, Grafana 8444 and Cockpit 443 URLs remain preferred.
- App gateways use the existing NPM container for HTTP/WebSocket forwarding and loopback relays. No public Funnel is enabled. No router, Cloudflare DNS, tunnel or Access policy was changed.
- MakersVault's upstream Host is its already-allowed canonical hostname; its browser URL remains Tailscale. Gateway redirects from HTTP on the same host are rewritten to HTTPS, including Checkmk's `/cmk/` login.
- `glance-network-relay.service` and `glance-network-status.service` are enabled at boot. The relay uses DynamicUser and systemd LoadCredential for its port map. No existing private-directory permissions were broadened.
- NPM's previous 256 MiB limit caused confirmed cgroup OOM kills during reload. Increased it to **1 GiB**, swap limit 2 GiB, both in runtime and maintained Compose. Restarted NPM to recover its master/workers. Its measured usage after stabilization was approximately 174 MiB.
- A failed, newly created container from an incorrect temporary Compose project was removed before deploying in the existing project. Existing app data was not removed. No package-manager lock was altered.

## Verification

- Glance and glance-router healthy; NPM running. Glance's existing IPv4 and MAC assignments were compared with the pre-change Compose configuration and retained.
- Qubit LAN context returned `local`; private HTTPS context returned `tailscale`.
- Browser rendered 38 cards. Local and external selector changes produced the corresponding IP/domain links. Tensor view rendered six cards. Automatic mode was restored, and the Services view was left open.
- A connector-style proxy-network request returned `external` even with forged local forwarding/context headers.
- Representative private app pages returned 200, including AdGuard, Syncthing, qBittorrent, Jellyfin, Portainer, MakersVault and Checkmk's followed HTTPS login.
- Existing Nexus Cockpit, HA and Grafana endpoints returned 200 after rollout.
- Latest endpoint counts: local 31 reachable, two protected, three private and two down; Tailscale 34 reachable, two protected and two down; external 31 protected and seven private.
- **Immich and PhotoPrism remain unreachable** at their existing Nexus backends. These were already down before the dashboard switch. They remain visible with failure status.
- External Cloudflare probes encountered Access protection. An authenticated dashboard session from a physically external client was not exercised. Actual application logins, OAuth callbacks and interactive WebSocket operations were not exercised for every service. Endpoint reachability is not database/application health.

## Recovery and rollback

Private backups and summary: `/var/lib/glance-network-20261013`.

1. Remove only this change's Serve handlers (8448 and 8701–8730); retain Cockpit, HA, Grafana and any later handlers. Original Serve configuration is saved.
2. Stop the two `glance-network-*` systemd services.
3. Stop/remove only the added `glance-router` container. Restore the original Glance configuration and the Glance portion of the monitoring Compose backup, retaining unrelated subsequent stack edits. Recreate Glance in project `nexus-monitoring`; its original listener is 8080.
4. Restore only the three dashboard proxy hosts' previous advanced configuration from `npm-routes-before.json`. Remove this change's custom include/config and validate/reload NPM.
5. Restore Tensor's service index from `/var/lib/tensor-tailscale-web-20261013/index-before-glance.html` if needed.
6. NPM's old Compose and memory settings are saved. Retaining the larger limit is recommended; lowering it while the extra gateways/configuration remain can repeat the OOM failure.

Do not restore entire HA/application databases, remove unrelated containers, globally reset Tailscale Serve, alter secrets or modify source migration archives as part of dashboard rollback.

Configuration reference: https://github.com/glanceapp/glance/blob/v0.8.6/docs/configuration.md
