# Nexus media VPN audit

2026-10-19, America/Toronto. User requested checking actual PIA VLAN/VPN use. This was a read-only network/service audit; no routing, firewall, Compose or container changes were made.

## Live results

| Service | Primary LAN IP | Network | Observed internet exit |
|---|---|---|---|
| Lidarr | 192.168.2.2 | pia-vlan | Same Swiss VPN exit |
| Prowlarr | 192.168.2.3 | pia-vlan | Same Swiss VPN exit |
| Cleanuparr | 192.168.2.4 | pia-vlan | Same Swiss VPN exit |
| Radarr | 192.168.2.5 | pia-vlan | Same Swiss VPN exit |
| Sonarr | 192.168.2.6 | pia-vlan | Same Swiss VPN exit |
| FlareSolverr | 192.168.2.9 | pia-vlan | Same Swiss VPN exit |
| qBittorrent | 192.168.2.10 | pia-vlan | Same Swiss VPN exit |
| Bazarr | 192.168.2.11 | pia-vlan | Same Swiss VPN exit |
| Jellyfin | 192.168.5.7 | docker-vlan | Regular Canadian WAN |
| Seerr | 192.168.5.45 | docker-vlan | Regular Canadian WAN |

All ten containers were running. Compared maintained media Compose definitions with runtime Docker network membership and IPv4 route selection. Probed HTTPS Cloudflare trace from each container's actual network namespace with host curl through nsenter, avoiding new images or containers. Eight VLAN 2 namespaces reported one common CH exit; Seerr/Jellyfin reported a distinct common CA exit. Native HTTP proxy environment variables were absent in the first eight requested/audited services; application proxy configuration was not exhaustively audited.

All media services also use proxy-backend. Docker reports that bridge as internal, without IPv6 or an internet gateway. It is not an alternate WAN route. VLAN 2 media containers have Quad9 DNS configured; Seerr/Jellyfin have public DNS. Resolver forwarding and DNS leak behavior were not separately packet-captured.

## Router verification

Authenticated to UDR7 through the existing private credential path and validated its SSH host key against Qubit's existing trusted key. No credential or trust changes.

- nexus-media-vpn-guard.service active/running; last process status zero.
- IPv4 FORWARD begins with the VLAN 2 source jump into NEXUS_MEDIA_VPN.
- That chain returns local subnet traffic and traffic through tunovpnc1, then drops other forwarding.
- IPv6 FORWARD begins with the br2 jump into NEXUS_MEDIA_VPN6, which drops forwarding.
- UniFi's VPN mark 0x6a0000 selects table 178.tunovpnc1; its default route and a marked route lookup from qBittorrent select tunovpnc1.
- An unmarked raw ip-route lookup selects the ordinary WAN table; it omits UniFi's packet marking and is not representative of observed media traffic. Live namespace egress and the marked lookup confirmed the VPN path.

No VPN shutdown, forced failover or download interruption was performed. The guard's current rules and service state were checked; an actual VPN-loss exercise was not repeated. No formal tests were added/run.

## Exceptions and next actions

Seerr and Jellyfin are not behind PIA. This is recorded, not a queued instruction to move them. A future request to move either requires updating persistent network/IP/DNS and relevant proxy/application paths while preserving volumes, identities, credentials and service access.

No operational rollback is needed because this audit did not change system configuration.
