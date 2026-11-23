# Measuring reliability without another telemetry service

Use the existing dated change records for the next ten real infrastructure tasks. Do not fabricate a completed cohort from configuration checks. Use the existing `skill-usage` report for observed skill loads; those counts are neither usefulness nor token savings.

For each task record: objective, matching evidence reused, new investigation commands, elapsed active time when observed, input/output tokens if the runtime supplies them, scope additions, changed assets, checks, regressions/rollbacks, and whether the next task found the result without rediscovery. Missing measures stay unknown.

Acceptance for the ten-task cohort:

- 10/10 tasks have objective, affected host, verification, change record and commit linkage.
- 0 secrets in Git, unsolicited skills, new management services or out-of-scope changes.
- 10/10 consequential changes have a usable rollback recorded before deployment.
- At least 9/10 follow-up recall checks find the relevant verified record within three searches.
- Repeated investigation commands decrease relative to the first three comparable tasks; report counts, not an invented percentage target across incomparable tasks.
- Report every regression and rollback. A target of zero is not proof of zero without observed tasks.

Immediate recall checks cover: each host's role/runtime; Nexus Hermes state location; Git source location; legacy sync hazards; backup restoration path; native imported-session provenance; native search availability; MCP duplication policy; and the newest change record. Verify exact paths and source IDs, without sending an LLM task that could execute old instructions.
