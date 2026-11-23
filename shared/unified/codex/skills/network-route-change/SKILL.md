---
name: network-route-change
description: Diagnose or change homelab DNS, VLAN, VPN and public routes with route-specific checks.
---

# Network route changes

Map the affected client, VLAN, DNS path, router policy and application endpoint before changing a route. Preserve management VLAN 1, media VPN and WAN guard, IoT segmentation, fixed Docker addresses, and Thread/IPv6/multicast paths.

Use the scoped UniFi, Cloudflare and Prometheus reads plus native `dig`, `curl` and route inspection. Local split-DNS success does not verify Cloudflare edge or Access login. Verify public paths through the actual edge when that is the task.

Save the targeted before-state and rollback before consequential policy changes. State checks and remaining physical or external validation separately. Do not add formal tests unless asked.
