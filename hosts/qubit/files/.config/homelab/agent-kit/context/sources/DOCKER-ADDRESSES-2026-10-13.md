# Nexus Docker addresses and UniFi client names — 2026-10-13

## Configuration

- 52 containers have explicit IP and MAC addresses for all 106 network interfaces.
- Existing live addresses were preserved. VLAN interfaces already had static IPs; private bridge IPs and all MAC addresses are now pinned per network in maintained Compose files.
- 46 VLAN container clients have their exact container names in UniFi, with matching MAC/IP reservations outside DHCP ranges.
- Six backend containers use private Docker bridges and do not appear as separate UniFi clients.
- Address settings also persist in `/var/lib/nexus-restoration/service-overrides.json` for future configuration regeneration.
- No active duplicate container IPs/MACs or conflicting fixed DHCP reservations were found during preparation.

## Wi-Fi and DNS

- `wifi`: native/default VLAN 1.
- `iotNet`: `iot-vlan`, VLAN 4.
- `vpnNet`: `pia-vlan`, VLAN 2, using the existing PIA Switzerland route and independent Media VPN guard.
- Default network DHCP advertises `1.1.1.1`; AdGuard IPv6 DNS advertisements were removed.
- Qubit general DNS uses `1.1.1.1`. Its local `blinkwired.com` resolver uses UDR7 at `192.168.1.1`.
- UDR7 hosts wildcard/apex `blinkwired.com` records pointing to Nexus at `192.168.1.2`. General router upstream resolvers are public Cloudflare/Google addresses.
- Explicit AdGuard Docker DNS settings were replaced with `1.1.1.1`. Existing arr/torrent Quad9 resolvers were retained.
- The proposed extra mobile VLANs were discarded. Their empty Mobile zone, firewall rules, routing policy and VLAN 7 guard were removed. Current Wi-Fi network choices made by the user were preserved.

## Records on Nexus

- Maintained Compose files: `/srv/containers/compose/<stack>/compose.yaml`.
- Address manifest: `/var/lib/nexus-addresses-20261013/addresses.json`.
- Persistent rollout and checkpoints: `/var/lib/nexus-addresses-20261013/rollout.log`, `completed.json`, `plan.json`.
- Verification: `/var/lib/nexus-addresses-20261013/verification.json`.
- Private pre-change Compose files, container inventory and overrides: `/var/lib/nexus-addresses-20261013/`.
- Prior DNS backups: `/var/lib/nexus-dns-20261013/`.
- UniFi name backups and verification: Qubit's `outputs/udr7-network/private/docker-client-names-before-20261013.json` and `docker-client-names-20261013.json`.
- Qubit resolver rollback copy: `/var/db/homelab-dns-20261013/blinkwired.com.before`.

## Rollback

Restore an affected stack's Compose file from `compose-before/<stack>/compose.yaml`, then recreate that service using its original project name from `plan.json`. Keep its existing image and matching application data. Refresh `/usr/local/sbin/nexus-container-routing routes` and `/usr/local/sbin/nexus-access-guard refresh` afterward. Restore matching override entries if configuration regeneration is needed.

Restore UniFi client name/reservation fields from the private before-state by matching MAC address. Restore DNS only as a deliberate separate change; current DNS bypasses AdGuard. Existing DHCP clients may retain old DNS until reconnecting or renewing their lease.

Do not execute `mobile-networks.py` or `mobile-use-existing-vlans.py` to apply current networking: they describe superseded VLAN 6/7 staging. Keep the existing default/IoT/PIA SSID associations.

## Completed verification

- Recreated all 52 containers; checked all 106 live interfaces against the saved IP/MAC plan.
- All 52 containers are running. All 38 configured health checks are healthy; no starting/unhealthy checks remain.
- Images, environment variables and persistent mounts matched the pre-recreation inventory.
- UniFi API confirms all 46 VLAN client names and reservations match the address manifest.
- Dashboard and Home Assistant returned HTTP 200; Grafana and Checkmk returned expected login redirects.
- Existing PIA Media firewall guard remains active at the start of the router forwarding chain.

## Nexus host interface names

The additional clients identified by the user are host macvlan interfaces:

| MAC | UniFi name | IP |
| --- | --- | --- |
| `0a:8d:6d:72:69:16` | `nexus-pia` | `192.168.2.254` |
| `72:9c:74:00:39:10` | `nexus-dns` | `192.168.3.254` |
| `3a:43:da:05:79:d5` | `nexus-iot` | `192.168.4.254` |
| `62:7a:69:1d:9a:b7` | `nexus-docker` | `192.168.5.254` |

Their current MACs are now explicit in `/usr/local/sbin/nexus-vlans` when creating interfaces at boot. No running interface was restarted. The original script is preserved at `/var/lib/nexus-addresses-20261013/nexus-vlans.before`; the address record is `/etc/nexus/host-macvlan-addresses.json`. Preserve these settings if regenerating the VLAN startup script. Restore that script and the private UniFi before-state to roll back this addition.
