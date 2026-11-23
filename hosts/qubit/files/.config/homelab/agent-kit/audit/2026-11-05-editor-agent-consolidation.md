# Homelab editor and agent consolidation — 2026-11-05

Execution host: Tensor, with authorized SSH operations on Nexus and Qubit.

## Result

- Nexus Hermes has one active default profile and one supervised gateway. The previous shared Qubit profile supplied the model/tool settings; root inbound/API settings were retained.
- Merged history: 106 sessions, 13,672 messages. SQLite integrity check passed. Memories and missing private environment keys were merged; original profiles were archived intact.
- Hermes and Codex on Nexus/Qubit have the same 99 unique skills. Codex skill files/resources match between the two machines.
- Both Codex installations have all 25 distinct Hermes MCP configurations. Role credentials stay separate in the single profile and remain on Nexus, outside Syncthing. Qubit uses SSH launchers; no local Hermes runtime was installed there.
- All 25 MCP configurations passed initialize and tools/list operational checks. Business actions were not executed. Remote provider tool counts depend on upstream availability.
- Neovim 0.12.6 and tmux 3.8 are available on all three hosts. Neovim configuration and plugin lockfiles match Qubit. Nexus plugins were restored to the pinned commits. Tmux configuration was reloaded without terminating existing sessions; Nexus has windows 1 zsh, 2 nvim, 8 superfile, 9 btop.
- Automatic Syncthing folders: homelab-unified-codex (send/receive), homelab-unified-nvim and homelab-unified-tmux (Qubit send-only; Linux receive-only). All nine host/folder checks reported idle, zero pending files, zero errors.
- Tensor local Hermes and its skills were not modified. Codex authentication, live session databases, history, and locks stayed local on each machine.

## Paths and activation

Shared root: ~/.config/homelab/unified. Codex skills are also exposed at ~/.agents/skills. Host-specific Codex configurations retain native runtime paths. Reload/reopen existing Codex sessions to load the new catalogs; live sessions were not terminated.

Nexus launcher: ~/.config/homelab/unified/codex/bin/hermes-mcp-exec.py. Private MCP diagnostics: /var/log/nexus-recovery/mcp. Syncthing has an explicit shared-root bind mount at /data/homelab-unified; no credential directory is shared.

## Rollback

- Snapshot: fast/debian-live@before-hermes-single-20261105-2208. Restore individual Hermes files; do not roll back the whole live dataset containing other services.
- Original profiles, configuration, identity/auth files, memories, and SQLite backups: /srv/containers/data/hermes/data/backups/single-profile-20261105-220932.
- Host link/configuration backups: ~/.local/state/homelab-unified/backups.
- Syncthing folder configuration backups: ~/.local/state/homelab-unified/syncthing.
- Syncthing Compose backup: compose.yaml.before-unified-sync beside the maintained Compose file.
- Protocol results: MCP-VERIFICATION.json beside this report.

## Limits and pending records

The existing Hermes artifact reports a venv/uv.lock mismatch. Its gateway/container health and MCP protocol checks pass; no dependency upgrade was attempted.

Knowledge record_change was unavailable in the current role catalog. A fallback audit note and linked CHANGELOG entry were saved in Qubit canonical agent kit. The Obsidian copy remains pending.

Legacy Nexus host-launcher selectors now redirect to the single default profile. Launcher rollback: `/usr/local/bin/hermes.before-single-profile-20261105`. Shared sessions were not terminated.
