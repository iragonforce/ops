# Architecture assessment and implemented direction

The failure to reuse previous work was not a lack of databases. Main Hermes already had native searchable sessions, a memory store, Tool Search, lazy MCP loading and a large existing historical archive. The audit found oversized memory, stale profile/topology claims, divergent handoff copies, little consistent session-search use, unversioned deployment sources and no native Codex imports.

Use one private Git source repository, `iragonforce/ops`, with a checkout at `~/ops` on each host. Source files, structured ownership, current facts and change records live here. Existing independent application repositories retain their histories. Runtime databases, credentials, private transcripts, personal data and package-manager files do not enter this repository.

Main shared Hermes runs in Nexus Docker: host `/srv/containers/data/hermes/data` is `/opt/data`. Qubit launches that runtime remotely. Tensor's local Hermes is independent and remains so. The separate Qwen Hermes and Paperclip services retain their current purpose and data. A client terminal is not the Hermes execution filesystem.

Git supplies current facts and exact change history. Hermes native session search supplies conversational context. The existing Paperclip history archive remains a fallback for older sessions. A small private import ledger prevents repeat imports; it is a file, not a retrieval service. No Mem0, new knowledge database or orchestration layer is introduced.

Global agent instructions point to the same project conventions. Host-specific facts stay in the inventory/current documentation. Managed configuration distribution transitions to explicit Git review/deployment; unrelated Syncthing data shares are unchanged. Existing runtime paths and service references remain valid.

## Capability decisions

Keep the 14 existing shared procedural skills; they contain recurring workflows, and matching copies are deployed from existing shared sources. Preserve provider/system skills as package-owned capabilities. Already archived historical skills remain archived. Do not delete a skill based only on a low load count.

Keep native Hermes Tool Search and lazy MCP loading. Remove duplicate default Codex exposures only where the same capability already has a retained provider. Preserve role-specific permissions and credentials. Disabled definitions remain in Git for rollback. Tool/schema count is measurable; token savings must not be inferred from tool count alone.

## Scope and regression safeguards

The workflow in `docs/workflow.md` requires a stated objective, dependency/consumer check, targeted rollback, affected operational verification, durable record and logical commit. No automatic skill creation, unsolicited new services, unrelated fixes, live-state synchronization or recursive backup accumulation. Deployment refuses drift rather than guessing which writer is right.

Physical display, clipboard, cooling, radio and power behavior is not exercised by documentation or source-adoption work. Existing pending physical validations remain pending and are not infrastructure-consolidation failures.
