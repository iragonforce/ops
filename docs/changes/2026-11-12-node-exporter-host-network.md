# Nexus Node Exporter host-network migration

Date: 2026-11-12
Host: nexus

## Objective

Collect actual Nexus host network metrics instead of
Node Exporter container-network metrics.

## Source files

- hosts/nexus/files/srv/containers/compose/monitoring/compose.yaml
- hosts/nexus/files/srv/containers/data/prometheus/config/prometheus.yml

## Prepared changes

- Node Exporter network_mode: host
- Node Exporter pid: host
- Listener: 172.16.11.1:9100
- Prometheus scrape target: 172.16.11.1:9100
- Instance label remains nexus

## Backup

Repository: iragonforce/backup
Branch: node-exporter-host-network-2026-11-12
Commit: 8c30cd05740d78d753fc10ac3954b6586fb82405

Original configurations, ownership information and
extended ACL snapshots are preserved.

## Validation

- Original live configurations unchanged.
- Docker Compose validation passed.
- Prometheus configuration validation passed.
- Live deployment pending.

## Rollback

Restore original configurations from the verified backup.
Use guarded deployment after checking live digests.
Preserve ownership and extended ACLs.
Recreate only Node Exporter and reload Prometheus.
Verify original exporter connectivity.

## Remaining work

- Guarded deployment
- Node Exporter container recreation
- Prometheus reload
- Verify enp6s0, VLAN and Tailscale metrics
- Update deployment inventory and verification record

## Deployment verification — 2026-11-12

- Guarded deployment: PASS, zero conflicts.
- Compose SHA256: 9dfeb855b35f8e4477355c3082884c26cc1ac776da071b9ad5cc0fd6ecf5b6c0
- Prometheus SHA256: 3341339f88eecd6173c075393503223f8a010fb64c9ff4fd1272584d9d8d231a
- Extended ACL preservation: PASS.
- Node Exporter host network namespace: PASS.
- Physical interface enp6s0 metrics: VERIFIED.
- Prometheus Nexus exporter target: UP.
- Prometheus configuration reload: PASS.
- Monitoring containers: RUNNING.
- Original configurations and ACLs preserved in
  iragonforce/backup branch node-exporter-host-network-2026-11-12,
  commit 8c30cd0.

## Remaining work

- Create Nexus system-performance Grafana dashboard.
- Create Docker container-performance dashboard.
- Investigate Tensor and Qubit exporter connectivity.
