# Nexus — NetherNetProxy LAN discovery

Date: 2026-11-19
Host: nexus
Status: Deployed and server-side verified

## Objective

Make the existing Minecraft Bedrock Dedicated Server
discoverable from Xbox under LAN Games without custom
DNS, mobile applications, or public port forwarding.

## Deployment

- Project: FlowLabsWorks/NetherNetProxy
- Version: v0.1.0-rc2
- Installation: native systemd service
- Binary: /opt/nethernet-proxy/nethernet-proxy
- Configuration: /etc/nethernet-proxy/config.json
- Service: nethernet-proxy.service
- Service account: nethernet-proxy
- LAN discovery: UDP 7551
- Minecraft target: 192.168.5.5:19132
- Transport: NetherNet
- Server version: 1.26.66, protocol 2225
- Release archive: SHA256 verified
- Build provenance: not independently verified;
  installed GitHub CLI lacked attestation support

## Network

- Nexus LAN: 192.168.1.2
- Minecraft container: 192.168.5.5, VLAN 5
- Xbox observed during test: 192.168.1.181
- Proxy advertises Minecraft on the local LAN
- Xbox joins proxy, then transfers to Minecraft
- Gameplay traffic connects directly to Minecraft
- Production Minecraft container is unchanged
- Existing network policy permitted the tested join

## Validation

- Release checksum verified
- Server /v1/join query succeeded
- Temporary proxy advertised the world
- Xbox reached the actual Minecraft world
- Bidirectional Xbox-to-Minecraft UDP traffic observed
- Persistent systemd service active and enabled
- UDP 7551 listener verified
- Persistent service logged "world announced"
- Live configuration matched the Git-managed source

Permanent-service Xbox join should be verified
separately before treating deployment as accepted.

## Operations

Check service:

    systemctl status nethernet-proxy
    journalctl -u nethernet-proxy -n 50 --no-pager
    ss -lunp 'sport = :7551'

Rollback:

    sudo systemctl disable --now nethernet-proxy

Rollback stops LAN discovery without changing
the Minecraft server or deleting configuration.

To restore:

    sudo systemctl enable --now nethernet-proxy

Updates must be reviewed against the Bedrock
protocol version before replacing the pinned binary.
