# Infrastructure operations

Private source, verified facts and change records for **qubit** (macOS), **tensor** (Arch Linux) and **nexus** (Debian 13). Checkouts live at `~/ops`. Git owns source history; running services and private agent state stay at their existing locations.

Start with [current state](docs/current/README.md), [changes](docs/changes/README.md), and the relevant [asset inventory](inventory/README.md). Read only the task-relevant source and recent records. Historical proposals are not queued work.

## Ownership

- `shared/`: maintained shared configuration, instructions and approved skill sources.
- `hosts/`: host-specific source files; deployment locations remain unchanged unless a record explicitly says otherwise.
- `inventory/`: assets, deployment ownership, backups and evidence dates.
- `docs/current/`: concise current facts with evidence references and pending validation.
- `docs/changes/`: objectives, changes, checks, limits, rollback and revisions.
- `docs/history/`: selected non-secret dated context; never automatically loaded instructions.
- `tools/`: existing deployment workflow extended for explicit manifests and conflict checks.
- `man/`: manuals for maintained executables.

Authentication, live Codex/Hermes databases, raw conversations, environment values, pairing state, Thread datasets, private keys, caches and application data do not belong in this repository. A private repository is not a credential vault.

Independent application repositories and `agent-tools-stage1` retain their own histories. See inventory for ownership; never create nested repositories by copying `.git` directories.

## Completion convention

For a meaningful change, record its objective, affected hosts/files/services, actual result, exact checks/outcomes, pending work and targeted rollback. Commit and push source and records together. A pending physical check, failed check, or failed push remains explicitly pending. Review reliability manually after ten completed infrastructure tasks; no new scheduler is required.
