# Private DNS and HTTPS deployment

Date: November 17, 2026.

Hosts: nexus, tensor, qubit.

## Objective

Provide consistent private hostnames across LAN and Tailscale,
preserve existing services, and automate HTTPS certificates.

## Implemented

- CoreDNS deployed on Nexus.
- Nexus static resolver configured.
- Tensor NetworkManager DNS configured.
- Qubit native split DNS configured.
- Tensor Caddy deployed with step-ca ACME.
- Tensor Caddy startup retry policy configured.
- Homelab CA trusted on Qubit.
- Existing Nexus NPM renewal preserved.
- Git-managed configuration adopted.
- Eleven deployment mappings registered.

## Verified

- Private DNS resolution on all three hosts.
- Remote Qubit DNS over Tailscale.
- Public DNS resolution.
- Tensor HTTPS HTTP 200 and TLS verification 0.
- Existing Tailscale Serve HTTP 200.
- Initial ACME certificate issuance.
- Caddy enabled and active.
- Nexus NPM renewal timer healthy.

## Outstanding

- First automatic Caddy renewal.
- Full Tensor reboot test.
- Qubit dock Ethernet test.
- NFS roaming/reconnection verification.

## Rollback

See docs/current/network-dns-tls.md for backup locations,
operational dependencies, and recovery instructions.
