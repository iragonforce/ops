# Nexus system-performance Grafana dashboard

Date: 2026-11-12
Host: nexus

## Objective

Create a Grafana overview for Nexus CPU, memory,
root filesystem, ZFS filesystems, physical disks and networking.

## Source

hosts/nexus/files/srv/containers/data/grafana/provisioning/dashboards/homelab/nexus-system.json

## Target

/srv/containers/data/grafana/provisioning/dashboards/homelab/nexus-system.json

## Provisioning

Existing Homelab Checkmk file provider.
Existing Prometheus data source UID: 1000.
Dashboard UID: nexus-system-overview.

## Verification

- Dashboard JSON validation: PASS.
- Twelve panels generated.
- No obsolete hostnames in new dashboard.
- Live deployment and Grafana UI verification: PENDING.

## Rollback

This is a new create-only dashboard file.
After checking the deployed digest, remove only the exact
new dashboard JSON target. Preserve all existing dashboards.

## Outstanding

- Guarded deployment of the exact dashboard target.
- Verify Grafana provisioning and panel results.
- Update deployed_sha256 and change record.

## Deployment verification — 2026-11-12

- Source and live SHA256: ba02cb9b5d486ecca90e0bcbb26665643c9c47c2456e7b691ceca3e32c6e0806
- Grafana container can read the dashboard file.
- Grafana health API reports database OK, version 13.2.3.
- File deployment completed without replacing existing dashboards.
- Grafana UI rendering and panel data remain to be confirmed.
