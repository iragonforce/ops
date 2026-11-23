# Component updates, verification and rollback

Keep this directory at a committed known revision. All commands below describe
deliberate maintenance, not jobs to run automatically. Before replacing components,
finish their active tool calls and save the current lockfiles and runtime directories.
Do not interrupt unrelated gateways, desktop sessions or Paperclip runs.

## Source and dependency ownership

| Component | Update procedure | Rollback unit |
|---|---|---|
| Superpowers | Fetch a reviewed immutable revision into a new source snapshot. Hermes: plugins install obra/superpowers --ref SHA --enable; review scanner findings before any force override. Codex: native local marketplace registration and plugin add superpowers@superpowers-dev against the staged source. Verify discovery and an actual skill invocation before switching the registered snapshot | Remove the two native plugin registrations; restore profile config and source pin |
| Matt Pocock | Checkout selected SHA in a staged clone. Use pinned skills-stage1 add LOCAL_SOURCE --skill handoff research domain-modeling writing-for-agents -g --copy -y with -a codex; in Hermes use -a hermes-agent and HERMES_HOME=/opt/data/profiles/qubit. Do not install the broad native plugin on top | Remove only these four newly added copies and their CLI provenance entries |
| Anthropic | Use the system skill-installer with --repo anthropics/skills --ref SHA --path skills/mcp-builder into an empty staging directory; review license/scripts. Copy the complete folder to the two runtime skill locations after removing/archiving the old added folder | Remove only newly added mcp-builder; keep original built-in skill-creator |
| Awesome MCP | Checkout a reviewed catalog revision and replace only the reference text, retaining the prior copy. Review maintenance/provenance before choosing any new server | Restore old reference or remove the added reference/agent-tools routing skill |
| Reference Memory | Stage npm server-memory@VERSION with exact lockfile and review schema/storage changes. Retain graph data; test create/search/reconnect in a separate fixture | Restore former npm bundle and graph file if data migration occurred |
| Mem0 | Stage pinned mem0ai/Ollama packages in separate host/container venvs; keep telemetry disabled. Fulfill documented inference/embedding/vector-store prerequisites before any production enablement | Remove the added SDK venvs; existing Hermes memory remains untouched |
| Context7 | Stage @upstash/context7-mcp@VERSION, retain the exact lockfile; test public version-specific lookup and anonymous failure/rate-limit handling. Keep optional sign-in elicitation off in Hermes | Restore former npm bundle and the two MCP definitions |
| Codebase Memory | Run provision_cbm.py only after explicitly choosing VERSION/ASSET and reviewing that release installer. Verify checksums, test in a separate cache/root, then replace the two runtime binaries after active clients close | Restore prior binary and matching cache snapshot; never point an older binary at migrated cache data |
| Playwright | Stage @playwright/mcp@VERSION and its exact browser revision. Install browser binaries as non-root, test sandboxed host launch and socket transport, update the recorded executable path and unit together | Restore matching npm/browser bundle and unit files; stop only these socket connections after coordination |
| Vercel CLI | Stage skills@VERSION and compatible Node, pin exact versions in package.json/lock; verify version, supported agent names, HERMES_HOME targeting, local listing and discovery before replacing the wrapper target | Restore the former npm/Node bundle; remove only the newly added wrappers if abandoning the integration |

Use `npm ci` against an reviewed package-lock in an empty staging directory.
The npm client itself can be run with the staged pinned Node on PATH. Retain both
Python locks; rebuild each venv using its own interpreter rather than copying a
Python 3.13 environment into a Python 3.14 container.

## Reproduce functional checks

1. Start a temporary fixture server on host loopback only:
   `python3 -m http.server 18765 --bind 127.0.0.1 --directory test-project`.
   Its content comes from fixtures/. Stop it after checks; it is not a service.
2. `python3 verify-codex-discovery.py` verifies native discovery. `node_modules/node/bin/node verify-mcp.mjs`
   exercises real host MCP calls. It creates its own temporary loopback page.
3. Copy the maintained verifier to the existing Hermes runtime bundle, then run
   `sudo -n docker exec --user hermes -w /opt/hermes -e HOME=/opt/data -e HERMES_HOME=/opt/data/profiles/qubit hermes /opt/hermes/.venv/bin/python /opt/data/agent-tools-stage1/verify-hermes.py`.
4. Browser-only container harness uses STAGE1_FIXTURE_URL=http://127.0.0.1:18765/
   and the private socket. A remote host-browser snapshot path is a host path;
   use browser_evaluate for bounded content instead of assuming container access.
5. Repeat the relevant model-driven checks in fresh CLI sessions. Package install
   success, schema enumeration and direct SDK clients alone are insufficient.
6. Confirm provider/model/memory/compression equality, zero clarification calls,
   unique server definitions and persisted graph results. No full reboot is
   required for routine checks unless a boot-persistence change is being evaluated.

The inspection and configuration scripts in this repository document the actual
sequence. They are not a blindly replayable installer: initial configure.py
intentionally refuses overwriting pre-existing MCP definitions, and later scripts
record the platform/socket/exposure corrections that were necessary here.

## Private backups

- Codex configuration and original plugin cache:
  `/home/iragonforce/.local/state/agent-tools-stage1/20261029/` (private directory).
- Hermes shared profile config, SOUL, skills and plugins, with permissions/ACLs:
  `/srv/containers/data/hermes/recovery/agent-tools-stage1-20261029/qubit-before.tar`.
- No provider authentication files, .env files, pairing data, Thread datasets or
  live session/memory databases were copied into this Git repository.
- Existing credentials remain in their original stores. Do not publish raw logs
  or backups. Preserve later user changes when restoring any before-state.

## Full integration rollback

1. Finish added tool calls. Disable only agent-tools-playwright.socket and stop
   its connection units; do not restart Hermes, Paperclip or unrelated services.
2. Remove the four added MCP definitions and Codex developer-instructions policy.
   If there were no subsequent config changes, restoring the private Codex config
   is equivalent. Otherwise merge those removals and preserve later settings.
3. Restore only Hermes config.yaml and SOUL.md from the tar archive (or merge out
   stage1 sections if there were subsequent edits), keeping UID/GID 10000. Remove
   the added native Superpowers plugin through its CLI, and the six added skill
   directories: four Matt skills, mcp-builder, agent-tools-stage1. Original skills
   and Hermes memory stay in place; do not restore an old live state.db.
4. Codex: remove superpowers@superpowers-dev with the native CLI and remove its
   added marketplace. Remove newly added mcp-builder, agent-tools-stage1 and four
   Matt skill copies. Retain original plugins and built-in skills.
5. Remove ~/.local/bin/codex to restore direct use of /usr/local/bin/codex; remove
   only the newly added skills-stage1 wrappers on host and Hermes. The global
   Codex binary and its provider credentials were not replaced by this work.
6. Archive the two runtime tool bundles and project-graph/CBM data before deleting
   them. Disable/remove the two added systemd units and reload systemd. Remove
   hermes-agent-tools GID 10000 only after confirming no remaining socket/files
   depend on it. Never recursively alter other /srv/containers/data ownership.
7. Recheck native memory, provider/model settings and ordinary CLI operation in
   fresh sessions. Retain this report, source locks and dated kit records as
   history, marking the integration rolled back rather than erasing the record.

No application/database image rollback is needed for the current installation:
existing images, provider data and memory databases were not migrated. If a later
tool update migrates its own graph store, restore the matching old binary and old
graph data together.
