# Current service and authentication inventory

Read-only capture: 2026-10-30T01:54:04.707414+00:00. Nexus: 69 containers (59 running); 39 nondeleted NPM hosts; 34 have authentik auth_request; 7 have the private administrative source restriction; 36 authentik applications.

This is observed configuration, not a reachability or native-SSO audit. A wildcard edge match applies only when DNS/client routing sends the request through Cloudflare. Split DNS and Tailscale may bypass that layer. Forward auth does not establish an application-native session. Native OIDC support and privileges inside applications remain unassessed. “Retain” below is a proposed next-step model, not a new access grant.

| Host | NPM / upstream | Container state | Current proxy controls | authentik application / allowed bindings | Edge match | Next model |
|---|---|---|---|---|---|---|
| adguard.blinkwired.com | 7 / adguard-home:30004 | exited | authentik forward auth + private sources | blinkwired-service-adguard / roman, authentik Admins | Main Stack wildcard; DNS untested | retain private source + forward auth |
| api.blinkwired.com | 39 / 192.168.1.2:43 | not mapped to container name | no forward-auth/ACL marker in DB | not mapped; inspect native/custom controls | Main Stack wildcard; DNS untested | review intended exposure/native controls; proxy disabled |
| archcore.blinkwired.com | 45 / 100.114.178.50:443 | not mapped to container name | authentik forward auth | blinkwired-service-archcore / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| auth.blinkwired.com | 25 / authentik-server:30140 | running | no forward-auth/ACL marker in DB | not mapped; inspect native/custom controls | authentik identity provider - no recursive Access | retain recursion exception; authentik enforces login |
| bambustudio.blinkwired.com | 184 / bambustudio:3000 | running | authentik forward auth | blinkwired-service-bambustudio / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| bazarr.blinkwired.com | 36 / bazarr:30046 | running | authentik forward auth | blinkwired-service-bazarr / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| blinkwired.com | 191 / glance:8080 | running | authentik forward auth | blinkwired-home / roman, authentik Admins | no public Access match established | retain forward auth; assess native SSO |
| calendar.blinkwired.com | 188 / baikal-baikal-1:80 | running | authentik forward auth | blinkwired-service-calendar / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| checkmk.blinkwired.com | 194 / checkmk:5000 | running | authentik forward auth + private sources | blinkwired-service-checkmk / authentik Admins, roman | Main Stack wildcard; DNS untested | retain private source + forward auth |
| cleanuparr.blinkwired.com | 37 / cleanuparr:30263 | running | authentik forward auth | blinkwired-service-cleanuparr / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| cockpit.blinkwired.com | 197 / 172.16.11.1:9090 | not mapped to container name | authentik forward auth | blinkwired-cockpit / roman, authentik Admins | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| dashboard.blinkwired.com | 174 / glance:8080 | running | authentik forward auth | blinkwired-dashboard / roman, authentik Admins | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| glance.blinkwired.com | 198 / glance:8080 | running | authentik forward auth | blinkwired-glance / roman, authentik Admins | Glance owner identity pilot | owner OIDC pilot + existing forward auth; verified positive path |
| grafana.blinkwired.com | 30 / grafana:30037 | exited | authentik forward auth + private sources | blinkwired-grafana / roman, authentik Admins | Main Stack wildcard; DNS untested | retain private source + forward auth |
| home.blinkwired.com | 176 / home-assistant:30103 | exited | authentik forward auth | blinkwired-service-home / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| homelable.blinkwired.com | 183 / homelable-frontend:80 | running | authentik forward auth | blinkwired-service-homelable / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| iot.blinkwired.com | 13 / home-assistant:30103 | exited | authentik forward auth | blinkwired-service-iot / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| ipx.blinkwired.com | 31 / netbootxyz-netboot:31010 | running | authentik forward auth + private sources | blinkwired-service-ipx / authentik Admins, roman | Main Stack wildcard; DNS untested | retain private source + forward auth |
| jellyfin.blinkwired.com | 28 / jellyfin:8096 | running | authentik forward auth | blinkwired-service-jellyfin / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| lidarr.blinkwired.com | 35 / lidarr:30071 | running | authentik forward auth | blinkwired-service-lidarr / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| makersvault.blinkwired.com | 60 / makersvault-web:5173 | running | authentik forward auth | blinkwired-service-makersvault / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| n8n.blinkwired.com | 9 / n8n:30109 | running | authentik forward auth | blinkwired-service-n8n / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| nexus.homelab.lan | 195 / glance:8080 | running | no forward-auth/ACL marker in DB | not mapped; inspect native/custom controls | no public Access match established | review intended exposure/native controls |
| nexus.tail4e4f0f.ts.net | 190 / 192.168.5.42:80 | not mapped to container name | no forward-auth/ACL marker in DB | not mapped; inspect native/custom controls | no public Access match established | review intended exposure/native controls |
| nginx.blinkwired.com | 17 / 127.0.0.1:81 | not mapped to container name | authentik forward auth + private sources | blinkwired-service-nginx / authentik Admins, roman | Main Stack wildcard; DNS untested | retain private source + forward auth |
| obsidian.blinkwired.com | 41 / obsidian-gui:3000 | not mapped to container name | no forward-auth/ACL marker in DB | not mapped; inspect native/custom controls | Main Stack wildcard; DNS untested | review intended exposure/native controls; proxy disabled |
| paperclip.blinkwired.com | 196 / paperclip:3100 | running | authentik forward auth | blinkwired-paperclip / roman, authentik Admins | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| pdf.blinkwired.com | 193 / stirling-pdf:8080 | running | authentik forward auth | blinkwired-service-pdf / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| portainer.blinkwired.com | 192 / portainer:9443 | running | authentik forward auth + private sources | blinkwired-service-portainer / authentik Admins, roman | Main Stack wildcard; DNS untested | retain private source + forward auth |
| prometheus.blinkwired.com | 29 / prometheus:30104 | exited | authentik forward auth + private sources | blinkwired-service-prometheus / authentik Admins, roman | Main Stack wildcard; DNS untested | retain private source + forward auth |
| prowlarr.blinkwired.com | 32 / prowlarr:30001 | running | authentik forward auth | blinkwired-service-prowlarr / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| radarr.blinkwired.com | 34 / radarr:30025 | running | authentik forward auth | blinkwired-service-radarr / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| seerr.blinkwired.com | 173 / seerr:5055 | running | authentik forward auth | blinkwired-service-seerr / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| sonarr.blinkwired.com | 33 / sonarr:30113 | running | authentik forward auth | blinkwired-service-sonarr / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| sync.blinkwired.com | 10 / syncthing:20910 | running | authentik forward auth | blinkwired-service-sync / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| tasks.blinkwired.com | 189 / vikunja:3456 | running | authentik forward auth | blinkwired-service-tasks / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| torrent.blinkwired.com | 22 / qbittorrent:30200 | running | authentik forward auth | blinkwired-service-torrent / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| vert.blinkwired.com | 19 / vert:80 | running | authentik forward auth | blinkwired-service-vert / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |
| zigbee2mqtt.blinkwired.com | 61 / zigbee2mqtt:8080 | exited | authentik forward auth | blinkwired-service-zigbee2mqtt / authentik Admins, roman | Main Stack wildcard; DNS untested | retain forward auth; assess native SSO |

## Review items

- Five hosts have no auth_request marker: auth.blinkwired.com (intentional IdP exception), api.blinkwired.com, obsidian.blinkwired.com, nexus.tail4e4f0f.ts.net and nexus.homelab.lan. Absence of this marker does not prove unauthenticated exposure; inspect custom routing, native/API controls and DNS before changing them.
- Grafana and Prometheus are stopped. Do not start historical services solely because an old route exists.
- Main Stack still uses broad Google/GitHub provider selectors and historical IP allow policies. OIDC appears as a login choice but is not allowed by its existing shared provider-based allow policy. Only the exact Glance pilot authorizes the owner through OIDC.
- Existing native applications may have separate passwords/accounts and sessions. Do not claim seamless application SSO from proxy authorization alone.
- Classify infrastructure controls (authentik, NPM, Portainer, storage/network management) as administrative; dashboards/development/task tools as personal; media tools separately. These classifications require per-service confirmation and do not grant equivalent privileges.
- Public host ports, firewall policy, LAN/Tailscale DNS, native application permissions and all client-path tests remain outside this capture.

## Sources

Live Docker metadata, read-only NPM SQLite rows, sanitized authentik ORM and Cloudflare API. Nexus source snapshots: /root/.local/state/hom42/phase2-inventory.json and authentik-apps.json. Workspace access-inventory.json records current Access settings. No secrets or environment values were collected.
