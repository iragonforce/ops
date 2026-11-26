# Qdrant chat reconciliation at durable session close — November 26, 2026

Objective: Select eligible default-profile chat findings only after a durable session close, wake the existing Nexus reconciler on close, and preserve the 12-hour auditor as a read-only review path.

Scope: public `ops` worktree `feat/qdrant-session-close`; Nexus `qdrant-memory.path`, existing systemd service/timer, and the default Hermes plugin directory. No new service, collection, auditor, profile, or provider. The original `hermes-chat-checkpoint.json` and indexed points remain untouched for rollback. No session database or transcript is modified.

Source: `shared/scripts/hermes_chat_memory.py`, `shared/scripts/qdrant-memory.py`, `shared/hermes/qdrant-session-close/`, `shared/tests/test_hermes_chat_memory.py`, `shared/tests/test_qdrant_session_close.py`, `hosts/nexus/files/etc/systemd/system/qdrant-memory.path`, `man/nexus/qdrant-memory.1`, and `docs/current/hermes-qdrant-memory.md`.

Implementation: `sync-chat` uses a private, integrity-checked closed-session cursor `(ended_at, session_id, answer_id)` and only explicitly closed CLI/TUI/Photon sessions; compression and automatic orphan cleanup are excluded. Individual turns keep the existing privacy, schema, model, exact-point/hash, deduplication and retry gates. Existing point IDs from the prior settled-turn selector are preserved even if the model returns different text on re-selection. A small default-profile `on_session_finalize` plugin touches a private marker without chat content; the existing `.path` watcher also observes that marker. An hourly timer catches missed/racing notifications. Bootstrap is explicit and forward-only; a project record still requires committed non-sensitive Markdown in the trusted Nexus checkout.

Audit: Existing `qdrant-memory-audit` cron was verified enabled at `every 720m` on `gemini-3.8-flash` (last run November 26, 08:22 EST). Its MCP toolset is read-only. Findings must be checked against Git and live state; correct the source and reindex with existing writer. Exact-ID/vector deletion or payload rewriting of stale/duplicate points requires separate explicit approval and a protected recovery snapshot, not automatic audit action.

Pre-deployment checks: seven chat tests, two hook/path tests, six ops tests, seven compaction tests, ten chunk tests, twelve Qdrant writer tests passed (44 total); Python compilation and `git diff --check` passed. Read-only `closed_turns` query executed against live default-profile SQLite, returning ten eligible turn rows and two end markers in a bounded historical sample; no transcript text printed. Live path/systemd validation and marker wake/readback remain to be recorded below.

Rollback: stop only the existing `.path` during unit replacement, restore the prior committed `.path`, remove only the deployed `qdrant-session-close` plugin, and restore the prior writer scripts/service revision in Nexus and Hermes. Keep both private checkpoint files and all existing Qdrant points; return to the old settled-turn writer only after confirming its retained original checkpoint. Do not delete points or reset the database as rollback.

Acceptance:

- Pending live deployment and hook/process reload verification.
