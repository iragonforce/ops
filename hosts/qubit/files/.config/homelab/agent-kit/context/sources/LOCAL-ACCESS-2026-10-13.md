# Homelab local access — 2026-10-13

Local records are served by UDR7. Qubit uses a domain resolver for `homelab.lan` and `blinkwired.com`; its general DNS remains Cloudflare `1.1.1.1`. Linux hosts use UDR7 for LAN names. AdGuard is not the resolver.

These names are configured on Qubit, Nexus and Tensor for use on the home LAN. Other clients using only public DNS need UDR7 (`192.168.1.1`) as their resolver, or their own `homelab.lan` domain resolver. Use the Tailscale relay command below when away from the LAN.

## Completed checks

- All 59 host/container/alias records resolved to their expected LAN addresses through Qubit's native resolver.
- SSH worked between Qubit, Nexus and Tensor through local names. Existing credentials and host-key trust were retained. Nexus's root-owned user `known_hosts` file was backed up and its ownership corrected.
- Dashboard, Home Assistant, Jellyfin, CUPS and Tensor services answered through the new hostnames. CUPS's explicit hostname allowlist was updated and reloaded.
- Nexus SSH, SMB and NFS ports were reachable from Qubit's reserved Wi-Fi address.
- Wake senders worked directly from Qubit Wi-Fi and through the Nexus Tailscale relay. Tensor is online with a fresh boot; Linux magic-packet/PCIe wake and startup-notification services are enabled. Qubit has wake-for-network enabled for AC and battery power; its wired sleep-wake hardware path was inspected, not power-cycled.
- Final Docker verification: 52 containers running, 106 pinned interfaces, all 38 configured health checks healthy.

## Hosts

| Host | Local name | LAN IP | Access |
| --- | --- | --- | --- |
| Nexus | `nexus.homelab.lan` | `192.168.1.2` | [Dashboard](http://nexus.homelab.lan), `ssh nexus.homelab.lan`, Finder → `smb://nexus.homelab.lan` |
| Tensor | `tensor.homelab.lan` | `192.168.1.3` | `ssh tensor.homelab.lan` |
| Qubit Wi-Fi | `qubit.homelab.lan` | `192.168.1.102` | `ssh qubit.homelab.lan` from Nexus/Tensor |
| Qubit Ethernet | `qubit-wired.homelab.lan` | `192.168.1.4` | Alternate wired address |

Qubit Wi-Fi has a reservation for its current private Wi-Fi MAC. The local dashboard uses HTTP. Existing `blinkwired.com` routes offer their existing HTTPS certificates. Direct `.homelab.lan` URLs retain the application port; Portainer’s direct HTTPS endpoint requires trust in its own certificate. Authentication is unchanged.

## Nexus container endpoints

Status codes 200/302 indicate a page or login redirect; 401/403 require application authorization. Other HTTP responses show that a listener answered, without proving application functionality. APIs, metrics and protocol endpoints are not necessarily browser interfaces.

| Container | Direct local endpoint | Existing HTTPS route | Check |
| --- | --- | --- | --- |
| 3d-printer-mcp | `3d-printer-mcp.homelab.lan` | — | No LAN TCP listener; use its configured MCP transport |
| adguard-home | [http://adguard-home.homelab.lan:30004](http://adguard-home.homelab.lan:30004) | [https://adguard.blinkwired.com](https://adguard.blinkwired.com) | HTTP 302 |
| authentik-server | [http://authentik-server.homelab.lan:30140](http://authentik-server.homelab.lan:30140) | [https://auth.blinkwired.com](https://auth.blinkwired.com) | HTTP 302 |
| baikal-baikal-1 | [http://baikal-baikal-1.homelab.lan](http://baikal-baikal-1.homelab.lan) | [https://calendar.blinkwired.com](https://calendar.blinkwired.com) | HTTP 200 |
| bambustudio | [http://bambustudio.homelab.lan:3000](http://bambustudio.homelab.lan:3000) | [https://bambustudio.blinkwired.com](https://bambustudio.blinkwired.com) | HTTP 200 |
| bazarr | [http://bazarr.homelab.lan:30046](http://bazarr.homelab.lan:30046) | [https://bazarr.blinkwired.com](https://bazarr.blinkwired.com) | HTTP 200 |
| cadvisor | [http://cadvisor.homelab.lan:8080](http://cadvisor.homelab.lan:8080) | — | HTTP 307 |
| checkmk | [http://checkmk.homelab.lan:5000/cmk/](http://checkmk.homelab.lan:5000/cmk/) | [https://checkmk.blinkwired.com/cmk/](https://checkmk.blinkwired.com/cmk/) | HTTP 302 |
| cleanuparr | [http://cleanuparr.homelab.lan:30263](http://cleanuparr.homelab.lan:30263) | [https://cleanuparr.blinkwired.com](https://cleanuparr.blinkwired.com) | HTTP 200 |
| cloudflared | [http://cloudflared.homelab.lan:20241/metrics](http://cloudflared.homelab.lan:20241/metrics) | — | HTTP 200 |
| cups | [http://cups.homelab.lan:631](http://cups.homelab.lan:631) | — | HTTP 200 |
| flaresolverr | [http://flaresolverr.homelab.lan:8191](http://flaresolverr.homelab.lan:8191) | — | HTTP 200 |
| glance | [http://glance.homelab.lan:8080](http://glance.homelab.lan:8080) | [https://dashboard.blinkwired.com](https://dashboard.blinkwired.com), [https://blinkwired.com](https://blinkwired.com) | HTTP 200 |
| grafana | [http://grafana.homelab.lan:30037](http://grafana.homelab.lan:30037) | [https://grafana.blinkwired.com](https://grafana.blinkwired.com) | HTTP 302 |
| hermes | [http://hermes.homelab.lan:8642/health](http://hermes.homelab.lan:8642/health) | — | HTTP 200 |
| home-assistant | [http://home-assistant.homelab.lan:30103](http://home-assistant.homelab.lan:30103) | [https://iot.blinkwired.com](https://iot.blinkwired.com), [https://home.blinkwired.com](https://home.blinkwired.com) | HTTP 200 |
| homelable-backend | [http://homelable-backend.homelab.lan:8000](http://homelable-backend.homelab.lan:8000) | — | HTTP 404 |
| homelable-frontend | [http://homelable-frontend.homelab.lan](http://homelable-frontend.homelab.lan) | [https://homelable.blinkwired.com](https://homelable.blinkwired.com) | HTTP 200 |
| jellyfin | [http://jellyfin.homelab.lan:8096](http://jellyfin.homelab.lan:8096) | [https://jellyfin.blinkwired.com](https://jellyfin.blinkwired.com) | HTTP 302 |
| lidarr | [http://lidarr.homelab.lan:30071](http://lidarr.homelab.lan:30071) | [https://lidarr.blinkwired.com](https://lidarr.blinkwired.com) | HTTP 200 |
| makersvault-api | [http://makersvault-api.homelab.lan:8000/docs](http://makersvault-api.homelab.lan:8000/docs) | — | HTTP 200 |
| makersvault-web | [http://makersvault-web.homelab.lan:5173](http://makersvault-web.homelab.lan:5173) | [https://makersvault.blinkwired.com](https://makersvault.blinkwired.com) | HTTP 403 |
| matter-server | ws://matter-server.homelab.lan:5580/ws | — | Protocol endpoint |
| mcp-homelable | [http://mcp-homelable.homelab.lan:8001](http://mcp-homelable.homelab.lan:8001) | — | HTTP 401 |
| minecraft-bedrock | minecraft-bedrock.homelab.lan:19132 | — | Bedrock game server, UDP |
| mosquitto | mqtt://mosquitto.homelab.lan:1883 | — | MQTT protocol |
| n8n | [http://n8n.homelab.lan:30109](http://n8n.homelab.lan:30109) | [https://n8n.blinkwired.com](https://n8n.blinkwired.com) | HTTP 200 |
| netbootxyz-netboot | [http://netbootxyz-netboot.homelab.lan:31010](http://netbootxyz-netboot.homelab.lan:31010) | [https://ipx.blinkwired.com](https://ipx.blinkwired.com) | HTTP 200 |
| nginx-proxy-manager | [http://nginx-proxy-manager.homelab.lan:81](http://nginx-proxy-manager.homelab.lan:81) | [https://nginx.blinkwired.com](https://nginx.blinkwired.com) | HTTP 200 |
| node-exporter | [http://node-exporter.homelab.lan:9100/metrics](http://node-exporter.homelab.lan:9100/metrics) | — | HTTP 200 |
| otbr | [http://otbr.homelab.lan:8081/node/state](http://otbr.homelab.lan:8081/node/state) | — | HTTP 200 |
| portainer | [https://portainer.homelab.lan:9443](https://portainer.homelab.lan:9443) | [https://portainer.blinkwired.com](https://portainer.blinkwired.com) | TLS trust required |
| prometheus | [http://prometheus.homelab.lan:30104](http://prometheus.homelab.lan:30104) | [https://prometheus.blinkwired.com](https://prometheus.blinkwired.com) | HTTP 302 |
| prowlarr | [http://prowlarr.homelab.lan:30001](http://prowlarr.homelab.lan:30001) | [https://prowlarr.blinkwired.com](https://prowlarr.blinkwired.com) | HTTP 200 |
| qbittorrent | [http://qbittorrent.homelab.lan:30200](http://qbittorrent.homelab.lan:30200) | [https://torrent.blinkwired.com](https://torrent.blinkwired.com) | HTTP 200 |
| radarr | [http://radarr.homelab.lan:30025](http://radarr.homelab.lan:30025) | [https://radarr.blinkwired.com](https://radarr.blinkwired.com) | HTTP 200 |
| seerr | [http://seerr.homelab.lan:5055](http://seerr.homelab.lan:5055) | [https://seerr.blinkwired.com](https://seerr.blinkwired.com) | HTTP 307 |
| sonarr | [http://sonarr.homelab.lan:30113](http://sonarr.homelab.lan:30113) | [https://sonarr.blinkwired.com](https://sonarr.blinkwired.com) | HTTP 200 |
| stirling-pdf | [http://stirling-pdf.homelab.lan:8080](http://stirling-pdf.homelab.lan:8080) | [https://pdf.blinkwired.com](https://pdf.blinkwired.com) | HTTP 200 |
| syncthing | [http://syncthing.homelab.lan:20910](http://syncthing.homelab.lan:20910) | [https://sync.blinkwired.com](https://sync.blinkwired.com) | HTTP 200 |
| tg-bot | [http://tg-bot.homelab.lan:8080/commands](http://tg-bot.homelab.lan:8080/commands) | — | HTTP 200 |
| vert | [http://vert.homelab.lan](http://vert.homelab.lan) | [https://vert.blinkwired.com](https://vert.blinkwired.com) | HTTP 200 |
| vertd | [http://vertd.homelab.lan:24153](http://vertd.homelab.lan:24153) | — | HTTP 404 |
| vikunja | [http://vikunja.homelab.lan:3456](http://vikunja.homelab.lan:3456) | [https://tasks.blinkwired.com](https://tasks.blinkwired.com) | HTTP 200 |
| webhook-notify | [http://webhook-notify.homelab.lan:9876/health](http://webhook-notify.homelab.lan:9876/health) | — | HTTP 200 |
| zigbee2mqtt | [http://zigbee2mqtt.homelab.lan:8080](http://zigbee2mqtt.homelab.lan:8080) | [https://zigbee2mqtt.blinkwired.com](https://zigbee2mqtt.blinkwired.com) | HTTP 200 |

## Private backend containers

`home-assistant-postgres`, `authentik-redis`, `authentik-postgres`, `authentik-worker`, `n8n-redis`, `n8n-postgres`.
These remain on private Docker networks. Access through their applications or an authenticated Nexus shell; no LAN database endpoints were exposed.

## Tensor services

| Service | Access |
| --- | --- |
| Syncthing | [http://tensor.homelab.lan:8384](http://tensor.homelab.lan:8384) |
| RStudio | [http://tensor.homelab.lan:8787](http://tensor.homelab.lan:8787) |
| Ollama API | [http://tensor.homelab.lan:11434/api/tags](http://tensor.homelab.lan:11434/api/tags) |
| Fixed power/RGB control API | `http://tensor.homelab.lan:8769` — existing authorization required |
| OpenRGB SDK | `tensor.homelab.lan:6742` — SDK protocol |
| OpenLinkHub | `ssh -N -L 6743:127.0.0.1:6743 tensor.homelab.lan`, then `http://127.0.0.1:6743` |

## Qubit services

- SSH: `ssh qubit.homelab.lan` from either Linux host.
- Obsidian REST API listens on Qubit loopback port 27124. Access locally at `https://127.0.0.1:27124`; from a peer use `ssh -N -L 27124:127.0.0.1:27124 qubit.homelab.lan`. Existing API credentials and certificate trust are required.
- AirPlay/Continuity listeners are macOS protocols, not browser dashboards.

## Storage

Finder → Go → Connect to Server: `smb://nexus.homelab.lan`. Available Samba shares: `Bulk Storage - 1 TB Limit`, `Fast Shared Files`.
The existing macOS NFS automounts remain configured through Tailscale for their previous recovery behavior. DNS configuration does not move or alter shared data.

## Wake and host controls

```sh
tensor on                 # Qubit on the home LAN, including native Wi-Fi
tensor on --via nexus     # Wake through an awake Nexus over Tailscale
tensor status
ssh tensor.homelab.lan
```

`nexus on/off`, `tensor on/off`, and `qubit on/off` remain installed. Qubit off sleeps; Linux off shuts down. Qubit wake targets its USB Ethernet MAC and requires the wired adapter/network to remain available during sleep. Linux NIC magic-packet wake and PCIe wake are enabled and persistent. No host was shut down for this check.

## Existing routes without a current listener

Legacy proxy records for TrueNAS, Immich, PhotoPrism, OpenClaw and Tensor Cockpit remain in NPM but their previous services were not found listening in this inventory. They are excluded from the working endpoint list.

## Configuration and rollback

UDR7 records and before-state are in Qubit’s `outputs/udr7-network/private/local-hostnames-20261013.json`, `local-hostnames-before-20261013.json` and `local-dns-client-records-before-20261013.json`. Restore modified policy/client fields by object ID; delete only newly created DNS records.
Nexus backups: `/var/lib/nexus-local-dns-20261013/`. Restore the original access files and reload their own nftables tables, exports and Samba; restore changed NPM advanced_config fields from the SQLite backup and regenerate those hosts. The new dashboard ID is recorded in `local-dashboard-id.json` and may be disabled/removed to roll back.
Tensor NetworkManager/firewall backups: `/var/lib/tensor-local-dns-20261013/`. Restore the recorded DNS fields and reapply the connection without changing its IP.
Qubit resolver backup: `/var/db/homelab-local-dns-20261013/`; remove the new `/etc/resolver/homelab.lan` or restore its before-state. SSH before-state is under each user’s `~/.config/homelab/local-dns-backup-20261013/`. Original credentials and keys were preserved.
