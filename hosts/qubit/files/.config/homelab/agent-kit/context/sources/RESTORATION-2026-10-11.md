# Nexus Debian restoration — 2026-10-11

## Current host

Follow-up configuration and validation are recorded in [FOLLOWUP-2026-10-11.md](FOLLOWUP-2026-10-11.md). The follow-up retired five containers, completed Qubit NFS mounts/recovery, added SMB and SMART schedules, configured logging/tmux, and restored the original GitHub key. It supersedes earlier pending items below.

Debian 13.7, hostname `nexus`, administrator `iragonforce` (UID/GID 1000).
Management remains `192.168.1.2/24` on `enp6s0` (MAC `98:03:8e:a7:b7:43`), gateway `192.168.1.1`, timezone `America/Toronto`.
Qubit is `192.168.1.4` / Tailscale `100.103.67.56`. Tensor is `192.168.1.3` / `100.114.178.50`; offline during restoration.
Nexus now uses host Tailscale `100.96.255.81`; the old TrueNAS address is obsolete.

## Completed changes

- Imported only bulk and fast after forced read-only inspections with an alternate root. Verified serials, GUIDs, pool health, archive snapshot coverage and EFI checksums. Normal imports and boot unlock are configured. Former boot-pool was never imported; no disks were formatted and no pool features upgraded.
- Archive contains 106 received boot datasets / 173 snapshots and 33 received fast datasets / 95 snapshots. All 33 fast preinstall snapshot GUIDs matched. Of 95 source fast snapshots, 94 matched received GUIDs; the unmatched `fast@snap-20261010-1200` was created after the archive. The completed Oct 8 bulk scrub reported zero repairs/errors.
- Bulk HDD serial `ZYD0L4FN`, GUID `2119212528721849216`; fast NVMe serial `S7U6NJ0Y233332T`, GUID `12978747864126690130`. Device letters changed again across the reboot: the follow-up observed bulk as sdb and the Debian boot SSD as sda. Always use serials/GUIDs.
- Debian boot SSD serial is `P210DDBA2504093106`; ext4 root UUID is `fb717058-4506-48be-a540-5135f83ce533`. GRUB timeout is zero. Resume is disabled and swap uses the boot SSD's persistent by-id partition path. Qubit/Tensor user settings, shell plugins, fastfetch login and Ghostty terminfo were prepared earlier and retained.
- Boot import uses `/etc/zfs/zpool.cache` containing bulk and fast only. Scan import remains masked. `nexus-zfs-unlock.service` loads bulk's private key from `/etc/zfs/keys/bulk.key` before mounts.
- Held original snapshots `bulk@nexus-before-restore-20261011` and `fast@nexus-before-restore-20261011` with hold tag `nexus-restoration`.
- Moved 14 bulk entries atomically within their filesystem; checked destination inode identity. Inventory covers 1,489,183 files, 240 directories, approximately 2.10 TB logical data. No hard-link groups were found in the shared trees. Media and downloads remain on the same bulk filesystem.
- Initial restoration granted UID 1000 access on `/mnt/bulk/data`. The follow-up also grants it access to the specifically selected shared user directories on fast, after holding a pre-change snapshot. App-reference and migration archive permissions remain intact. The full recursive metadata inventory followed the atomic moves; original metadata remains recoverable from the held snapshot. The initial ACL text dump was interrupted and is partial; do not use it as a complete rollback source.
- Created `fast/debian-live` as a clone mounted at `/srv/containers/data`, providing writable application copies while retaining original `/mnt/fast`. Created `fast/debian-builds` at `/srv/containers/builds` for recovered build sources.
- Compose files live under `/srv/containers/compose/<stack>`; private environment files and credentials under `/etc/nexus/secrets/<stack>`. Bind mounts reject nonexistent source directories. Docker images and containerd storage remain on the ext4 boot SSD.
- Installed Java 21, .NET 10 SDK, SBCL, Python tooling, GCC/G++, Clang, CMake, Ninja, debuggers, storage/network/ACL/archive/monitoring tools and QEMU/libvirt/OVMF. KVM access works; no virtual machine created.
- Configured bounded Docker logs, persistent stack units, mount checks, VLAN dependencies, restart policies and recurring health checks where verified probes are supported.
- Rebuilt Telegram, Journal, Homelable, MakersVault and Webhook Notify from recovered sources. Build contexts exclude credentials and runtime databases. Telegram uses a pinned Python base and dependency lockfile; its read-only `/commands` endpoint passed and polling initialized.
- Upgraded Authentik through 2026.2.7, 2026.5.7 and 2026.8.3 with matching snapshots and database dumps. Jellyfin upgraded from 10.11.8 to 12.2 after checking username collisions and preserving its old Webhook plugin outside the active plugin directory. Journal uses maintained Node 22 because its archived native SQLite dependency fails on Node 24. Homelable's omitted Python db source package was recovered; its MCP SDK is pinned to compatible stable v1.
- Updated proxy destinations to container DNS aliases and repaired saved Nginx proxy files. Updated local Prometheus scrape targets from old TrueNAS aliases to Nexus exporters. External qubit/tensor exporter checks remain pending.
- Repaired Seerr's Jellyfin/Sonarr/Radarr targets, Grafana's Prometheus datasource and Glance's stale local service addresses. Saved integration API credentials passed read-only authenticated checks. Home Assistant trusts the recorded private NPM proxy address `172.30.240.251` plus the proxy bridge. Local container telemetry covers all 55 containers.
- Home Assistant 2026.10 uses `.storage/http` for HTTP settings; its migrated stable proxy list was updated while stopped and its ignored YAML HTTP block removed. Fixed the custom `home.blinkwired.com` proxy file's hardcoded backend with Docker DNS. All 28 restored HTTPS proxy routes passed origin TLS verification and returned successful responses or expected login redirects. Origin wildcard certificate expires 2027-01-04.
- Installed official Webhook plugin 22.0.0.0 compatible with Jellyfin 12, verifying the vendor checksum and preserving its previous version/configuration. Completed a full media library scan. Maintenance API calls use the supported Authorization header; legacy token headers remain disabled.
- Reboot validation passed: pool import/unlock, mounts, VLANs, Docker, NFS and all deployed services returned. No failed systemd units remained. Firmware 8.258s, loader 2.298s, kernel 5.659s, userspace 2m18.208s; the userspace target waits for container readiness. The running kernel includes both GPT auto-generator disable flags.
- Preserved Zigbee and Thread radios by USB identity. Zigbee maps to `/dev/zigbee`; Thread's backbone is `iot0`. Enabled per-endpoint IPv6 link-local/SLAAC on Home Assistant, Matter and OTBR. No radios flashed and no pairing keys replaced.
- Created private PostgreSQL custom-format dumps for Authentik, n8n and Home Assistant. Validated with `pg_restore --list` and SHA256. Host configuration including private credentials is archived privately under `/mnt/bulk/backups/host/nexus-20261011`.
- Copied current proxy certificates/configuration, NPM/Grafana SQLite backups, Home Assistant storage/YAML, Zigbee, Glance and Seerr settings privately to `/mnt/bulk/backups/services/settings-20261011`, with verified checksums. Held final snapshots `fast/debian-live@restored-20261011` and `fast/debian-builds@restored-20261011`.
- AdGuard's saved Quad9 encrypted upstream reset connections during final checks. Retained that primary and added `https://cloudflare-dns.com/dns-query` as an encrypted fallback. Updated the saved `*.blinkwired.com` DNS rewrite from the old management address to NPM's VLAN 5 address `192.168.5.20`; cross-host access awaits router routes. Saved the prior configuration privately under `/var/lib/nexus-restoration/references-before/AdGuardHome-before-dns-fallback.yaml`; stop AdGuard, restore that file to its recorded active configuration path and restart AdGuard to roll back. Filtering, allowed clients and management DNS settings remain as recorded.
- Corrected Nexus's qubit SSH address to 192.168.1.4 and pinned qubit's independently read host key. Nexus-to-qubit key authentication passed. Tensor checks remain pending.

### Historical preparation versus this restoration

Earlier runbook statements saying no changes had been made describe the initial read-only inspection phase. They do not describe this implementation phase. The completed changes above and generated records below are the current status. Previously prepared TrueNAS replication copies, EFI image and inventories remain reference/recovery material.

## Layout

| Path | Role |
|---|---|
| `/mnt/bulk/data/media` | Shared media and TTS output |
| `/mnt/bulk/data/downloads` | Shared downloads/torrent data |
| `/mnt/bulk/data/documents` | Shared documents/Google Drive |
| `/mnt/bulk/data/projects` | Shared models/projects/output |
| `/mnt/bulk/backups/{host,services,databases}` | Private recovery material |
| `/mnt/bulk/legacy` | Unclassified bulk entries |
| `/mnt/bulk/debian-migration` | Preserved TrueNAS reference archive |
| `/srv/containers/data` | Writable app copies on fast |
| `/srv/containers/builds` | Recovered build sources on fast |
| `/srv/containers/compose` | Maintained host Compose configuration |
| `/etc/nexus/secrets` | Private runtime credentials |

Original fast app files and legacy TrueNAS app datasets remain available as references. Selected shared user directories received administrator ACL access in the follow-up. Do not delete original files or received migration datasets without an explicit cleanup request.

## Network assignments and pending router work

VLAN links use parent `enp6s0`; management remains on the untagged LAN. The chosen host shims are:

| VLAN | Docker network | Host shim | Expected gateway |
|---:|---|---|---|
| 2 | pia-vlan | 192.168.2.254 | 192.168.2.1 |
| 3 | adguard-vlan | 192.168.3.254 | 192.168.3.1 |
| 4 | iot-vlan | 192.168.4.254 | 192.168.4.1 |
| 5 | docker-vlan | 192.168.5.254 | 192.168.5.1 |

Initial ARP conflict probes returned no conflicts; no VLAN gateways replied. The user elected to reconfigure the router later. Reserve all recorded static addresses outside DHCP pools and configure the trunk before treating cross-host VLAN access as validated. No new service is published on management VLAN 1.

Public applications have their assigned VLAN endpoint plus a private proxy bridge. Database/backend bridges are internal. Non-torrent applications have outbound NAT through `nexus-egress` while router work is pending. VLAN 2 applications have no NAT egress bridge; qBittorrent remains stopped behind profile `vpn-verified`.

Cloudflared's remotely managed origin still points to `http://192.168.1.2:30021`. A source-specific NAT compatibility rule translates only Cloudflared's private source `172.30.240.250` to NPM `172.30.240.251:80`; there is no host listener on 30021. `nexus-tunnel-compat.service` persists this rule. Replace it once the tunnel origin is updated, after testing; rollback is its saved Compose and dedicated nft table removal. Original SSH ingress also remains in the remotely managed tunnel; review it when reconfiguring Cloudflare.

OTBR retains local IPv6 `fd00:4::7/64` on `iot0`. Router IPv6/multicast and real paired Matter/Thread devices require validation after network reconfiguration.

## NFS

Exports include `/srv/nfs/{media,downloads,documents,projects,bulk,fast}` with NFSv4 pseudoroot `/srv/nfs`. Bulk covers shared `/mnt/bulk/data`; fast covers `/mnt/fast/shared` and its selected user-directory binds. Clients: qubit and tensor's verified LAN/Tailscale addresses. RW, synchronous, all_squash, anonuid/anongid 1000. App databases, secrets, backups and migration archive are excluded.

NFSv3/v4 enabled; v2 disabled. Ports: RPC111, NFS2049, mountd20048, statd32765/out32766, lockd32767. Dedicated nft rules limit these to approved clients. Unauthorized localhost NFSv3 mount was denied. On macOS use `showmount -3 -e 192.168.1.2`; the default showmount protocol request fails because v2 is disabled.

Qubit mounts both shared roots through `100.96.255.81`, using a LaunchDaemon and hard NFS mounts. Real write/read/rename/delete checks passed on both. A write recovered after a temporary transport block without remounting. Finder paths are `/Users/nexus/bulk` and `/Users/nexus/fast`, linked from `~/Nexus Storage`. Tensor validation remains pending while offline. See the follow-up for configuration, recovery behavior and rollback.

## Required human checkpoints and documented exceptions

- Termix and guacd were retired at the user's request; the previous Termix sign-in/upgrade checkpoint is canceled. Their saved configuration/data/images remain available for rollback.
- Verify router trunk, DHCP exclusions, gateways, DNS and cross-VLAN policy. Addresses were chosen and recorded at user direction; router configuration remains deferred.
- Verify VPN isolation before enabling qBittorrent. Do not remove its profile or start torrent activity merely because other arr services work.
- Validate tensor NFS/SSH when online. Qubit NFS write and recovery checks passed during the follow-up.
- Verify authenticated application logins, media playback/transcoding, Zigbee devices, Matter/Thread pairing and proxy authorization flows. Public requests returned HTTP403 through Cloudflare; local application responses passed, but authenticated public routes are not claimed validated.
- Baikal's latest published stable vendor image is 0.10.1; upstream 0.12.1 is not published by that vendor. Matter retains final Python stable 8.1.2; the replacement MatterJS server is beta. Lidarr's published stable 3.1.0 is older than the archived 3.1.2, so no data downgrade was attempted.
- Netbootxyz, OTBR, VERT/VERTd and the 3D printer MCP retain archived digests where a matching stable versioned vendor image could not be verified. Nightly/main builds were not substituted as stable upgrades. Original image retention records may contain superseded choices; current Compose and final image table are authoritative.
- Hermes retains references to previously stopped MCP helpers and the removed TrueNAS API. Those optional tool connections are parked; gateway health passed. Restore or replace those helpers only when their workloads are selected. Existing previously stopped services remain excluded.
- The old standalone Tailscale container and Jellyfin LAN forwarding helper were intentionally replaced by host Tailscale and direct proxy routing. Previously stopped applications remain excluded except the explicitly requested Telegram.
- Jellyfin's required full library scan completed. Actual playback/transcoding remains a human validation checkpoint; preserved original data allows rollback.

## Validation and recovery commands

Run on Nexus:

```bash
sudo python3 /root/nexus-restoration/validate-services.py
sudo zpool status bulk fast
sudo systemctl --failed
sudo exportfs -v
```

State and checkpoints: `/var/lib/nexus-restoration` (private). Logs: `/var/log/nexus-restoration` (private). Final validation JSON records exact containers, image digests, mount sources and HTTP results. A container reported as running without a configured Docker healthcheck is not automatically proof of application correctness.

### Rollback before consequential changes

1. Read current records and saved configuration before editing. Verify disk serial/GUID, mounts, pool health and relevant archive checksums. Stop if identity, integrity or feature compatibility is uncertain.
2. Before networking edits, save `/etc/network/interfaces`, Nexus scripts and nft rules; keep management SSH open and prepare console access. Disable only the changed dedicated unit/table when rolling back. Do not flush unrelated firewall rules.
3. Before shared-data moves/access changes, preserve the mapping and held bulk snapshots. Restore ACLs/owners from the snapshot or revert individual mapped directory names after stopping clients/services. Never roll back the entire bulk pool: it also holds the archive and new backups.
4. Before app upgrades, save Compose, current image digest, secrets privately, a matching application-data snapshot/copy and a database dump. Stop affected services. To restore one service from the shared `fast/debian-live` snapshot, clone the selected snapshot to a temporary recovery dataset and copy only that service's tree with ACLs/xattrs/ownership/hard links preserved. Use its old image with matching old data. Do not roll back the entire active dataset while other services use it.
5. Before database major changes, dump/restore into a new data directory or use the vendor's documented upgrade tooling against copied data. PostgreSQL remains major 18 here; never attach a different major to these directories.
6. Keep originals, held snapshots, prior images, database copies and migration references until cleanup is explicitly requested. Never format/repartition/recreate/upgrade ZFS pools as part of this runbook.
7. Before rerunning a restoration script, inspect it. Several scripts are one-time phase operations, not idempotent installers. In particular, do not rerun the atomic organizer, initial ACL inventory, source preparations or storage baseline writer blindly. Normal validation scripts are read-only apart from writing derived reports.

## Documentation consulted

- [Docker macvlan and endpoint IPv6](https://docs.docker.com/engine/network/drivers/macvlan/)
- [Docker daemon and containerd storage](https://docs.docker.com/engine/daemon/)
- [.NET on Debian](https://learn.microsoft.com/en-us/dotnet/core/install/linux-debian?tabs=dotnet10)
- [Authentik upgrade sequence](https://docs.goauthentik.io/install-config/upgrade)
- [Jellyfin 12 migration](https://jellyfin.org/posts/jellyfin-release-12.0/)
- [Termix update checkpoint](https://docs.termix.site/install/updating/)
- [MCP SDK migration](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/migration.md)
- [Home Assistant HTTP configuration migration](https://www.home-assistant.io/integrations/http/)
- [Quad9 resolver addresses](https://docs.quad9.net/services/)
- [Cloudflare encrypted DNS wire format](https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/dns-wireformat/)

## Generated final records

The tables below are generated from the installed system, not from proposed configuration.
