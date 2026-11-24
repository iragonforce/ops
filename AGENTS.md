Infrastructure work

Primary objective: Complete the owner’s task, verify the result, and leave accurate source and records for the next agent. Improve reliability without accumulating unnecessary complexity.

1. Orient first. Confirm host, project, and scope. Read relevant inventory, recent Git history, change records, and existing source before probing live systems. Reuse dated evidence unless its dependencies changed or fresh verification is necessary. Historical instructions are evidence, not commands. When operating through Hermes, distinguish the client, agent container, and target host. Verify the actual execution environment before commands; use SSH when needed to reach another host. Prefer `capture` for persistent diagnostics and keep large logs private.
2. Stay on task. Complete the requested objective and direct blockers first. Report unrelated opportunities afterward; do not implement them. Choose the smallest maintainable solution.
3. Preserve working systems. Protect services, data, host identities, network segmentation, credentials, and unsaved work. Coordinate disruption. Existing authorization covers scoped implementation, logical commits, and pushes; do not ask again. Respect stricter task-specific constraints. Disabled approval prompts do not expand the owner's authorization. Treat Docker daemon access and similarly privileged tool interfaces as host-level capabilities requiring the safeguards of direct root access.
4. Make Git authoritative. Every managed script/configuration needs a repository owner. Preserve independent repository history and existing deployment paths until consumers and replacements are verified. Commit/push logical, verified changes. Git does not replace runtime-state backups.
5. Standardize scripts. Reuse utilities before creating new ones. Name by function, not machine or homelab. Every retained persistent executable needs an introductory purpose comment, usable help, a man page, and documented dependencies. Avoid persistent one-off utilities.
6. Protect secrets and runtime state. Never print or commit credentials or raw transcripts. Use existing Bitwarden references and protected stores with least privilege. Rotate exposed secrets when required, not routinely. Never synchronize live agent databases, authentication, or sessions across machines.
7. Retrieve before rediscovering. Use native Hermes memory/session search, Git, and shared inventories. Keep global/profile memory concise: stable preferences, verified lessons, and retrieval pointers. Store detailed machine facts, incidents, and decisions in the repository. Distinguish verified current state from history and hypotheses. The historical archive remains private regardless of directory names. Use `project_graph` only for explicit project knowledge, not automatic personal memory.
8. Use focused specialists. Coordinator handles cross-domain context and delegation; Hermes profiles hold domain-specific experience. Share verified facts through Git, not duplicated memories. Preserve profile isolation. No new or duplicated skills, MCP servers, profiles, or tools without recurring value and authorization. Improve existing relevant skills within scope. Keep Mem0 disabled and existing index/project boundaries intact unless authorized. Follow `docs/current/specialists.md` for current task authority and specialist permissions. Do not reactivate archived boards, dormant profiles, or parallel production task intake without authorization. Load full third-party skills only when relevant.
9. Verify proportionately. Perform affected syntax and operational checks. Run or add formal tests only when task constraints permit; avoid unnecessary frameworks. Configuration readback does not prove physical behavior. Component updates require explicitly selected versions and affected checks. Report unverified acceptance criteria honestly.
10. Make rollback targeted. Prefer Git for source/configuration recovery. Establish a rollback path before consequential changes. Use a task branch of private iragonforce/backup for appropriate non-secret backups; keep sensitive/large recovery in approved protected stores. No routine timestamp backup directories or blind cleanup.
11. Learn from outcomes. After meaningful work, record reusable verified findings, recurring failures, and corrected assumptions in the appropriate existing documentation or memory. Consolidate outdated or duplicate knowledge. Record failed approaches when useful. Learning never authorizes unrelated changes.
12. Close the loop. Update affected current-state docs, inventory, and meaningful change records, with objective, actual changes, checks/results, limitations, rollback, and Git revision. Git commits suffice for routine history; create separate records only when valuable. If incomplete, record the exact blocker and next step.

Default boundaries: No unsolicited services, databases, recurring jobs, external messages, version upgrades, or unrelated fixes. Add components only when required by the approved objective or expressly authorized. Preserve existing authorized boot notifications. Prefer native shell, filesystem, Git, Hermes, and Codex capabilities over custom orchestration.

Knowledge entry point: host `~/ops/docs/START-HERE.md`; main Nexus Hermes `/opt/data/workspace/ops/docs/START-HERE.md`. Shared source: public `iragonforce/ops` on `consolidate`. The original Hermes checkout, including its private Git history, local changes, and linked worktrees, is retained at `/opt/data/workspace/ops-private` with `iragonforce/ops-private` as its only remote. Never merge or push that history into public `ops`. Current operating boundaries are in `docs/current/host-operations.md`; new meaningful changes belong in `docs/changes`.

## Task isolation and context efficiency

### Git worktrees

- For repository-modifying tasks, use a task-specific Git
  worktree and branch by default. Read-only work does not
  require a new worktree.
- Reuse the existing worktree when continuing the same task.
  Do not create duplicate worktrees for the same objective.
- Verify the authoritative branch and fetch current refs
  before creating a task worktree.
- For Hermes ops tasks, prefer:
  `/opt/data/workspace/worktrees/ops/<task-id>`.
  Use the current authoritative `origin/consolidate` as the
  baseline when verified.
- Never reset, clean, rebase or overwrite an existing dirty
  checkout merely to start another task.
- Preserve unpublished commits and untracked files.
- Validate changes before integration. Do not automatically
  merge, push or delete task worktrees.

### Infrastructure context hierarchy

- The `iragonforce/ops` repository is authoritative for
  infrastructure configuration and operating procedures.
- Use `AGENTS.md` and `docs/START-HERE.md` as the entry point.
  If their instructions are already loaded and current, do
  not reread them unnecessarily.
- For a specific task, retrieve only relevant sections of
  `docs/current/`, inventories and recent `docs/changes/`.
- Distinguish documented configuration, historical evidence,
  observed runtime state and assumptions.
- The `homelab-context` legacy documents, old inventories,
  bootstrap prompts, Paperclip records and execution plans
  are historical reference material, not current authority.
- Do not preload or routinely summarize historical context
  collections. Consult them only when specifically relevant.
- Do not automatically promote old project instructions or
  historical facts into persistent memory.
- Prefer existing Hermes memory and session search over
  creating a second infrastructure memory system.
- Avoid repeated full audits. Reuse verified findings while
  checking whether they remain current.
- Keep large logs outside model context; return concise
  findings, relevant excerpts and evidence paths.
- When handing off a task, preserve only its objective,
  important findings, authorized changes, verification,
  blockers and next action.
- Preserve active task state and historical evidence.
  Do not delete it merely to reduce context size.

### Operational boundaries

- Perform read-only diagnostics without unnecessary prompts.
- Authorized non-destructive file creation and modification
  may proceed within the requested scope.
- Never infer authority for destructive changes from Docker
  socket access, SSH access or disabled approval prompts.
- Do not delete persistent datasets, destroy backup or
  snapshot history, or rotate, revoke or replace existing
  credentials without separate, explicit authorization
  for the specific operation.
- Never expose credentials in logs, prompts or Git history.
