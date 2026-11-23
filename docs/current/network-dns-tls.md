# Homelab DNS and HTTPS

Verified November 17, 2026.

Hosts: nexus, tensor, qubit.

## DNS architecture

Nexus runs CoreDNS using Docker Compose:

`/opt/data/network-alias-dns`

CoreDNS listens on the Nexus LAN and Tailscale addresses
using TCP/UDP ports 53 and 1053.

Port 1053 is also used for step-ca validation.

### DNS records

| Host | LAN | Tailscale |
|---|---|---|
| nexus | 192.168.1.2 | 100.96.255.81 |
| tensor | 192.168.1.3 | 100.114.178.50 |
| qubit | 192.168.1.4 | 100.103.67.56 |

CoreDNS LAN view:

- nexus: 192.168.1.2
- tensor: 192.168.1.3
- qubit: 192.168.1.4

CoreDNS tailnet view:

- nexus: 192.168.1.2
- tensor: 192.168.1.3
- qubit: 100.103.67.56

Search domain: home.arpa.

Public DNS forwards to 192.168.1.1.

Tailscale FQDN queries forward to 100.100.100.100.

## Host resolvers

### Nexus

Nexus uses static ifupdown networking.

Primary DNS: 192.168.1.2
Secondary DNS: 192.168.1.1

Managed configuration:

- /etc/network/interfaces
- /etc/resolv.conf

### Tensor

Tensor uses NetworkManager.

Connection UUID:

e7dad4fd-0230-34ea-b42c-00d3840b465d

Verified properties:

- ipv4.dns: 192.168.1.2, 192.168.1.1
- ipv4.dns-search: home.arpa
- ipv4.ignore-auto-dns: yes

The complete NetworkManager connection profile is excluded
from Git to avoid storing unrelated settings or credentials.

### Qubit

macOS native split DNS:

- /etc/resolver/home.arpa -> 192.168.1.2
- /etc/resolver/tail4e4f0f.ts.net -> 100.100.100.100

Wi-Fi search domain: home.arpa.

All three hosts have Tailscale DNS acceptance disabled.

Qubit was verified on home Wi-Fi and an iPhone hotspot.

## HTTPS architecture

### Nexus

Nginx Proxy Manager remains the existing reverse proxy.

The Homelab step-ca renewal timer remains enabled.

No Caddy instance is required on Nexus.

### Tensor

Caddy listens on:

- 192.168.1.3:443
- 127.0.1.1:443

Upstream application:

http://127.0.0.1:9090

Caddy uses the existing step-ca ACME directory:

https://192.168.1.2:9000/acme/acme/directory

Certificate validation uses TLS-ALPN-01.

Caddy manages certificate issuance and renewal automatically.

Persistent Caddy state: /var/lib/caddy

The systemd service is enabled and ordered after
network-online.target.

A Git-managed override configures:

- Restart=on-failure
- RestartSec=5s

Existing Tailscale Serve remains on Tensor's tailnet address.

### CA trust

Homelab root certificate SHA-256 (DER):

d177228fbc6735a2b3c1d965b687d1097ef56dbafae0bcd07cc4012b8f90cc2b

Qubit trusts this root through the macOS System Keychain.

The CA certificate is public.
Private keys and Caddy ACME account state are excluded from Git.

## Verified

- Nexus CoreDNS is operational.
- LAN and remote DNS resolution passed.
- Tensor and Nexus host resolvers use CoreDNS.
- Qubit split DNS works locally and remotely.
- Tensor HTTPS returns HTTP 200 with TLS verification 0.
- tensor.home.arpa also returns HTTPS 200.
- Tailscale Serve remains operational.
- Caddy successfully obtained both certificates from step-ca.
- Caddy is enabled and active.
- Nexus NPM renewal timer is enabled and operational.

## Remaining validation

- Observe Caddy's first automatic renewal.
- Verify Caddy and DNS after Tensor reboots.
- Verify Qubit dock Ethernet DNS behavior.
- Verify NFS reconnection during network transitions.

## Known limitations

Nexus currently resolves qubit to its LAN address even
when Qubit is roaming.

Use qubit.tail4e4f0f.ts.net when Nexus needs to reach
Qubit remotely.

Private DNS depends on Nexus and its CoreDNS service.
The gateway DNS fallback primarily provides public resolution.

## Recovery

Nexus DNS backup:

/var/backups/homelab/nexus-dns-20261117-214601

Tensor DNS backup:

/var/backups/homelab/tensor-dns-20261117-212607

Tensor Caddy backup:

/var/backups/homelab/tensor-caddy-20261117-221244

Restore configuration through the established guarded
deployment workflow.

Inspect live target digests before overwriting files.

Preserve /var/lib/caddy during rollback because it contains
ACME account state, certificates, and private keys.

Do not remove Tailscale subnet routes during DNS rollback.
