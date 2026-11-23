# SSH alias and clipboard, 2026-10-18

## Changes

- On Qubit, Tensor and Nexus, `ssh qubit` now resolves to Qubit's Tailscale address (the same route as `qubit-ts`). Removed the obsolete `qubit-lan` SSH alias. Existing host-key aliases and strict checking were preserved. Nexus's `qubit-bootstrap` entry was kept and redirected to Tailscale.
- Qubit and Tensor Ghostty now copy any mouse selection to the system clipboard. Cmd+C copies it, Cmd+V pastes through Ghostty, and Cmd+X copies then sends a cut key to a visual Neovim selection. Ghostty's old private CSI sequence caused `7101~` in a plain shell; it was replaced with Shift-F1/Shift-F2 and absorbed in new Zsh shells.
- Tmux mouse capture is off on all three hosts, making normal drag selection work without Shift. Shift-F1/Shift-F2 use the existing tmux copy path when tmux copy mode is active; no clipboard watcher was added.
- Neovim mouse capture is off on all three hosts. In visual mode, Shift-F1 copies and Shift-F2 cuts to the attached client clipboard using OSC 52 inside tmux. Cmd+V uses Ghostty's native terminal paste. Qubit and Tensor running Neovim processes received the new module live; Nexus's running Neovim RPC socket did not respond, so its saved config takes effect on a new editor instance.
- Tensor Hyprland maps Super+C/V/X to Ghostty's native Super shortcuts for terminal windows and to Ctrl+C/V/X for other active applications. Its old Super+V float toggle moved to Super+Alt+V. The running Hyprland and Ghostty instances reloaded without closing windows.

## Operational checks

- `ssh -G qubit` showed the Tailscale address and strict checking on each host; batch SSH to `qubit` succeeded from each host.
- Ghostty 1.3.1 configuration validation passed on Qubit and Tensor. The effective config showed the new keybindings and copy-on-select setting.
- Tmux reported `mouse off` on Qubit, Tensor and Nexus after source-file. Shift-F1/Shift-F2 bindings loaded after correcting an initial unsupported F13/F14 spelling.
- Tensor Hyprland reported Super+C/V/X bindings, Super+Alt+V, and no config errors. Lua syntax and Zsh syntax checks passed. Qubit/Tensor Neovim RPC readback showed `mouse` empty and the Shift-F1 visual mapping.
- Physical Cmd key behavior, clipboard contents, and desktop application cut behavior still need user observation. This operational check does not claim those interactions were exercised.

## Rollback

- Qubit prechange files: the task's `work/clipboard-backup/` directory under `/Users/iragonforce/Documents/Codex/2026-10-18/can-you-fix-tmux-x20/`. It includes separate SSH, both Ghostty configs, Zsh, Neovim and tmux clipboard backups.
- Tensor prechange files: `~/.local/state/clipboard-20261018/` on Tensor, including SSH, Ghostty, Zsh, Neovim and Hyprland backups.
- Nexus prechange files: `~/.local/state/clipboard-20261018/` on Nexus, including SSH, Zsh, Neovim and peers SSH config backups.
- Restore only the relevant saved files, preserving subsequent edits; reload Ghostty/Hyprland and source tmux config if restoring key handling. Existing Neovim sessions may retain live mappings until reopened.
