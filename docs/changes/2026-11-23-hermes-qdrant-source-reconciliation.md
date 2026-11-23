# Hermes Qdrant Compose source reconciliation

Date: 2026-11-23
Host: nexus
Branch: consolidate

## Verified source change

The Hermes Git checkout was updated to attach Hermes
to the external qdrant_default Docker network.

The effective Compose model differs from the previous
Git HEAD only in the network declaration and Hermes
network attachment.

The running Hermes container is already connected
to qdrant_default.

## Runtime-specific differences

The deployed Compose additionally specifies:

- A custom Hermes image with a quota5 test suffix.
- HERMES_QUOTA_TEST_FILE.

Both are present in the running container.

Their permanence has not been established. They were
not incorporated into the canonical Git configuration
during this reconciliation.

The deployed Compose configuration was not overwritten.

## Operational impact

No Docker restart, recreation, network modification,
or deployment was performed.

The deployed Compose file remains different from Git
until the runtime-specific test configuration is resolved.

## Recovery

The previous committed Hermes source is recoverable
from Git history.

The running and deployed Hermes configurations were
left unchanged.
