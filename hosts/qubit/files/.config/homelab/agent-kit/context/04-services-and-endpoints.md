# Service access and deployment references

The complete recorded local-access table is `sources/LOCAL-ACCESS-2026-10-13.md`; current container IP/MAC/image/state/mount metadata is `11-live-nexus-inventory.json`. Do not reconstruct addresses from the old TrueNAS service table alone.

| Service | Recorded access |
|---|---|
| Shared Glance dashboard | LAN http://nexus.homelab.lan ; tailnet https://nexus.tail4e4f0f.ts.net:8448 |
| Nexus Cockpit | https://nexus.tail4e4f0f.ts.net |
| Tensor Cockpit | https://tensor.tail4e4f0f.ts.net |
| Home Assistant | https://nexus.tail4e4f0f.ts.net:8443 ; LAN http://home-assistant.homelab.lan:30103 |
| Grafana | https://nexus.tail4e4f0f.ts.net:8444 ; existing grafana.blinkwired.com route |
| Checkmk | http://checkmk.homelab.lan:5000/cmk/ ; https://checkmk.blinkwired.com/cmk/ |
| Telegram REST reference | http://192.168.5.242:8080 ; GET /commands is read-only |
| qBittorrent | http://192.168.2.10:30200 ; torrent.blinkwired.com |
| Jellyfin | Existing jellyfin.blinkwired.com and local catalog entry |
| Hermes | Existing CLI; VLAN 5 address 192.168.5.55 |

2026-10-19 Authentik current state: `kroman` was renamed to `roman`; the account is active, internal, non-admin and has no group memberships. Direct user bindings grant access to all 34 `blinkwired-*` protected service applications, alongside the existing Authentik Admins bindings. New Authentik sessions last 30 days. Confirmed WebAuthn users use a passkey-only stage; users without a confirmed passkey retain password/default MFA login. Roman still needs to enroll a passkey for that route. Downstream app logins/roles may be separate. No password value is recorded here. See CHANGELOG and private Nexus backup `/var/backups/homelab/authentik-roman-20261019/` for rollback.

Tensor Syncthing, OpenLinkHub, OpenRGB relay and service index have private Tailscale endpoints described in `sources/TAILSCALE-WEBSITES-2026-10-13.md`. Preserve individual Serve handlers; a global Serve reset would disrupt unrelated services.

One Nexus-hosted Glance covers both machines. It has Services/Nexus/Tensor views and Automatic/Local/Tailscale/External selection. Automatic mode follows actual dashboard ingress, not simply whether the client has Tailscale running. Cloudflare Access responses are classified Protected, not proof that an app itself is usable. No second Tensor dashboard was requested.

Services restored include authentication/proxy, monitoring, IoT, media, photographs, Git and other existing applications. Keep maintained Compose project names and private backend networks. Reject missing bind sources rather than allowing Docker to create empty data directories. Existing IP and MAC pinning must be preserved on recreation.

The user requested removal of `unifi-mcp`, `termix-guacd`, `termix`, `obsidian-gui`, and `journal`. Treat that as historical intent and compare live inventory before asserting all related resources were deleted; never delete a similarly named unrelated service or its retained data from this note alone.

Public `*.blinkwired.com` traffic may require Cloudflare Access. No public bypass or new public administrative endpoint should be inferred from a LAN success. The apex dashboard's publication was left pending. Local DNS and existing HTTPS certificates were configured separately.

Image upgrades were pinned during restoration. Choose current vendor-supported stable versions only when an upgrade is requested, preserve data compatibility and rollback, and do not run an unattended blanket `latest` pull as part of context setup.

## 2026-10-16 — Syncthing folder-ID reconciliation (sync still in progress)

User specified that files must always be preserved and Qubit's Obsidian is authoritative. Configuration now has exactly six folder IDs on each host, each listing Qubit/Nexus/Tensor: project `9u4zc-b3psw`, screenshots `bgafe-rocjp`, downloads `cfw72-bfx5c`, Obsidian `i6gtg-mdcdh`, documents `ruzm6-fkqhz`, 3d-models `xperf-9p7s3`. Disabled peer auto-accept on all three to prevent duplicate re-creation. Qubit's former `jtpwg-pycck` documents share was replaced by `ruzm6-fkqhz` at the same path; Tensor's redundant `jtpwg-pycck`, `kau3z-kcsrz`, `hrlfr-6m2j7` folder entries were removed without removing their source directories. Tensor's retained downloads ID now points to `~/Downloads`; restored its `.stfolder` marker after Syncthing removed it when the former ID was dropped. Nexus gained the previously absent Qubit documents and Tensor Obsidian/3d-models membership. Qubit Obsidian is send-only and was overridden as source; Nexus and Tensor Obsidian are receive-only. Qubit/Tensor Obsidian reached 31,191 local/global files, idle, zero errors; Nexus was still reconciling its larger former copy. Documents were still transferring: monitor all three until local/global counts converge and errors remain zero. The former Qubit documents and Nexus Obsidian files may be removed from their *live* folders during reconciliation; their preserved copies below are the recovery sources.

Pre-change private config copies: Qubit `~/Library/Application Support/Syncthing/config.xml.pre-reconcile-20261016-190103`, Tensor `~/.local/state/syncthing/config.xml.pre-reconcile-20261016-190103`, Nexus `/srv/containers/data/syncthing/config/config/config.xml.pre-reconcile-20261016-190103` (container `/var/syncthing/config/config.xml.pre-reconcile-20261016-190103`), all mode 0600. Data preservation: Qubit and Tensor `~/.local/state/syncthing-reconcile-20261016-190103/` (each mode 0700; per-folder copies include the old Documents and Obsidian data); Nexus `/mnt/bulk/data/syncthing-reconcile-20261016-190103/nexus-obsidian` and `nexus-documents` (parent mode 0700). Tensor's retired folder directories remain in place as additional copies. Rollback: pause affected shares first, preserve any post-change files separately, restore the appropriate saved config through Syncthing's authenticated REST API or a coordinated stopped-service restore, and reconcile the saved per-folder data; blindly reverting the old configs recreates duplicate shares and can sync old deletions. Do not discard the archives until document/Obsidian contents have been reviewed and sync has completed.
2026-10-19 Prowlarr authentication reset: stopped `prowlarr`, removed its single `AuthenticationMethod` entry from `/srv/containers/data/prowlarr/config/config.xml`, and restarted it. It became healthy and saved `AuthenticationMethod=None`; UI root HTTP 200 checked inside the container. User must set a new password and method in the Web UI. Private rollback copy: `/srv/containers/data/prowlarr/rollback/config.xml.before-auth-reset-20261019-211534`. Browser prompt and new credentials not verified.

2026-10-19 FlareSolverr/Prowlarr check: FlareSolverr already runs in the maintained `nexus-media` Compose project, and Prowlarr already has one FlareSolverr proxy configured at `http://192.168.2.9:8191`. Its `flaresolverr` tag is assigned to enabled 1337x only; RuTor and The Pirate Bay are untagged for this proxy. From the Prowlarr container, FlareSolverr's sessions API returned `status=ok`. No installation or configuration change was made; live challenge solving was not checked.

2026-10-19 FlareSolverr 1337x timeout repair: Prowlarr/FlareSolverr connectivity was intact, but 1337x Cloudflare solving timed out. FlareSolverr's former 320 MiB limit showed an OOM kill. Maintained media Compose now sets FlareSolverr memory to 2 GiB and `LANG: en-US`; Prowlarr FlareSolverr proxy timeout is 120 seconds. Scoped FlareSolverr 1337x request and Prowlarr 1337x connection check both returned HTTP 200 (38–40 seconds); final cgroup OOM kills=0. Private rollback: `/var/backups/homelab/flaresolverr-timeout-20261019/` (Compose and proxy snapshots). No other media service recreated; future challenge behavior remains site-dependent.

2026-10-19 qBittorrent peer binding repair: Docker interface order changed so `eth0` was internal proxy-backend (`172.16.11.45`), while pia-vlan (`192.168.2.10`) was `eth1`; qBittorrent had bound its peer port to the internal bridge. API preferences now bind `eth1` and `192.168.2.10`; TCP/UDP 51413 live sockets confirm. DHT recovered from 0 to 213 nodes and one incomplete torrent resumed downloading. Upload slots raised 3→30 and total active torrent slots 5→35, keeping 3 concurrent downloads; 28 completed torrents became active but had no connected leechers/upload at final check. Four ratio-limited torrents remain stopped. Private rollback snapshots: `/var/backups/homelab/qbittorrent-binding-20261019/`. Router/VPN guard unchanged. See kit CHANGELOG for detail.

2026-10-19 Spectrum echo app: `paperclip-spectrum` is a separate outbound iMessage Cloud app at fixed docker-vlan `192.168.5.58` with no published port. Maintained Compose: `/srv/containers/compose/paperclip-spectrum/compose.yaml`; source: `/home/iragonforce/paperclip`; existing private `.env` is mounted read-only and excluded from the image. Running with zero restarts at final check; end-to-end iMessage behavior not verified. No change to deployed Paperclip.

