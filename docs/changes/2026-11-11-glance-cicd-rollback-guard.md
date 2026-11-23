# Glance CI/CD rollback guard — 2026-11-11

## Objective

Introduce a Git-managed, persistent recovery guard for unconfirmed
Glance blue-green deployments on Nexus.

## Scope

Host: nexus

Components:
- glance-cicd-rollback.py
- glance-cicd-rollback.service
- glance-cicd-rollback.timer

No changes to existing Compose stacks, NPM hosts, Docker networks,
application data or container restoration services.

## Baseline

- Production Blue: glance:8080
- NPM host: 198 (glance.blinkwired.com)
- Other NPM hosts: 174, 191, 195
- Green canary successfully tested and removed
- Blue-green switching and restoration verified
- SQLite recovery checkpoint:
  /var/backups/homelab/glance-cicd-20261111T175307Z

## Guard behavior

- Reads root-only pending deployment state.
- Performs no action before the deadline.
- Requires healthy production Blue containers for rollback.
- Uses the existing protected NPM credentials.
- Restores host 198 to glance:8080 if necessary.
- Verifies API and generated Nginx configuration.
- Records completed recovery.
- Retries failures without discarding pending state.
- Detects conflicting recovery history.

## Verification

Completed:
- Python syntax validation
- systemd unit syntax validation
- Isolated rollback simulation
- Interrupted-history recovery simulation
- Conflicting-history rejection
- Pending-state preservation

Not yet completed:
- Live installed guard validation
- Power-loss and reboot recovery test
- Persistent deployment controller
- End-to-end HTTPS switch validation
- New image digest deployment
- Automatic successful-deployment confirmation

## Rollback

Before removing installed files, disable the rollback timer.

Preserve pending deployment state and recovery history for inspection.
Restore the prior Git revision using the existing deployment workflow.

Remove only deployment targets created by this change and only after
verifying that their installed contents match the recorded sources.

Reload systemd after removing its unit files.

If NPM host 198 is unexpectedly routed to Green, restore the upstream
to glance:8080 through the NPM API and verify both configuration and
application health.

Never overwrite NPM's live SQLite database with the checkpoint while
the application has accepted subsequent writes.

## Deployment status

Installed on Nexus using the Git-managed installer.

Verification:
- All three installed files match their Git source SHA-256 digests.
- File ownership is root:root, with modes 0755/0644/0644.
- systemd service and timer are loaded.
- No-op guard execution succeeded (exit status 0).
- No pending deployment was present.
- Both production Glance containers remained healthy.
- All four NPM hosts remained on glance:8080.

Timer remains disabled and inactive.

Automatic rollback is NOT yet enabled. Integration into
consolidate and deployment-controller testing remain pending.

Follow docs/workflow.md for backup, installer preview, deployment,
verification and final inventory reconciliation.
