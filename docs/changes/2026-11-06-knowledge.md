# Native knowledge and capability consolidation

Objective: reuse verified infrastructure knowledge without another memory or retrieval system.

Main Nexus Hermes memory was consolidated through its native MemoryStore batch interface from 20 stale entries / 3,878 characters to 3 entries / 1,152 characters, within the unchanged 2,200 limit. The user profile remained unchanged. The new entries contain the runtime boundary, Git/native-search pointers and concise working preferences. The screened original is on private backup branch `unified-infra-2026-11-06`, commit `bdf7424`. Running conversations may retain their frozen prompt snapshot until a new context loads; no restart was forced.

Imported one selected, completed archived Codex conversation per host using the installed native importer. Tool outputs and injected context wrappers were omitted; known credentials and credential patterns were redacted in memory. Original archives were read only. Temporary sanitized input files were removed after import. Private provenance/deduplication ledger: Hermes `/opt/data/import-ledger/codex.json`. Raw transcripts and that private ledger are outside Git.

| Origin | Native Hermes session | Actual native search result |
|---|---|---|
| qubit | `20261106_173433_d5590d` | tmux: 11 matching messages; SSH: 10 |
| tensor | `20261106_173433_67b51f` | tmux: 2; SSH: 3; Hermes: 8 |
| nexus | `20261106_173433_cb4cb2` | Hermes: 2 |

These are historical conversations, not verified current configurations. Existing private archive retrieval remains available for everything not selectively imported. Rollback uses native `delete_session` for these exact new IDs and removes their ledger entries; never restore an old database over active sessions.

Skill disposition is in `inventory/capabilities.json`: retain the 14 shared procedural skills and Tensor's 58 existing bundled skills; do not infer disuse from absent counters. Prior obsolete skills already have an archive branch. No new skills were created. Observed load counts and description sizes are recorded without claiming token savings.

Nexus Codex's four local MCP duplicates (`context7`, `codebase_memory`, `project_graph`, `playwright`) are disabled in the host override and generated configuration; their existing `hn-*` providers remain. Other roles, credentials, Hermes native Tool Search/lazy loading, Tensor local inference, Mem0-disabled state and approved indexing boundaries are preserved. Backup commit `dcfd5f0` retains the original definitions. Deployment and client readback are recorded with this change's completion commit.

Completion checks: all six Nexus-definition copies across the three source trees deployed with matching hashes. The Nexus Codex CLI parsed 30 MCP definitions (including the plugin-provided definition), 26 enabled, and exactly the four intended local duplicates disabled. Existing Hermes processes stayed healthy. Source change: `a3225b4`; native session retrieval results above were obtained through the installed SessionDB search interface, without an LLM replaying historical instructions.
