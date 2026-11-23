# Remove automatic tmux layout — 2026-10-17

User asked to remove `tmux-ensure-layout` entirely. Existing sessions and windows were left in place.

## Changes

- Removed the `after-new-session` hook from the shared tmux config and cleared it live on Qubit, Tensor and Nexus.
- Removed calls from `tmux-auto-start`, `tmux-bootstrap-session`, Nexus `nexus-login-tmux`, and `agent-kit-sync`.
- Deleted the managed helper from the canonical kit, the Tensor/Nexus kit mirrors, and all three `~/.local/bin` directories. Future `install-host.py` runs remove a stale installed copy.
- New sessions still bootstrap a single zsh window. The login and relay attach paths remain; no window numbers or applications were changed.
- Updated the current README and shared AGENTS instructions. Historical audit and change entries remain as dated records.

## Checks

- Live `tmux show-hooks -g after-new-session` had no command on all three hosts. No active startup/bootstrap script referenced `tmux-ensure-layout`, and no installed executable remained.
- Session inventories remained Qubit `main` (6 windows), Tensor `1` (5) plus `main` (1), Nexus `nexus` (7). `base-index` is 1 on each host. Shell and Python syntax checks passed for edited scripts.
- No new tmux session was created to exercise the future bootstrap path; this is a configuration and live hook check.

## Backups and rollback

- Qubit: `/Users/iragonforce/.local/state/tmux-remove-layout-20261017-145126/qubit.before.tgz`, plus `install-host.py.before`, `AGENTS.md.before`, and `context-AGENTS.md.before` in that directory.
- Tensor: `/home/iragonforce/.local/state/tmux-remove-layout-20261017-145126/tensor.before.tgz`, plus `AGENTS.md.before` and `context-AGENTS.md.before`.
- Nexus: `/home/iragonforce/.local/state/tmux-remove-layout-20261017-145126/nexus.before.tgz`, plus `AGENTS.md.before` and `context-AGENTS.md.before`.
- To restore automatic layout, extract the matching archive under that host's home directory, restore Qubit's saved installer and AGENTS files, reinstall the saved `tmux-ensure-layout` executable where needed, and `tmux source-file ~/.tmux.conf` on each host. This will affect future sessions; it does not require restarting the current server.
