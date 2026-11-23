# Nexus Steam Headless preparation

Date: 2026-11-19

## Objective

Prepare Steam Headless v2 with Sunshine for remote gaming
using Nexus's AMD Radeon RX 6600.

## Storage

- bulk/steam -> /mnt/bulk/steam -> /mnt/games
- fast/steam -> /mnt/fast/steam -> persistent state

## Deployment

- Project/container: steam
- Source: hosts/nexus/files/srv/containers/compose/steam/compose.yaml
- Installed: /srv/containers/compose/steam/compose.yaml
- Network: existing docker-vlan, 192.168.5.59 (not activated; DHCP and access checks pending)
- Remote access: Tailscale and Moonlight

## Verified

- RX 6600 supports Vulkan, H.264 and HEVC encoding
- ZFS datasets mounted
- Docker and Compose available
- No conflicting gaming listeners at preflight
- Compose source and installed copy validated

## Pending

- Pin container image digest
- Confirm host firewall restrictions
- Start container and verify hardware acceleration
- Complete Steam and Sunshine enrollment
- Verify Moonlight streaming and controller input
- Check Jellyfin regression
- Update current infrastructure inventories

## Rollback

Do not destroy either ZFS dataset.
Before startup, removing the installed Compose file
and reverting the Git commit restores the configuration
baseline. Preserve all Steam runtime data.

## Macvlan preparation

- Reuse existing Docker macvlan network `docker-vlan`.
- Assign Steam candidate address `192.168.5.59/24`.
- Preserve Nexus's existing VLAN 5 host shim.
- Existing Tailscale advertisement is `192.168.0.0/23`.
- Future Steam route: `192.168.5.59/32`.
- Confirm address exclusion from UDR7 DHCP before startup.
- Check VLAN 5 access control and Tailscale route approval.
- Container remains stopped.

## Tailscale route advertisement

- Existing advertisement preserved: `192.168.0.0/23`.
- Steam-specific route added: `192.168.5.59/32`.
- Applied using `tailscale set`.
- Tailnet route approval and client connectivity remain unverified.
- Steam container remains stopped.
- Rollback: `sudo tailscale set --advertise-routes=192.168.0.0/23`.

## Immutable image selection

- Image: `josh5/steam-headless:2@sha256:c60f4d7243a4d94515f722441fff90b752413bf6a45bb221c9a4ed55bc4d9108`
- Registry digest verified before deployment.
- Container has not been started.
- Rollback: restore the previous Compose revision from Git.
