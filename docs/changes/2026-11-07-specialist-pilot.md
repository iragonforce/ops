# Native specialist evaluation and closeout

Objective: evaluate installed Hermes Profiles/Kanban after consolidation, preserve Paperclip and inference experiments, and demonstrate a reversible bounded handoff if native capabilities suffice.

Added only DevOps and Research profile configuration and retrieval-pointer seeds, owned by `shared/hermes/pilot`. The existing default Nexus Hermes remained Coordinator. The profiles use separate live homes under `/opt/data/profiles`, root OAuth fallback without copied credentials, no MCP configuration, bounded turns and no new gateway services. Role descriptions and source-based instructions are recorded in `docs/current/specialists.md`.

Created native board `infra-pilot` with one dependency chain. These were real native workers launched by the existing gateway, not manually completed cards:

| Task | Assignee | Result | Runtime |
| --- | --- | --- | --- |
| `t_0c971c71` | devops | Retrieved the four duplicate MCP changes, source/deployment paths, dated checks, revision and rollback. | 57 seconds |
| `t_9b81ea31` | research | Verified the parent handoff against repository evidence; distinguished recorded November 6 checks from fresh live verification. | 39 seconds |
| `t_080ad7b1` | default / Coordinator | Accepted the evidence handoff and explicitly retained Paperclip as production authority. | 30 seconds |

All three native runs ended `done`, with no active run remaining. DevOps used 10 read-file calls, 8 searches, 2 task-context reads and one completion; Research used 8 read-file calls, 2 searches, 2 task-context reads and one completion. Neither specialist invoked shell, write, patch, MCP, skill-management or memory-write tools. Each created its own session database and one session. Native worker startup seeded one essential Hermes skill in each home despite the no-bundled-skills marker; no custom skill was created. The shared source checkout remained clean. All ten seeded source files matched their deployed bytes.

The owner then requested that only Codex and its agents continue, with no further Hermes calls. By the time this instruction was checked, Coordinator had already finished. No further worker was launched. Native `remove_board(archive=True)` preserved the pilot under `/opt/data/kanban/boards/_archived/infra-pilot-1794056283`; only `default` remains in active board discovery. The two profiles are dormant and the main Hermes gateway, Paperclip routing and existing inference services were not restarted or replaced.

Consolidation through `9500472` had already passed the separate review: 505 deployed paths matched source, and the fresh reviewer recovered all six change-handoff elements from Git records alone. Pilot source and this record are committed together; their introducing revision is discoverable with `git log -- docs/changes/2026-11-07-specialist-pilot.md`.

Limits: this demonstrates native isolated execution and knowledge handoff, not automatic task decomposition, process-crash recovery, direct Codex worker execution or long-term reliability. Installed native code supports routing and recovery, but those operational gates remain untested. Existing Docker CLI venv/lock warning did not prevent these runs. The file toolset has write capability; successful read-only behavior is observed, not an OS sandbox guarantee. Physical behavior and unrelated service failures remain outside scope. No formal tests were run.

Decision: retain Paperclip as production authority. Do not migrate agents or enable competing production intake. Resume Hermes evaluation only on owner instruction; next gates are a bounded routing check, interrupted-worker recovery and a working Codex implementation handoff. Use the existing ten-task metrics in `docs/reliability.md` to measure subsequent reliability rather than claiming improvement from this one pilot.

Rollback: board already archived with history retained. If profiles are retired later, first verify no profile worker exists, then preserve their homes outside active profile discovery. Never overwrite root auth, sessions, databases or learned memory from seeded source. Existing production task routing needs no rollback because it was not changed.

Final Codex reviewer completed: ten source hashes matched recorded live hashes; one stale current-state sentence about the empty profiles directory was corrected. No other important findings. New profile source secret scan found zero findings; `git diff --check` passed. Existing main Hermes and relays remained healthy, Paperclip remained running, and Qwen Hermes remained healthy. These are process/health checks, not full application or physical acceptance.
