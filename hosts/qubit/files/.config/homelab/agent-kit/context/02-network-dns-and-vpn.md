# Network, DNS and VPN

2026-10-19 latest media update: UDR7 OpenVPN Toronto is `tunovpnc3`. UniFi left its marked policy table 178 without a default route after the profile change; the guard still allowed retired `tunovpnc2`, so media traffic was blocked without WAN fallback. The guard now allows only `tunovpnc3` and reconciles a missing table-178 tunnel default while the tunnel has an IPv4 address. qBittorrent and Prowlarr container HTTPS and Toronto geolocation succeeded; the guard's IPv4/IPv6 drops remain. See CHANGELOG for root-only UDR7 rollback files. Future VPN profile switches may rename the interface again; inspect the live tunnel, policy table and guard together.

2026-10-19 later update: the active UDR7 media tunnel is `tunovpnc2` with a Canadian exit, as requested by the user. The independent guard now permits only that tunnel for VLAN 2 internet forwarding; its final IPv4 DROP and IPv6 DROP remain active. qBittorrent and Prowlarr namespace egress both returned Canada, and qBittorrent resumed download/upload after reannounce. Rollback copies and checks are in the 2026-10-19 CHANGELOG entry. If UniFi renumbers the VPN interface again, inspect the live tunnel and guard together; preserve fail-closed behavior.

2026-10-19 Qubit–Tensor direct Thunderbolt link: Qubit Bridge `10.0.0.1/30`, Tensor `thunderbolt-link` `10.0.0.2/30`, no default gateway. Qubit `tensor-tb` SSH alias targets only this link and pins the existing Tensor host key. After initial carrier cycling and a brief successful direct connection, a high-load run stalled with Tensor ASM4242 config-space timeouts. Direct traffic is currently unusable. Tensor's second USB4 port was not detected after a controller reset; a fresh replug after the reset is pending confirmation. See [QUBIT-TENSOR-THUNDERBOLT-2026-10-19.md](sources/QUBIT-TENSOR-THUNDERBOLT-2026-10-19.md).

2026-10-19 live media audit: Prowlarr, Radarr, Sonarr, Lidarr, Bazarr, Cleanuparr, qBittorrent and FlareSolverr use VLAN 2 and showed the same Swiss VPN exit from their actual network namespaces. Seerr and Jellyfin use VLAN 5 and showed regular Canadian WAN egress. UDR7's independent IPv4/IPv6 guard was active with the expected first-position rules; marked policy lookup selected tunovpnc1. No forced VPN-loss exercise or networking changes. Details: [NEXUS-MEDIA-VPN-AUDIT-2026-10-19.md](sources/NEXUS-MEDIA-VPN-AUDIT-2026-10-19.md). Exceptions are findings, not queued migration actions.

## Recorded topology and choices

Bell gateway `192.168.100.1` feeds UDR7's WAN. The user initially chose WAN `192.168.100.10`; the 2026-10-12 live record observed DHCP `.11`. Treat the WAN address as dynamic and inspect it rather than asserting `.10` is current.

| VLAN | Network | Purpose |
|---|---|---|
| 1 | 192.168.1.0/24, default-vlan | Management hosts |
| 2 | 192.168.2.0/24, pia-vlan | VPN media workloads; vpnNet Wi-Fi |
| 3 | 192.168.3.0/24, adguard-vlan | Existing AdGuard service; currently not selected as DNS |
| 4 | 192.168.4.0/24, iot-vlan | Home Assistant, MQTT, radios; iotNet |
| 5 | 192.168.5.0/24, docker-vlan | General application services |

Gateways are `.1` on each subnet. The recorded DHCP ranges are `.100–.199`, with 86400-second leases. Inspect current reservations before allocating. Docker service IPs and MACs were persisted in maintained Compose configuration; current mappings are in the live inventory and `sources/DOCKER-ADDRESSES-2026-10-13.md`.

The user's final Wi-Fi choice is `wifi` on the native/default network, `iotNet` on VLAN 4, and renamed `vpnNet` on VLAN 2. No extra mobile VLANs are wanted. Do not copy a Wi-Fi password into this pack.

## DNS — latest user choice

AdGuard must not be the general resolver. Earlier 2026-10-12 instructions making it sole DNS are superseded. Qubit general DNS is `1.1.1.1`; its per-domain macOS resolvers send `homelab.lan` and local `blinkwired.com` lookups to UDR7. Linux hosts use UDR7 for local names. Verify current DHCP/public DNS configuration when changing networks.

An iPhone DNS profile pointing at AdGuard prevented tailnet name resolution; the user identified and corrected it. Do not reinstate that profile. MagicDNS suffix is `tail4e4f0f.ts.net`.

LAN split DNS and a successful local `blinkwired.com` request do not prove public internet access. Public service paths use Cloudflare → cloudflared → Nginx Proxy Manager → application, sometimes protected by Cloudflare Access. Apex dashboard publication was explicitly deferred when the token lacked tunnel/Access permissions; do not assume it was completed.

## Media VPN

The arr stack, FlareSolverr and qBittorrent route through UDR7's media OpenVPN client, currently exiting in Toronto, Canada. VLAN 2 is the policy-route source; vpnNet also uses that VLAN. qBittorrent is `192.168.2.10:30200` with peer port 51413 and UPnP disabled.

Independent UDR7 guard scripts live under `/data/nexus-media-vpn/`; service `nexus-media-vpn-guard.service` permits media internet forwarding only through the tunnel and drops media IPv6 forwarding. Existing inter-zone firewall policy remains in force. Controlled VPN-loss checks passed on 2026-10-12. Do not repeat outage tests or interrupt downloads just to load context.

Media public DNS was set to Quad9 within the VPN namespaces. Do not substitute host/NAT DNS that could route outside the VPN. Inspect each container's route: interface names differ.

IPv6, Thread OMR routes, mDNS and host macvlan shims have existing configuration. Do not broadly disable IPv6/multicast or reset UniFi firewall/Serve configuration to resolve an unrelated issue.
