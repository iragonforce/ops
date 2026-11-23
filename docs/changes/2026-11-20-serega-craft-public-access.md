# Serega Craft — public Minecraft Bedrock access

Date: 2026-11-20
Host: nexus
Status: Externally tested and operational

## Server identity

- Name: Serega Craft
- Domain: mc.blinkwired.com
- Bedrock server: 1.26.66.1
- World directory: Bedrock level
- Maximum players: 4
- Online authentication: enabled
- Allowlist: enabled
- Resource packs mandatory: false

## Public networking

Cloudflare:
- DNS-only A record: mc.blinkwired.com
- IPv4: 142.198.205.209
- No Cloudflare HTTP proxy or Spectrum

Bell modem:
- Public WAN IPv4: 142.198.205.209
- Forward TCP 19132 to UDR7
- Forward UDP 19140-19149 to UDR7

UDR7:
- Observed Bell-side address: 192.168.100.10
- Forward TCP 19132 to 192.168.5.5:19132
- Forward UDP 19140-19149 to 192.168.5.5
- No external forwarding of UDP 7551

Docker:
- Container: minecraft-bedrock
- Docker VLAN address: 192.168.5.5
- Proxy backend address: 172.16.11.23

Protected environment settings:

    SERVER_NAME=Serega Craft
    TEXTUREPACK_REQUIRED=false
    SERVER_UDP_PORTS=142.198.205.209:19140-19149:19140-19149

The actual protected environment file is not tracked.

## Xbox LAN discovery

NetherNetProxy v0.1.0-rc2 runs through systemd.

- UDP 7551
- Local discovery and transfer
- Xbox connects directly to Minecraft after transfer
- No BedrockConnect DNS required

## Branding

Official Serega Craft image:

    docs/assets/serega-craft-logo.png

Original file:

    /Users/iragonforce/mc-logo.png

This is a branding asset, not a native Bedrock server icon.

## Verification

- Cloudflare DNS resolved to public IPv4
- External TCP /v1/join succeeded over cellular
- Minecraft public UDP configuration verified
- External Minecraft gameplay confirmed
- Xbox LAN discovery and gameplay confirmed
- Minecraft container healthy
- NetherNetProxy active

## Backup and rollback

Configuration backup:

    /var/backups/homelab/minecraft-bedrock/public-udp.SoyQNOgC

Resource-pack policy backup:

    /var/backups/homelab/minecraft-bedrock/resource-packs.yliGTLDF

Server-name backup:

    /var/backups/homelab/minecraft-bedrock/name-change.S6NDRAEY

To revert the public UDP advertisement, restore the
protected environment file from the public-udp backup
and recreate only the minecraft-bedrock Compose service.

Cloudflare and port-forwarding changes can be reversed
independently.

Do not delete world data or authentication state during rollback.
