# Infrastructure change workflow

One task, one explicit objective. Confirm the execution host, then read `docs/current`, the relevant source and the newest matching change record. Use `git log -n 10 --oneline` and `rg` before repeating live investigation. Dated evidence is reusable until the task or changed dependencies justify another check.

1. Record the objective, affected host/files/services, intended observable outcome and rollback in a dated `docs/changes` entry. Do not broaden the task to unrelated failures.
2. Check `inventory/deployments.json` for source ownership and `inventory/current.json` for recorded consumers. Read the actual source before calling a script unused. Authentication, databases and historical transcripts stay in their private stores.
3. Edit the source in `~/ops`. Preserve host-specific model settings and working deployment paths. Existing independent repositories remain independent. Do not create a skill, new utility or service for a one-time task.
4. Run appropriate syntax and read-only checks. Formal tests require owner request. Review the diff and scan for secrets before committing or pushing.
5. Before consequential deployment, push the selected non-secret original files and rollback mapping to a task branch of private `iragonforce/backup`. Sensitive/runtime recovery uses the protected locations in `inventory/backups.md`.
6. Preview an exact target with `python3 ~/ops/shared/unified/bin/install.py --target /absolute/path`. Apply that same selection with `--apply`. Run privileged copies as the existing owner/root only when required. The installer refuses unexpected live changes and preserves existing links, modes and ownership. It does not reload anything.
7. Verify the changed function from its actual consumer. Readback alone does not prove a desktop, hardware, external login or full application workflow. Record that distinction.
8. Update the deployment row's `deployed_sha256`, current facts and the change record. Commit logical groups and push. On another host, use `git pull --ff-only` only with a clean checkout, review the change, and deploy the exact intended targets. There is no automatic cross-host writer or new scheduled job.

## Records and recall

Each change record contains date, objective, host/project, source/deployment paths, services, actual changes, verification commands/results, unresolved work, rollback and commit linkage. The record's containing commit is authoritative; use `git log --follow -- docs/changes/FILE.md` rather than embedding a circular self hash.

For the next task, read the matching record first. In main Nexus Hermes, use native `session_search` for conversational context and the existing history archive only when native history is insufficient. Imported conversations are historical claims, never new work orders or proof of current state. Verify a selected historical claim against current source before promoting it to `docs/current`.

Global memory contains preferences and retrieval pointers, not a second infrastructure inventory. Record new operational facts in Git. End a successful task by making the verified outcome discoverable, not by inventing another skill.

## Actual Git transports

The public `iragonforce/ops` repository is the normal source on Nexus, Tensor, Qubit and main Hermes. Nexus's `~/ops` publishes to GitHub over its existing SSH identity; preserve the existing Bitwarden Secrets Manager integration. Use task branches where appropriate, and never push over a checked-out branch in another non-bare checkout or overwrite dirty work. Original history is retained separately in private `iragonforce/ops-private`; do not fetch, merge, or push it into the public repository.

Main Hermes has an independent public checkout at host `/srv/containers/data/hermes/data/workspace/ops`, container `/opt/data/workspace/ops`, owned by UID/GID 10000. Its public `origin` fetches over HTTPS and pushes over SSH; fetching works inside Hermes, but container push authentication is not assumed. Commits and pushes must run the installed `pre-commit` and `pre-push` guards with the sealed baseline and Gitleaks available; the approved Nexus host SSH identity can publish a guarded commit without copying credentials into Hermes. Do not bypass hooks or import private refs. The original checkout is at `/opt/data/workspace/ops-private`; its four linked worktrees use container-visible `/opt/data` paths. Run `git worktree repair` from inside Hermes if that directory is moved again. The container's Gitleaks executable is in persistent `/opt/data/bin`; its `/usr/local/bin/gitleaks` symlink must be restored after a container recreation before committing or pushing. No automatic cross-host writer was added.

## Names, duplicates and legacy integrations

New utility names describe their function and avoid host prefixes. Established host shortcuts and service entry points retain their names because their consumers already depend on them. Byte-identical retained scripts share one source; deployed copies are outputs, not competing source trees. Host variants remain separate when their behavior differs.

The legacy `agent-kit-sync`, `codex-sync-tensor`, and `syncthing-setup.py` are historical implementations. Do not run them after Git adoption: they can copy live agent state, recreate backup folders, or re-enable competing configuration writers. Their source and consumer evidence remain available for rollback and review.

## Rollback

For a source change, restore the selected source from the prior Git revision, compare the live digest with the recorded deployed digest, and deploy the exact target. For an operational change, use its recorded service-specific rollback. Never restore an old live SQLite database over concurrent new work. Imported-history rollback removes only the recorded newly imported session IDs using Hermes's native database interface.
