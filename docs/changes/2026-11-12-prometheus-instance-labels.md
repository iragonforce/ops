# Prometheus instance-label normalization

Date: 2026-11-12
Host: nexus
Service: Prometheus

## Objective
Normalize instance labels to nexus, tensor and qubit.

## Source and deployment
Source: hosts/nexus/files/srv/containers/data/prometheus/config/prometheus.yml
Target: /srv/containers/data/prometheus/config/prometheus.yml
Original backup: docs/changes/prometheus-before-instance-rename-20261112T142815Z.yml
Original SHA256: fb2b443e59ed520d14ed55693deed8ed18c51ad6cedfd683d3df4c7be2e174dc

## Verification
Source configuration passed promtool validation.
Original Git backup matches the live configuration.
Deployment and live verification are pending.

## Rollback
Restore the original backup through the guarded installer.
Reload Prometheus and verify scrape targets.
Preserve and restore the original extended ACLs.

## Outstanding
Back up selected originals to iragonforce/backup before deployment.
Account for extended ACLs during atomic replacement.
Update deployed_sha256 after successful deployment.
Tensor and Qubit exporter connectivity remains unresolved.

## Deployment verification — 2026-11-12

- Guarded installer: applied, zero conflicts.
- Deployed SHA256: b5a08ca6e2793216099fe3a5929cc726f9ad1fec8399b4df9caf84a812fdfe42
- Original ownership and extended ACLs restored and verified.
- Prometheus configuration validation: PASS.
- Prometheus reload: successful.
- nexus: three scrape targets UP.
- tensor: one target DOWN; connectivity unresolved.
- qubit: one target DOWN; connectivity unresolved.
- Obsolete instance labels: zero.
- Rollback baseline and ACL snapshot preserved in iragonforce/backup, branch prometheus-instance-labels-2026-11-12, commit f4b5314.
