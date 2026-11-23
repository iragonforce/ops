# Paperclip connection identity repair

2026-10-18, America/Toronto.

## Cause

The migration setup added credential-bearing default organization grants to Homelab Knowledge, UniFi and Prometheus but left their original empty organization grants active. Paperclip's native connection-intent resolver requires one unambiguous active identity, even when a separate operator broker probe succeeds. The four migrated connections also had profile permissions but no agent installation targets, so their availability was incomplete.

## Changes

- Revoked only the three empty, non-default organization grants. Working default grants and their existing encrypted credential references were preserved.
- Added agent installation targets for coordinator, Hermes and Tensor Ollama to Homelab Knowledge, UniFi, Prometheus and Context7, preserving existing targets and existing scoped tool profiles.
- Granted service UID 10000 read access only to the staged history.sqlite file after saving its ACL. The public directory traversal ACL from the previous change remains. No pool-wide ownership or permission changes.
- Refreshed the Knowledge catalog and health after repairing access.

## Checks

- Knowledge now has one active organization identity.
- Coordinator's effective connections include Knowledge and its four permitted tools.
- The actual connection-intent service selected the expected connection for all four migrated services, using coordinator and the existing responsible administrator.
- Coordinator's history_search succeeded through the Paperclip broker; decision allowed, result returned without error.
- No credentials were rotated, services restarted, agent model runs triggered, external messages sent or formal tests run.

Refresh the browser and retry the existing access request. Its previous transaction was rolled back when the ambiguous identity check failed; the failed UI attempt is not evidence of a credential problem.

## Rollback

Before-state and installation targets: `/srv/containers/data/paperclip/recovery/identity-20261018`. Restore prior targetType/targetId lists through the supported connection-installs API. Revoked grants are retained in the audit trail; recreating empty duplicate grants would recreate the ambiguity. Restore the saved index ACL with setfacl --restore if needed. Full API results remain in the private migration directory. Temporary maintenance credentials were revoked after each operation.
