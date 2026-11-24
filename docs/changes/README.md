# Change records

Authoritative location: host `~/ops/docs/changes`; main Nexus Hermes `/opt/data/workspace/ops/docs/changes`, in public `iragonforce/ops`. Original private history remains in `iragonforce/ops-private` and Hermes `/opt/data/workspace/ops-private`. Copies of this pointer in legacy kit locations are not separate changelogs. Their prior contents remain in private history and backup branch `unified-infra-2026-11-06`.

Use Git commits for routine history. Add a concise dated record when an operational decision, verification limit, recurring failure or rollback needs explanation. Its containing Git commit supplies the exact revision; include related implementation commit IDs when a record spans commits.

Required fields: original objective; affected host/project/files/services; actual changes; verification commands and outcomes; unresolved/physical acceptance; targeted rollback and private recovery references; deployment status; Git/push status.

Recent records:

- [Hermes public ops cutover](2026-11-23-hermes-public-ops-cutover.md)
- [Native knowledge and capability consolidation](2026-11-06-knowledge.md)
- [Source adoption and deployment](2026-11-06-source-adoption.md)
- [2026-11-06 inventory and ownership baseline](2026-11-06-baseline.md)
