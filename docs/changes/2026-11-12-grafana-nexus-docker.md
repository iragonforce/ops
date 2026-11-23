# Nexus Docker performance dashboard

Date: 2026-11-12
Host: nexus

## Objective

Create per-container and per-Compose-project CPU, memory,
network, and CPU-throttling views using existing cAdvisor metrics.

## Files

Source: hosts/nexus/files/srv/containers/data/grafana/provisioning/dashboards/homelab/nexus-docker.json
Target: /srv/containers/data/grafana/provisioning/dashboards/homelab/nexus-docker.json
SHA256: 6e063cd6130987605b02c5b4a7769c8829af52b19744ae1cfc3f5ce14e1e50c6

## Data source

Prometheus UID: afgt2mp7n1wxse
Dashboard UID: nexus-docker-containers
Panels: 14

## Query safeguards

- Exclude the cAdvisor host aggregate using name != "".
- Identify containers by cAdvisor name labels.
- Only show selected network interface families.
- Shared network namespace traffic is not independently
  attributable to each application; Gluetun may include
  qBittorrent and other VPN-sharing services.
- Network panels must not be summed as total physical traffic.
- Container disk I/O metrics are disabled in current cAdvisor
  configuration; no disk I/O panels have been invented.

## Validation

- CPU, RAM, network and throttling queries returned data.
- Dashboard JSON structurally validated.
- Source committed; live deployment pending.

## Rollback

New dashboard, create-only deployment.
Remove only the exact dashboard target after checking its digest.
Preserve all existing Grafana dashboards.

## Deployment verification — 2026-11-12

- Guarded installer: SUCCESS, zero conflicts.
- Source and deployed SHA256: 6e063cd6130987605b02c5b4a7769c8829af52b19744ae1cfc3f5ce14e1e50c6
- Dashboard UID: nexus-docker-containers.
- Dashboard panel count: 14.
- Grafana container file access: PASS.
- Grafana health API: PASS, database OK.
- Existing dashboards preserved.
- Grafana UI rendering and panel data verification: PENDING.

## Subsequent work

- Verify panels in Grafana UI.
- Exclude host-network containers from per-container network attribution.
- Investigate qBittorrent application metrics.
- Review Prometheus retention, currently one day.
