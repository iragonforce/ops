# Hermes specialist pilot

## Current deployment status — 2026-11-08

The owner subsequently selected Nexus Hermes native Kanban
to replace Paperclip. Paperclip and its relays have been retired;
the main Hermes dashboard and Authentik integration are verified.
The redundant Nexus Qwen Hermes container was removed, while
Tensor's independent native Hermes and local Ollama inference
were verified.

The November 7 specialist pilot below is retained as historical
evidence. The Codex provider responding successfully does not
establish that the Codex CLI is installed inside Hermes, that a
Codex worker lane is configured, or that autonomous specialist
execution has passed its remaining acceptance criteria.
Keep the pilot board archived. No new production specialist
execution is authorized by this documentation change.

## Archived pilot evidence — 2026-11-07

Verified 2026-11-07 against installed Hermes v0.21.6 (2026.9.24), upstream `a28a5d03`, and Paperclip server 0.3.1 in `blinkwired/paperclip-paused-guard:20261103-v1`. No software was upgraded.

At the time of this pilot, Paperclip was the production task authority. Hermes board `infra-pilot` completed a bounded evaluation and is now archived. The owner subsequently instructed that only Codex and its agents continue this project; do not invoke Hermes workers or resume this board without a new instruction. The existing Nexus default profile remains Coordinator; only `devops` and `research` were added. No Network, Git or Designer profiles were created. Tensor and the separate Nexus Qwen instance were still present at pilot time.

## Installed capability comparison

| Requirement | Hermes evidence and limit | Existing Paperclip comparison |
| --- | --- | --- |
| Persistent isolation | Native profile homes hold separate config, memory and session databases. Root OAuth fallback avoids copying grants. Isolation is application state separation, not an OS security boundary. | Existing adapter/agent identities support separate workers; host-oriented roles can remain during evaluation. |
| Task management | Native boards, dependency graph, run records, comments and structured results exist in this build. | Existing issues, activity and heartbeat-run records already provide this. |
| Automatic routing | Installed `kanban_decompose.py` routes triage children using profile descriptions; existing coordinator config enables decomposition. Pilot uses explicit bounded assignments; automatic decomposition is not yet acceptance-tested. | Existing agents/adapter routing remain available; owner reports organizational friction. |
| Independent execution | Existing gateway spawns `hermes -p <assignee> chat` workers with profile scope and pinned board/workspace. No additional gateway or daemon is needed. | Existing Hermes relays and native adapter registry remain intact. |
| Handoffs | Parent dependencies and native run summaries carry results to downstream workers. | Existing issue/context and activity mechanisms remain intact. |
| Visibility | Native task status, attempts, heartbeat, worker logs, errors, runtime caps and retry limits are implemented. | Existing heartbeat, issue and activity records remain the production history. |
| Shared knowledge | Both profiles read `/opt/data/workspace/ops`; personal memory and session search stay profile-local. | Shared Git can also serve existing Paperclip workers. No archive migration required. |
| Low friction | Ready cards can execute without a company hierarchy or board-approval workflow. Tool approvals and authorization boundaries still apply. | Installed server includes companies, approvals and agent-reporting structures; current policy was not changed. |
| Recovery | Native block/unblock, reclaim, runtime timeout and retry circuit breakers exist. A blocked pilot card was explicitly unblocked and dispatched. Process-crash recovery remains untested. | Installed heartbeat/cancellation/recovery code exists; no disruptive recovery exercise performed. |
| Codex implementation | Git-based handoff already works. Native worker-lane extension contracts exist, but this container has no Codex executable or configured Codex lane. Do not claim direct Codex worker integration. | Installed registry has `codex_local`, `hermes_local` and `hermes_gateway` adapters. Preserve this working option. |

Evidence: installed `/opt/hermes/hermes_cli/{profiles,kanban_db,kanban_db_dispatch,kanban_decompose}.py`, `gateway/kanban_watchers_dispatcher.py`, `model_tools.py`, `toolsets.py`; Paperclip `/app/server/src/routes/{agents,approvals}.ts` and `adapters/registry.ts`. An unauthenticated Paperclip companies request returned 403; no auth policy was bypassed, and live per-agent settings are not claimed revalidated.

Upstream references: [profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles/), [Kanban](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban), [worker lanes](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban-worker-lanes). Installed behavior takes precedence over current website claims.

## Pilot boundaries and ownership

Non-secret profile source: `shared/hermes/pilot/{devops,research}`. Live homes: `/opt/data/profiles/{devops,research}` inside main Hermes, backed by `/srv/containers/data/hermes/data/profiles` on Nexus. `MEMORY.md` in source is an initial retrieval pointer, deployed to `memories/MEMORY.md`; future learned memory and sessions are private runtime state, never a synchronization target.

The minimal standard profile layout was published atomically and recognized by native profile discovery. Native profile-create also registers a dormant gateway; that unnecessary service registration was avoided. CLI worker bootstrap subsequently seeded its one native essential `autonomous-ai-agents/hermes-agent` skill in each profile despite the no-bundled-skills marker; this is observed native behavior, not a new custom skill. Each new profile has its own empty mode-600 `.env`, no copied auth or channels, no MCP definitions, the native no-bundled-skills marker and the one bootstrap-seeded essential skill. `AGENTS.md` links to the shared checkout. No gateway service was registered. Existing multiplexing is disabled.

The pilot uses the existing model/provider (`gpt-6-sol`, `openai-codex`), 12 tool turns, 240-second task caps and a one-failure circuit breaker. Specialist CLI tools are limited to file, native memory/session search and Kanban. The file toolset includes writes: read-only pilot behavior is an instruction boundary, not a filesystem sandbox. Coordinator retains its existing configuration and receives an explicitly read-only task.

Active native board storage was `/opt/data/kanban/boards/infra-pilot`; archived history is `/opt/data/kanban/boards/_archived/infra-pilot-1794056283`. Default board and sticky profile remain unchanged. The existing gateway discovers all boards, so ready pilot cards are real runnable work. Do not add unbounded tasks or production intake to this board. No new service, timer, database framework, custom retrieval or orchestration integration was introduced.

## Acceptance and next decision

Pilot cards: DevOps `t_0c971c71` → Research `t_9b81ea31` → Coordinator `t_080ad7b1`. Results and actual checks belong in `docs/changes/2026-11-07-specialist-pilot.md`.

Replacement is **not approved by setup alone**. Before choosing Hermes as the sole production task system, require the complete native handoff chain, accurate evidence and rollback retrieval, visible failed/interrupted-task recovery, one bounded automatic-routing task, and an agreed working Codex handoff. Then evaluate the next ten real tasks using `docs/reliability.md`. No claim of improved long-term reliability follows from a single demonstration.

If those gates pass, route new work to one selected authority, retain Paperclip history read-only, and retire redundant host agents only in a separate targeted change. Do not activate parallel production intake or remove local-model experiments.

## Targeted rollback

Stop adding pilot work. Inspect native `hermes kanban --board infra-pilot list` and `runs` first; never archive or move state while a worker is active. All three pilot cards are terminal and the board has already been archived with native `remove_board(archive=True)`, preserving its history. Leave default/Paperclip routing untouched. Preserve the two profile homes outside active `profiles/` if retiring them, after checking no profile worker remains; do not copy or restore the main runtime database or root OAuth. The source and seeded files can be recovered from the commit introducing this document. Review live diffs before replacing config; never overwrite learned memory with its initial seed.

Known pre-existing warning: the installed CLI reports that its Docker-managed venv is out of sync with `uv.lock`. Do not auto-update or rebuild it as part of this pilot. Actual worker outcomes determine whether it blocks this use case.
