# Hermes completed-compaction Qdrant memory

Date: 2026-11-23. Objective: safely capture durable findings from the default Hermes profile's completed compactions into the existing `qdrant_memory` collection as `hermes_session`, then make them retrievable in future sessions without a second provider or scheduler.

## Source and scope

- Public source: `shared/scripts/hermes-compaction-export.py` (preserved and extended from the validated, untracked Nexus script with original SHA-256 `fed7cf589f154a7370369961558c4ba8b34b0ce1d3f6623d08699920387ad968`), `shared/scripts/qdrant-memory.py`, `shared/scripts/qdrant-memory-hermes-mcp.py`, `shared/tests/test_hermes_compaction_memory.py`, and `hosts/nexus/files/etc/systemd/system/qdrant-memory.service`.
- Existing Nexus exporter was untracked in public `~/ops`, not part of preserved private Git history. Public `ops` and original private `ops-private` remain separate; no private commit was imported.
- Runtime: `/opt/data/state.db` (main profile only), private checkpoint `/opt/data/state/qdrant-memory/hermes-compaction-checkpoint.json`, existing Nexus timer and `hermes` container, existing Tensor Ollama, existing Nexus Qdrant, container MCP `/opt/data/mcp/qdrant-memory-hermes-mcp.py`. No profile DB, agent memory file, old origin, or compression source changed.
- Existing protected `/srv/containers/data/hermes/data/memory-export-review` retains four **UNREVIEWED** Markdown files from the earlier pilot. None is placed in the public checkout or manual inbox.

## Verification and limitations

The validated baseline was re-read and rerun: 36 completed compactions, 140 selected sections, 416,771 selected source bytes. The new strict item-level selector currently accepts one candidate from these summaries (a historical qBittorrent telemetry observation) and quarantines the rest by sensitivity, ambiguity, structure, or missing public Git source reference. Its source path matches the tracked `telemetry.py`; corroborating public `docs/current/nexus-qbittorrent-monitoring.md` independently describes the `qbittorrent.prom` output. Even so, the payload remains labelled historical agent report, not verified current state. This is intentionally low recall; no bulk section indexing. See `docs/current/hermes-qdrant-memory.md` for the data flow and rollback.

Pending production verification, Qdrant counts, scheduling results, and Git publication will be recorded here after actual readback; do not infer them from source installation.

## Recovery

Restore the previous unit and dispatcher from the preceding public Git revision; `systemctl daemon-reload` to remove the post-start container invocation. Preserve the private database and checkpoint; restore the MCP runtime file from its targeted protected pre-change copy. If Qdrant rollback is necessary, delete only exact IDs verified as `hermes_session`; never delete the collection or other origins. Consult the current-state document before doing so.
